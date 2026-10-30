"""16_presiones_web.py — Arma web_data/presiones.json para el explorador (capas de presión).
Entradas: presiones/*.csv y .geojson (scripts 12–15). Sin datos nuevos: solo reordena y redondea.
"""
import json, pandas as pd, geopandas as gpd
Y = list(range(2012, 2026))
hx = gpd.read_file('presiones/hex_h4_base.geojson')
ap = pd.read_csv('presiones/hex_h4_ap.csv').set_index('h3')
fu = pd.read_csv('presiones/fuego_hex4_anio.csv'); fu = fu[fu.instrumento == 'viirs-snpp']
fp = fu.pivot_table(index='h3', columns='anio', values='focos', fill_value=0).reindex(columns=Y, fill_value=0)
feats = []
for i, r in hx.iterrows():
    h = r.h3; a = ap.loc[h]
    f = [int(x) for x in fp.loc[h]] if h in fp.index else [0] * 14
    feats.append({'type': 'Feature', 'id': i, 'properties': {'h': h, 'km2': round(a.km2_tierra), 'ap': a.pct_ap_nominal, 'ape': a.pct_ap_estricta,
                  'apy': None if pd.isna(a.anio_primera_ap) else int(a.anio_primera_ap), 'f': f},
                  'geometry': {'type': 'Polygon', 'coordinates': [[[round(x, 4), round(y, 4)] for x, y in r.geometry.exterior.coords]]}})
ae = pd.read_csv('presiones/ap_ecorregion_anio.csv'); ae = ae[ae.anio.isin(Y)]
apEco = {e: {'nom': [round(v, 2) for v in g.sort_values('anio').pct_nominal], 'est': [round(v, 2) for v in g.sort_values('anio').pct_estricta],
             'km2': round(g.km2_eco.iloc[0])} for e, g in ae.groupby('eco_id')}
fe = pd.read_csv('presiones/fuego_ecorregion_anio.csv'); fe = fe[(fe.instrumento == 'viirs-snpp') & fe.eco_id.notna()]
fuegoEco = {e: [int(g.set_index('anio').focos.get(y, 0)) for y in Y] for e, g in fe.groupby('eco_id')}
mb = pd.read_csv('presiones/mapbiomas_eco_resumen.csv'); mb = mb[mb.anio.isin(Y)]
mbEco = {e: {'nat': [round(v / 1e3) for v in g.sort_values('anio').natural], 'bos': [round(v / 1e3) for v in g.sort_values('anio').bosque],
             'agro': [round(v / 1e3) for v in g.sort_values('anio').agropecuario]} for e, g in mb.groupby('ecorregion_burkart')}
# contornos de AP simplificados (para la lámina de líneas)
apg = gpd.read_file('presiones/areas_protegidas_tomba2025.gpkg')
from shapely.geometry import MultiPolygon
def solo_pol(g):
    ps = [p for p in getattr(g, 'geoms', [g]) if p.geom_type in ('Polygon', 'MultiPolygon')]
    ps = [q for p in ps for q in getattr(p, 'geoms', [p])]
    return MultiPolygon(ps) if ps else None
apg['geometry'] = apg.geometry.map(solo_pol).simplify(0.005, preserve_topology=True)
apg = apg[apg.geometry.notna() & ~apg.is_empty]
apFC = json.loads(apg[['nombre', 'anio_creacion', 'clase_uicn', 'estricta_I_IV', 'administracion', 'area_km2_fuente', 'geometry']]
                  .rename(columns={'anio_creacion': 'y', 'clase_uicn': 'c', 'estricta_I_IV': 'e', 'administracion': 'adm', 'area_km2_fuente': 'km2'}).to_json())
def rnd(c): return [rnd(x) for x in c] if isinstance(c[0], list) else [round(c[0], 3), round(c[1], 3)]
for f in apFC['features']: f['geometry']['coordinates'] = rnd(f['geometry']['coordinates']); f['properties']['km2'] = round(f['properties']['km2'], 1)
sn = pd.read_csv('presiones/snmf_provincia_anio.csv')
snmf = {pv: [None if pd.isna(v) else round(float(v)) for v in g.set_index('anio').reindex(Y).ha] for pv, g in sn.groupby('prov')}
import os
rangos, rangoCeldas = {'type': 'FeatureCollection', 'features': []}, {}
if os.path.exists('presiones/mdd_rangos.geojson'):   # script 19
    G = gpd.read_file('presiones/mdd_rangos.geojson'); H = pd.read_csv('presiones/mdd_rango_hex4.csv')
    for r in G.itertuples():
        gj = json.loads(gpd.GeoSeries([r.geometry]).to_json())['features'][0]['geometry']; gj['coordinates'] = rnd(gj['coordinates'])
        rangos['features'].append({'type': 'Feature', 'properties': {'id': r.especie_id, 'km2': round(r.km2_arg), 'mdd': r.nombre_mdd}, 'geometry': gj})
    rangoCeldas = {k: g.h3.tolist() for k, g in H.groupby('especie_id')}
out = {'meta': {'anios': Y, 'fuentes': {
        'ap': 'Tomba, A. (2025) Mendeley Data V1 doi:10.17632/wggsh3dszp.1 (CC BY 4.0)',
        'fuego': 'NASA FIRMS VIIRS S-NPP 375 m, Country Yearly Summary (SP), type=0, confianza n/h',
        'mb': 'MapBiomas Argentina Colección 3, Estadísticas por ecorregión (Burkart), CC BY 4.0',
        'rangos': 'Marsh et al. (2022) J. Biogeogr. 49:979, doi:10.1111/jbi.14330 · MDD v1.2 range maps, Zenodo 6644198, CC BY 4.0',
        'snmf': 'Servicio Nacional de Manejo del Fuego vía Subsecretaría de Ambiente (datos.gob.ar, ciam.ambiente.gob.ar dt 510 y 416)'}},
       'hexP': {'type': 'FeatureCollection', 'features': feats}, 'apEco': apEco, 'fuegoEco': fuegoEco, 'mbEco': mbEco, 'apFC': apFC, 'snmf': snmf, 'rangos': rangos, 'rangoCeldas': rangoCeldas}
s = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
open('web_data/presiones.json', 'w').write(s); print(len(s) / 1e6, 'MB', len(apFC['features']), 'AP')
