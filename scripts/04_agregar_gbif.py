"""Agrega ocurrencias GBIF de especies amenazadas por ecorregión y por hexágono H3.

Entrada mínima (CSV, coma o tab): species, decimalLatitude, decimalLongitude, year,
coordinateUncertaintyInMeters, gbifID  (columnas extra se ignoran; acepta también un
"Simple CSV" de descarga oficial GBIF, que trae esas mismas columnas separadas por tab).

Uso:
  python -I scripts/04_agregar_gbif.py --puntos gbif/ocurrencias_gbif.csv \
      --especies especies_amenazadas.csv --ecorregiones ecorregiones_full.gpkg --out .

Salidas en --out:
  especie_x_ecorregion.csv      especie × ecorregión: presencia, n_registros, años, año min/max
  resumen_ecorregiones.csv      por ecorregión: n especies amenazadas total y por categoría, n registros
  ecorregiones_riqueza.geojson  ecorregiones.geojson + columnas del resumen (para el mapa web)
  h3_res4.geojson, h3_res5.geojson  hexágonos con n_registros, n_especies, n_CR/EN/VU
  especies_sin_match.csv        nombres de la lista que no aparecen en los puntos (revisar sinonimias)
"""
import argparse
import os
import sys

import pandas as pd
import geopandas as gpd

ap = argparse.ArgumentParser()
ap.add_argument("--puntos", required=True)
ap.add_argument("--especies", required=True)
ap.add_argument("--ecorregiones", required=True, help="ecorregiones_full.gpkg (o .geojson)")
ap.add_argument("--ecorregiones_web", default=None, help="ecorregiones.geojson simplificado (para riqueza)")
ap.add_argument("--out", default=".")
ap.add_argument("--anio_min", type=int, default=2012)
ap.add_argument("--anio_max", type=int, default=2025)
ap.add_argument("--incert_max_m", type=float, default=10000,
                help="descarta registros con coordinateUncertaintyInMeters mayor (NA se conserva)")
ap.add_argument("--sin_h3", action="store_true")
a = ap.parse_args()

sep = "\t" if open(a.puntos, encoding="utf-8").readline().count("\t") > 2 else ","
usecols = ["species", "decimalLatitude", "decimalLongitude", "year", "coordinateUncertaintyInMeters", "gbifID"]
pts = pd.read_csv(a.puntos, sep=sep, usecols=lambda c: c in usecols + ["scientificName"], dtype={"gbifID": str},
                  low_memory=False, on_bad_lines="skip", quoting=3 if sep == "\t" else 0)
n0 = len(pts)
pts = pts.dropna(subset=["decimalLatitude", "decimalLongitude", "species"])
pts["year"] = pd.to_numeric(pts["year"], errors="coerce")
pts = pts[(pts.year >= a.anio_min) & (pts.year <= a.anio_max)]
unc = pd.to_numeric(pts["coordinateUncertaintyInMeters"], errors="coerce")
pts = pts[unc.isna() | (unc <= a.incert_max_m)]
pts = pts.drop_duplicates(subset="gbifID")
print(f"puntos leídos {n0}, tras filtros {len(pts)}", file=sys.stderr)

esp = pd.read_csv(a.especies, dtype=str)
# GBIF devuelve en `species` el nombre aceptado del backbone; puede diferir del nombre de la Res. 316/2021.
# Agregar acá equivalencias verificadas con https://api.gbif.org/v1/species/match (columna `nombre_gbif`).
if "nombre_gbif" in esp.columns:
    esp["clave"] = esp["nombre_gbif"].fillna(esp["nombre_cientifico"])
else:
    esp["clave"] = esp["nombre_cientifico"]
pts = pts.merge(esp[["clave", "especie_id", "nombre_cientifico", "nombre_comun", "categoria_nacional"]],
                left_on="species", right_on="clave", how="inner")
faltan = esp[~esp.clave.isin(pts.species.unique())]
faltan[["especie_id", "nombre_cientifico", "categoria_nacional", "ambito"]].to_csv(
    os.path.join(a.out, "especies_sin_match.csv"), index=False)

g = gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy(pts.decimalLongitude, pts.decimalLatitude), crs=4326)
eco = gpd.read_file(a.ecorregiones).to_crs(4326)
j = gpd.sjoin(g, eco[["eco_id", "nombre", "nombre_es", "geometry"]], how="inner", predicate="within")
print(f"puntos dentro de ecorregiones: {len(j)}", file=sys.stderr)

ex = (j.groupby(["eco_id", "nombre", "nombre_es", "especie_id", "nombre_cientifico", "nombre_comun", "categoria_nacional"])
        .agg(n_registros=("gbifID", "size"), anio_min=("year", "min"), anio_max=("year", "max"),
             n_anios=("year", "nunique"),
             anios=("year", lambda s: ";".join(str(int(x)) for x in sorted(s.unique()))))
        .reset_index())
ex["presencia"] = 1
ex.sort_values(["eco_id", "categoria_nacional", "nombre_cientifico"]).to_csv(
    os.path.join(a.out, "especie_x_ecorregion.csv"), index=False)

res = ex.groupby("eco_id").agg(n_especies=("especie_id", "nunique"), n_registros=("n_registros", "sum")).reset_index()
cat = ex.pivot_table(index="eco_id", columns="categoria_nacional", values="especie_id", aggfunc="nunique", fill_value=0)
cat = cat.reindex(columns=["CR", "EN", "VU"], fill_value=0).add_prefix("n_").reset_index()
res = eco[["eco_id", "nombre", "nombre_es", "area_km2"]].merge(res, on="eco_id", how="left").merge(cat, on="eco_id", how="left")
for c in ["n_especies", "n_registros", "n_CR", "n_EN", "n_VU"]:
    res[c] = res[c].fillna(0).astype(int)
res["registros_por_1000km2"] = (res.n_registros / res.area_km2 * 1000).round(2)
res.to_csv(os.path.join(a.out, "resumen_ecorregiones.csv"), index=False)

web = gpd.read_file(a.ecorregiones_web) if a.ecorregiones_web else eco
web = web[["eco_id", "geometry"]].merge(res, on="eco_id")
web.to_file(os.path.join(a.out, "ecorregiones_riqueza.geojson"), driver="GeoJSON", COORDINATE_PRECISION=4)

if not a.sin_h3:
    import h3
    from shapely.geometry import Polygon
    for res_h in (4, 5):
        g["h3"] = [h3.latlng_to_cell(la, lo, res_h) for la, lo in zip(g.decimalLatitude, g.decimalLongitude)]
        hx = g.groupby("h3").agg(n_registros=("gbifID", "size"), n_especies=("especie_id", "nunique")).reset_index()
        c2 = g.pivot_table(index="h3", columns="categoria_nacional", values="especie_id", aggfunc="nunique", fill_value=0)
        c2 = c2.reindex(columns=["CR", "EN", "VU"], fill_value=0).add_prefix("n_").reset_index()
        hx = hx.merge(c2, on="h3")
        geoms = [Polygon([(lo, la) for la, lo in h3.cell_to_boundary(c)]) for c in hx.h3]
        gpd.GeoDataFrame(hx, geometry=geoms, crs=4326).to_file(
            os.path.join(a.out, f"h3_res{res_h}.geojson"), driver="GeoJSON", COORDINATE_PRECISION=4)
print(res.to_string(), file=sys.stderr)
