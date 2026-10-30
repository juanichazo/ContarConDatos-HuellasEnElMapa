"""21_registros_dentro_ap.py — Marca qué registros GBIF caen dentro de un área protegida y lo agrega a presiones.json (clave occAP).
Entradas: web_data/presiones.json (salida del script 16), presiones/areas_protegidas_tomba2025.gpkg (575 AP, Tomba 2025),
          site/data/puntos.json (script 20: [lon, lat, año, n] con coordenadas a 0,01°).
Método: unión de todos los polígonos de AP (estado 2022, cualquier categoría) y prueba punto-en-polígono con shapely.contains_xy;
        cada punto «dentro» suma n registros a su celda H3 res 4 y año → occAP[especie][celda] = 14 conteos (2012–2025).
Límite: los puntos tienen ≈1 km de precisión, así que un registro pegado al borde puede caer de uno u otro lado.
Salida: site/data/presiones.json (= web_data/presiones.json + occAP). En 2026 dio 56.406 de 162.717 registros dentro (34,7 %), 125 especies.
Uso:  python -I scripts/21_registros_dentro_ap.py
"""
import json, geopandas as gpd, numpy as np, h3, shapely
from shapely import contains_xy
from shapely.ops import unary_union
ap = gpd.read_file('presiones/areas_protegidas_tomba2025.gpkg').to_crs(4326)
U = unary_union(ap.geometry.make_valid().values); shapely.prepare(U)
P = json.load(open('site/data/puntos.json'))
occ = {}; tot = ins = 0
for sp, rows in P.items():
    a = np.array(rows, float); dentro = contains_xy(U, a[:, 0], a[:, 1]); d = {}
    for (lon, lat, y, n), f in zip(rows, dentro):
        tot += n
        if f:
            ins += n; c = h3.latlng_to_cell(lat, lon, 4); d.setdefault(c, [0] * 14)[y - 2012] += n
    if d: occ[sp] = d
pr = json.load(open('web_data/presiones.json')); pr['occAP'] = occ
json.dump(pr, open('site/data/presiones.json', 'w'), separators=(',', ':'), ensure_ascii=False)
print(ins, 'de', tot, 'registros dentro de AP (%.1f %%)' % (ins / tot * 100), '·', len(occ), 'especies')
