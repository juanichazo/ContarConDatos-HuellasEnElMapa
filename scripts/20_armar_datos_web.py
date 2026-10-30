"""20_armar_datos_web.py — Arma los dos JSON que lee el explorador: data/datos.json y data/puntos.json.
Entradas (todas dentro del paquete):
  raw/gbif_descarga/0012791-261023074918325.csv   descarga oficial GBIF (DOI 10.15468/dl.t87f4d), TSV, 259.468 filas
  especies_amenazadas.csv                          205 especies (id, nombre GBIF, categoría nacional y UICN)
  ecorregiones_full.gpkg                           RESOLVE 2017 recortado a Argentina (para asignar ecorregión)
  ecorregiones.geojson, provincias.geojson         contornos para el mapa (se simplifican acá)
  web_data/hex_h4.geojson                          grilla H3 res 4 con registros (salida del script 04)
Reglas (verificadas: dan exactamente 162.717 registros únicos):
  1. coordinateUncertaintyInMeters vacío o ≤ 30.000 m   → 257.861 filas
  2. drop_duplicates(species, decimalLatitude, decimalLongitude, eventDate)  → 162.717 (quita copias entre datasets y repeticiones)
  3. celda = H3 res 4 de (lat, lon); ecorregión = polígono RESOLVE que contiene el punto (join espacial; puede quedar vacía en el mar)
  4. puntos.json: coordenadas redondeadas a 0,01° (≈1 km), agrupadas por especie, lon, lat, año → [lon, lat, año, n]
  5. contornos: Douglas–Peucker 0,01° con topología, redondeo a 4 decimales; solo se conservan las propiedades que usa la página.
Uso (desde la carpeta del paquete):  python -I scripts/20_armar_datos_web.py [--chequear]
  --chequear compara el resultado con web_data/*.json y data/*.json existentes y avisa si difieren.
"""
import json, sys, os
import numpy as np, pandas as pd, geopandas as gpd, h3
from shapely.geometry import shape, mapping

RAW = 'raw/gbif_descarga/0012791-261023074918325.csv'
ANIOS = list(range(2012, 2026))
esp = pd.read_csv('especies_amenazadas.csv')
nom2id = dict(zip(esp.nombre_gbif, esp.especie_id))
r = pd.read_csv(RAW, sep='\t', usecols=['species', 'decimalLatitude', 'decimalLongitude', 'coordinateUncertaintyInMeters', 'eventDate', 'year'], low_memory=False)
r = r[r.coordinateUncertaintyInMeters.isna() | (r.coordinateUncertaintyInMeters <= 30000)]
r = r.drop_duplicates(['species', 'decimalLatitude', 'decimalLongitude', 'eventDate']).copy()
r['especie_id'] = r.species.map(nom2id)
assert r.especie_id.notna().all(), r[r.especie_id.isna()].species.unique()
assert len(r) == 162717, len(r)
r['h4'] = [h3.latlng_to_cell(a, b, 4) for a, b in zip(r.decimalLatitude, r.decimalLongitude)]
eco = gpd.read_file('ecorregiones_full.gpkg').to_crs(4326)
pts = gpd.GeoDataFrame(r, geometry=gpd.points_from_xy(r.decimalLongitude, r.decimalLatitude), crs=4326)
pts = gpd.sjoin(pts, eco[['eco_id', 'geometry']], how='left', predicate='within').drop(columns='index_right')
pts = pts[~pts.index.duplicated()]

# --- occ: especie → celda → registros por año
occ = {}
for (sp, cell, y), n in pts.groupby(['especie_id', 'h4', 'year']).size().items():
    occ.setdefault(sp, {}).setdefault(cell, [0] * 14)[int(y) - 2012] += int(n)
# --- especies
base = esp.set_index('especie_id')
especies = []
for sid, row in base.iterrows():
    g = pts[pts.especie_id == sid]
    yv = [int((g.year == y).sum()) for y in ANIOS]
    especies.append(dict(id=sid, cie=row.nombre_cientifico, com=row.nombre_comun, gru=row.grupo, nac=row.categoria_nacional, nact=row.categoria_nacional_texto,
                         uicn=None if pd.isna(row.categoria_uicn_global) else row.categoria_uicn_global, amb=None if pd.isna(row.ambito) else row.ambito, n=int(len(g)), y=yv,
                         eco=sorted(g.eco_id.dropna().unique().tolist()), nh=int(g.h4.nunique())))
# --- ecoAnio: ecorregión × año
cat = dict(zip(esp.especie_id, esp.categoria_nacional)); pts['cat'] = pts.especie_id.map(cat)
eco_anio = []
for (e, y), g in pts.dropna(subset=['eco_id']).groupby(['eco_id', 'year']):
    c = g.drop_duplicates('especie_id').cat.value_counts()
    eco_anio.append(dict(eco=e, y=int(y), n=int(len(g)), sp=int(g.especie_id.nunique()), CR=int(c.get('CR', 0)), EN=int(c.get('EN', 0)), VU=int(c.get('VU', 0))))
eco_anio.sort(key=lambda d: (d['eco'], d['y']))

def rnd(c, n=4): return [rnd(x, n) for x in c] if isinstance(c, (list, tuple)) else round(c, n)
def simp(path, keep):
    g = json.load(open(path)); out = []
    for f in g['features']:
        s = shape(f['geometry']).simplify(0.01, preserve_topology=True)
        out.append({'type': 'Feature', 'properties': {k: f['properties'][k] for k in keep}, 'geometry': {'type': s.geom_type, 'coordinates': rnd(mapping(s)['coordinates'])}})
    return {'type': 'FeatureCollection', 'features': out}
ecor = simp('ecorregiones.geojson', ['eco_id', 'nombre', 'nombre_es', 'area_km2'])
prov = simp('provincias.geojson', ['nombre'])
hexg = json.load(open('web_data/hex_h4.geojson'))
datos = {'meta': {'anios': ANIOS, 'gbif': 'GBIF.org (29/10/2026) GBIF Occurrence Download https://doi.org/10.15468/dl.t87f4d'},
         'especies': especies, 'occ': occ, 'ecoAnio': eco_anio, 'ecor': ecor, 'prov': prov, 'hex': hexg}
pts['lon2'] = pts.decimalLongitude.round(2); pts['lat2'] = pts.decimalLatitude.round(2)
puntos = {}
for (sp, lo, la, y), n in pts.groupby(['especie_id', 'lon2', 'lat2', 'year']).size().items():
    puntos.setdefault(sp, []).append([round(float(lo), 2), round(float(la), 2), int(y), int(n)])
os.makedirs('site/data', exist_ok=True)
json.dump(datos, open('site/data/datos.json', 'w'), separators=(',', ':'), ensure_ascii=False)
json.dump(puntos, open('site/data/puntos.json', 'w'), separators=(',', ':'), ensure_ascii=False)
print('datos.json', len(datos['especies']), 'especies;', 'puntos.json', sum(len(v) for v in puntos.values()), 'puntos')
if '--chequear' in sys.argv:
    web = {k: json.load(open(f'web_data/{k}.json')) for k in ['especies', 'ocurrencias_h4', 'ecorregion_anio']}
    print('especies igual:', web['especies'] == especies, '| occ igual:', web['ocurrencias_h4'] == occ, '| ecoAnio igual:', web['ecorregion_anio'] == eco_anio)
