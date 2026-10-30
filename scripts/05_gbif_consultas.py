"""Consultas a la API de GBIF para la lista de especies amenazadas (correr desde una red con acceso a api.gbif.org).

Pasos:
  1. species/match de cada nombre -> taxonKey, nombre aceptado (columna nombre_gbif) -> gbif/especies_gbif_match.csv
  2. conteo total por especie con limit=0 (mismos filtros)                       -> gbif/conteo_registros_por_especie.csv
  3. paginado de occurrence/search (limit=300, tope --cap por especie)          -> gbif/ocurrencias_gbif.csv
  4. escribe scripts/gbif_download_predicate_taxonkeys.json (predicado con TAXON_KEY, para la descarga oficial con DOI)

Filtros: country=AR, year=2012,2025, hasCoordinate=true, hasGeospatialIssue=false, occurrenceStatus=PRESENT.
OJO: la API de búsqueda NO es citable. Para el dataset final hay que pedir una descarga oficial
(POST https://api.gbif.org/v1/occurrence/download/request con usuario GBIF) usando el predicado JSON;
GBIF le asigna un DOI (10.15468/dl.xxxxx) que hay que citar.

Uso: python -I scripts/05_gbif_consultas.py --especies especies_amenazadas.csv --out gbif --cap 3000
"""
import argparse, csv, json, os, time
import requests

ap = argparse.ArgumentParser()
ap.add_argument("--especies", required=True)
ap.add_argument("--out", default="gbif")
ap.add_argument("--cap", type=int, default=3000)
ap.add_argument("--solo_terrestres", action="store_true")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
API = "https://api.gbif.org/v1"
FILT = dict(country="AR", year="2012,2025", hasCoordinate="true", hasGeospatialIssue="false", occurrenceStatus="PRESENT")
s = requests.Session()


def get(url, **p):
    for i in range(5):
        r = s.get(url, params=p, timeout=60)
        if r.status_code == 200:
            return r.json()
        time.sleep(2 ** i)
    r.raise_for_status()


esp = list(csv.DictReader(open(a.especies, encoding="utf-8")))
if a.solo_terrestres:
    esp = [e for e in esp if e.get("ambito") != "marino"]
match_rows, count_rows, keys = [], [], []
occ_f = open(os.path.join(a.out, "ocurrencias_gbif.csv"), "w", newline="", encoding="utf-8")
occ = csv.writer(occ_f)
occ.writerow(["especie_id", "nombre_lista", "species", "taxonKey", "decimalLatitude", "decimalLongitude", "year",
              "coordinateUncertaintyInMeters", "datasetKey", "gbifID", "license", "basisOfRecord", "institutionCode"])
for e in esp:
    n = e["nombre_cientifico"]
    m = get(f"{API}/species/match", name=n, kingdom="Animalia", **{"class": "Mammalia"} if e["grupo"] == "Mamíferos" else {})
    key = m.get("acceptedUsageKey") or m.get("usageKey")
    match_rows.append(dict(especie_id=e["especie_id"], nombre_cientifico=n, matchType=m.get("matchType"),
                           confidence=m.get("confidence"), status=m.get("status"), usageKey=m.get("usageKey"),
                           taxonKey=key, nombre_gbif=m.get("species") or m.get("canonicalName"), rank=m.get("rank")))
    if not key or m.get("rank") not in ("SPECIES", "SUBSPECIES"):
        count_rows.append(dict(especie_id=e["especie_id"], nombre_cientifico=n, taxonKey="", n_registros_2012_2025=""))
        continue
    keys.append(key)
    c = get(f"{API}/occurrence/search", taxonKey=key, limit=0, **FILT)["count"]
    count_rows.append(dict(especie_id=e["especie_id"], nombre_cientifico=n, taxonKey=key, n_registros_2012_2025=c))
    off = 0
    while off < min(c, a.cap):
        d = get(f"{API}/occurrence/search", taxonKey=key, limit=300, offset=off, **FILT)
        for r in d["results"]:
            occ.writerow([e["especie_id"], n, r.get("species"), key, r.get("decimalLatitude"), r.get("decimalLongitude"),
                          r.get("year"), r.get("coordinateUncertaintyInMeters"), r.get("datasetKey"), r.get("gbifID") or r.get("key"),
                          r.get("license"), r.get("basisOfRecord"), r.get("institutionCode")])
        off += 300
        if d.get("endOfRecords"):
            break
    print(n, key, c)
occ_f.close()
for name, rows in (("especies_gbif_match.csv", match_rows), ("conteo_registros_por_especie.csv", count_rows)):
    with open(os.path.join(a.out, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
pred = json.load(open(os.path.join(os.path.dirname(__file__), "gbif_download_predicate.json"), encoding="utf-8"))
for p in pred["predicate"]["predicates"]:
    if p.get("key") == "SCIENTIFIC_NAME":
        p.update(key="TAXON_KEY", values=[str(k) for k in sorted(set(keys))])
json.dump(pred, open(os.path.join(os.path.dirname(__file__), "gbif_download_predicate_taxonkeys.json"), "w"), indent=2)
