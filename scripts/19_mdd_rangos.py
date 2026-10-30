"""19_mdd_rangos.py — Mapas de rango expertos (MDD v1.2) de mamíferos amenazados, recortados a Argentina.
Fuente: Marsh, C. J., Sica, Y. V., Burgin, C. J., et al. (2022). Expert range maps of global mammal distributions
harmonised to three taxonomic authorities. Journal of Biogeography 49(5): 979–992. doi:10.1111/jbi.14330.
Datos: Zenodo 6644198, «Geographic range maps for Mammal Diversity Database v1.2 taxonomy», CC BY 4.0.
https://zenodo.org/records/6644198 (GeoPackage por orden). Bajados el 30/10/2026 desde el navegador; en el navegador se
recortó cada polígono a la caja de Argentina (-74,5/-52,5 · -56,5/-21), se simplificó (Douglas–Peucker, 0,01°) y se
redondeó a 0,01°. Acá se recorta al contorno de Argentina (INDEC) y se asigna a la grilla H3 res 4 del paquete.
Órdenes procesados: Cingulata, Pilosa, Perissodactyla, Microbiotheria, Paucituberculata, Didelphimorphia, Primates.
Pendientes (archivos de 1,3 a 3,6 GB, no se pueden abrir en el navegador): Carnivora, Artiodactyla, Rodentia, Chiroptera.
Equivalencias de nombre: Metachirus nudicaudatus (lista nacional) ← Metachirus myosuros (MDD v1.2) ⚠ la población argentina
se asigna a M. myosuros en MDD; Philander quica igual en ambas.
Salidas: presiones/mdd_rangos.geojson · presiones/mdd_rango_hex4.csv
"""
import json, pandas as pd, geopandas as gpd
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.validation import make_valid
d = json.load(open('raw/mdd_rangos/mdd_rangos_argentina_bbox.json'))
esp = pd.read_csv('especies_amenazadas.csv'); idx = dict(zip(esp.nombre_cientifico, esp.especie_id))
EQ = {'Metachirus myosuros': 'Metachirus nudicaudatus'}
tierra = gpd.read_file('argentina_contorno.geojson').to_crs(4326).union_all()
filas = []
for nom, polys in d['res'].items():
    nac = EQ.get(nom, nom)
    if nac not in idx or not polys: continue
    ps = []
    for rings in polys:
        try:
            p = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4])
            ps.append(make_valid(p))
        except Exception: pass
    def planos(g):
        if g.geom_type == 'Polygon': return [g]
        if hasattr(g, 'geoms'): return [q for h in g.geoms for q in planos(h)]
        return []
    g = make_valid(MultiPolygon([q for p in ps for q in planos(p)])).intersection(tierra)
    if g.is_empty: continue
    # limpieza: cerrar astillas del recorte y quitar piezas y huecos diminutos (< ~25 km²)
    g = g.buffer(0.03).buffer(-0.03)
    partes = [Polygon(q.exterior, [h for h in q.interiors if Polygon(h).area > 0.002]) for q in planos(g) if q.area > 0.002]
    if not partes: continue
    g = MultiPolygon(partes)
    filas.append(dict(especie_id=idx[nac], nombre_nacional=nac, nombre_mdd=nom, cita=d['cit'][nom], geometry=g.simplify(0.01)))
G = gpd.GeoDataFrame(filas, crs=4326)
G['km2_arg'] = G.to_crs('ESRI:102033').area / 1e6
G.to_file('presiones/mdd_rangos.geojson', driver='GeoJSON')
hx = gpd.read_file('presiones/hex_h4_base.geojson').to_crs('ESRI:102033'); Gp = G.to_crs('ESRI:102033')
j = gpd.overlay(hx[['h3', 'geometry']], Gp[['especie_id', 'geometry']], how='intersection', keep_geom_type=True)
j['km2'] = j.area / 1e6
j = j[j.km2 > 200]   # la celda cuenta si el rango cubre al menos ~11 % de ella
j[['especie_id', 'h3', 'km2']].round(1).to_csv('presiones/mdd_rango_hex4.csv', index=False)
print(G[['especie_id', 'nombre_nacional', 'km2_arg']].round(0).to_string()); print(j.groupby('especie_id').h3.count().to_dict())
