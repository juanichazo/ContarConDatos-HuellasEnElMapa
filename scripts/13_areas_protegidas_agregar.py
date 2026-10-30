"""13_areas_protegidas_agregar.py — Áreas protegidas (Tomba 2025) por ecorregión RESOLVE, año y hexágono H3 res 4.
Entrada: presiones/areas_protegidas_tomba2025.gpkg (script 12), ecorregiones.geojson, argentina_contorno.geojson.
Salidas (presiones/):
  ap_ecorregion_anio.csv  eco_id × año 1934–2025: km² protegidos (unión, sin doble conteo), nominal y estricta (UICN I–IV)
  hex_h4_base.geojson     grilla H3 res 4 que toca el territorio continental+insular (incl. Malvinas, como el contorno INDEC)
  hex_h4_ap.csv           por hexágono: km² terrestres, km² protegidos 2025 (nominal/estricta), % y año de la primera AP
Método: solo superficie terrestre (AP recortadas al contorno INDEC; se excluye lo marino). Proyección equivalente Albers
Sudamérica (ESRI:102033). Tomba no trae AP creadas después de 2022: 2023–2025 repiten el stock de 2022.
"""
import geopandas as gpd, pandas as pd, h3, shapely
from shapely.geometry import Polygon
P = 'ESRI:102033'
ap = gpd.read_file('presiones/areas_protegidas_tomba2025.gpkg').to_crs(P)
tierra = gpd.read_file('argentina_contorno.geojson').to_crs(P).union_all()
eco = gpd.read_file('ecorregiones.geojson').to_crs(P)
ap['geometry'] = ap.geometry.buffer(0).intersection(tierra)
ap = ap[~ap.is_empty]
filas = []
for _, e in eco.iterrows():
    sub = ap[ap.intersects(e.geometry)].copy()
    sub['geometry'] = sub.geometry.intersection(e.geometry)
    for anio in range(1934, 2026):
        v = sub[sub.anio_creacion <= anio]
        nom = v.union_all().area / 1e6 if len(v) else 0
        es = v[v.estricta_I_IV]
        est = es.union_all().area / 1e6 if len(es) else 0
        filas.append(dict(eco_id=e.eco_id, anio=anio, km2_eco=e.geometry.intersection(tierra).area / 1e6,
                          km2_ap_nominal=round(nom, 1), km2_ap_estricta=round(est, 1), n_ap=len(v)))
t = pd.DataFrame(filas)
t['pct_nominal'] = (100 * t.km2_ap_nominal / t.km2_eco).round(2)
t['pct_estricta'] = (100 * t.km2_ap_estricta / t.km2_eco).round(2)
t.to_csv('presiones/ap_ecorregion_anio.csv', index=False)

# grilla H3 res 4 sobre el contorno
cont = gpd.read_file('argentina_contorno.geojson').union_all()
celdas = set()
for poly in getattr(cont, 'geoms', [cont]):
    celdas |= set(h3.geo_to_cells(poly.buffer(0.15), 4))   # margen para tomar celdas de borde
hx = gpd.GeoDataFrame({'h3': sorted(celdas)}, geometry=[Polygon([(lo, la) for la, lo in h3.cell_to_boundary(c)]) for c in sorted(celdas)], crs='EPSG:4326')
hxp = hx.to_crs(P)
hxp['km2_tierra'] = hxp.geometry.intersection(tierra).area / 1e6
hx = hx[hxp.km2_tierra > 1].copy(); hxp = hxp[hxp.km2_tierra > 1].copy()
u_nom = ap.union_all(); u_est = ap[ap.estricta_I_IV].union_all()
hxp['km2_ap_nominal'] = hxp.geometry.intersection(u_nom).area / 1e6
hxp['km2_ap_estricta'] = hxp.geometry.intersection(u_est).area / 1e6
j = gpd.sjoin(hxp[['h3', 'geometry']], ap[['anio_creacion', 'geometry']], predicate='intersects')
hxp['anio_primera_ap'] = hxp.h3.map(j.groupby('h3').anio_creacion.min())
hxp['pct_ap_nominal'] = (100 * hxp.km2_ap_nominal / hxp.km2_tierra).clip(upper=100).round(1)
hxp['pct_ap_estricta'] = (100 * hxp.km2_ap_estricta / hxp.km2_tierra).clip(upper=100).round(1)
hx[['h3', 'geometry']].to_file('presiones/hex_h4_base.geojson', driver='GeoJSON')
hxp.drop(columns='geometry').round(1).to_csv('presiones/hex_h4_ap.csv', index=False)
print(len(hx), 'hexágonos;', t[t.anio == 2025][['eco_id', 'km2_eco', 'pct_nominal', 'pct_estricta']].to_string())
print('total 2025 km² nominal (suma eco):', t[t.anio == 2025].km2_ap_nominal.sum().round(), '/ tierra', round(tierra.area / 1e6))
