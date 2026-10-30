"""Provincias (INDEC Codgeo vía geoAr/PoliticaArgentina) -> provincias.geojson simplificado + area_km2.
Uso: python -I scripts/03_provincias.py <provincias.geojson crudo> <out_dir>
"""
import sys, os
import geopandas as gpd
from shapely.validation import make_valid
src, out = sys.argv[1:3]
AEA = "+proj=aea +lat_1=-28 +lat_2=-48 +lat_0=-38 +lon_0=-64 +datum=WGS84 +units=m +no_defs"
g = gpd.read_file(src).to_crs(4326)
print(g.drop(columns="geometry").to_string())
g["geometry"] = g.geometry.apply(make_valid)
g = g.dissolve(by=["codprov_censo", "provincia"], as_index=False)
g["area_km2"] = (g.to_crs(AEA).area / 1e6).round(1)
g["geometry"] = g.geometry.simplify(0.005, preserve_topology=True).apply(make_valid)
g = g.rename(columns={"codprov_censo": "cod_prov", "provincia": "nombre"})[["cod_prov", "nombre", "area_km2", "geometry"]]
g.to_file(os.path.join(out, "provincias.geojson"), driver="GeoJSON", COORDINATE_PRECISION=4)
# contorno nacional (unión de provincias)
a = gpd.GeoDataFrame({"nombre": ["Argentina (sector continental e insular según INDEC)"]}, geometry=[g.union_all()], crs=4326)
a["area_km2"] = (a.to_crs(AEA).area / 1e6).round(1)
a.to_file(os.path.join(out, "argentina_contorno.geojson"), driver="GeoJSON", COORDINATE_PRECISION=4)
print(g.drop(columns="geometry").to_string()); print(os.path.getsize(os.path.join(out, "provincias.geojson")))
