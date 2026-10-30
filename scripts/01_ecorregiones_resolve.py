"""Ecorregiones RESOLVE 2017 (Dinerstein et al. 2017) recortadas a Argentina.

Fuente: objeto sf `ecoregions` del paquete R IanOndo/RGeodata (data/ecoregions.rda),
que redistribuye Ecoregions2017 (ecoregions2017.appspot.com, CC BY 4.0).
Se parsea el .rda con la librería `rdata` (sin R), se reconstruyen las geometrías
MULTIPOLYGON, se recorta al contorno de Argentina continental (provincias INDEC),
se calcula el área en una proyección Albers equivalente centrada en Argentina y se simplifica.
`nombre_es` es una traducción orientativa hecha a mano del nombre RESOLVE (NO es la ecorregión de Burkart 1999).

Uso: python -I scripts/01_ecorregiones_resolve.py <ecoregions.rda> <provincias.geojson> <out_dir>
"""
import sys
import json
import numpy as np
import rdata
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import make_valid

rda, prov_path, out_dir = sys.argv[1:4]

AEA = "+proj=aea +lat_1=-28 +lat_2=-48 +lat_0=-38 +lon_0=-64 +datum=WGS84 +units=m +no_defs"


def attrs(o):
    d = {}
    a = o.attributes
    while a is not None and getattr(a, "info", None) is not None and a.info.type.name == "LIST":
        t = a.tag
        while t is not None and t.info.type.name == "REF":
            t = t.referenced_object
        tag = t.value.value.decode() if t is not None else None
        d[tag] = a.value[0]
        a = a.value[1]
    return d


def strvec(o):
    return [None if x.value is None else x.value.decode("utf-8", "replace") for x in o.value]


def mat(o):
    arr = np.asarray(o.value, dtype=float)
    dim = attrs(o).get("dim")
    nr, nc = [int(x) for x in dim.value]
    return arr.reshape((nc, nr)).T  # R es column-major


def geom(o):
    cls = strvec(attrs(o)["class"])
    if "MULTIPOLYGON" in cls:
        polys = []
        for poly in o.value:
            rings = [mat(r) for r in poly.value]
            polys.append(Polygon(rings[0], rings[1:]))
        return MultiPolygon(polys)
    if "POLYGON" in cls:
        rings = [mat(r) for r in o.value]
        return Polygon(rings[0], rings[1:])
    raise ValueError(cls)


parsed = rdata.parser.parse_file(rda)
top = parsed.object  # pairlist: tag 'ecoregions'
df = top.value[0]
names = strvec(attrs(df)["names"])
cols = dict(zip(names, df.value))
print("columnas:", names)
geomcol = [n for n in names if n in ("geometry", "geom", "SHAPE")][0]
geoms = [geom(g) for g in cols[geomcol].value]
data = {}
for n in names:
    if n == geomcol:
        continue
    o = cols[n]
    if o.info.type.name == "STR":
        data[n] = strvec(o)
    else:
        data[n] = list(np.asarray(o.value))
gdf = gpd.GeoDataFrame(data, geometry=geoms, crs="EPSG:4326")
print("ecorregiones globales:", len(gdf))

prov = gpd.read_file(prov_path).to_crs(4326)
arg = prov.union_all()
bbox = gdf.cx[-74:-53, -56:-21]
bbox = bbox[bbox.intersects(arg)].copy()
bbox["geometry"] = bbox.geometry.apply(make_valid)
clip = gpd.clip(bbox, arg)
clip = clip[~clip.geometry.is_empty]
clip = clip.dissolve(by="ECO_NAME", as_index=False, aggfunc="first")
clip["area_km2"] = (clip.to_crs(AEA).area / 1e6).round(1)
clip = clip[clip.area_km2 >= 1].copy()
clip = clip.sort_values("area_km2", ascending=False).reset_index(drop=True)
clip["eco_id"] = ["E%02d" % (i + 1) for i in range(len(clip))]
keep = ["eco_id", "ECO_NAME", "BIOME_NAME", "REALM", "area_km2", "geometry"]
keep = [k for k in keep if k in clip.columns]
ES = {"Patagonian steppe": "Estepa patagónica", "Dry Chaco": "Chaco seco", "Humid Pampas": "Pampa húmeda",
      "Low Monte": "Monte de llanuras", "Espinal": "Espinal", "Humid Chaco": "Chaco húmedo", "High Monte": "Monte de sierras",
      "Southern Andean steppe": "Estepa andina del sur", "Central Andean puna": "Puna", "Southern Andean Yungas": "Yungas",
      "Valdivian temperate forests": "Bosques templados valdivianos", "Paraná flooded savanna": "Delta e islas del Paraná",
      "Central Andean dry puna": "Puna seca", "Magellanic subpolar forests": "Bosques subpolares magallánicos",
      "Southern Cone Mesopotamian savanna": "Sabana mesopotámica (Esteros del Iberá)", "Alto Paraná Atlantic forests": "Selva paranaense (Bosque Atlántico)",
      "Araucaria moist forests": "Bosques de araucaria (Misiones)", "Rock and Ice": "Roca y hielo", "Uruguayan savanna": "Sabana uruguaya",
      "Chilean Matorral": "Matorral chileno"}
clip["nombre_es"] = clip["ECO_NAME"].map(ES)
keep.insert(2, "nombre_es")
clip = clip[keep].rename(columns={"ECO_NAME": "nombre", "BIOME_NAME": "bioma", "REALM": "reino"})

# versión de trabajo (alta resolución, para sjoin) y versión web simplificada
clip.to_file(f"{out_dir}/ecorregiones_full.gpkg", driver="GPKG")
web = clip.copy()
tol = 0.003
while True:
    web["geometry"] = clip.geometry.simplify(tol, preserve_topology=True).apply(make_valid)
    web.to_file(f"{out_dir}/ecorregiones.geojson", driver="GeoJSON", COORDINATE_PRECISION=4)
    import os
    size = os.path.getsize(f"{out_dir}/ecorregiones.geojson")
    print("tol", tol, "bytes", size)
    if size < 1_500_000:
        break
    tol *= 1.6
print(clip.drop(columns="geometry").to_string())
