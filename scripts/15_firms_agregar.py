"""15_firms_agregar.py — Focos de calor FIRMS (NASA) 2012–2025 por año, ecorregión RESOLVE y hexágono H3 res 4.
Fuente: NASA FIRMS, Country Yearly Summary (Standard Processing), archivos <instrumento>_<año>_Argentina.csv
  índice: https://firms.modaps.eosdis.nasa.gov/data/country/yearly_summary_files.txt
  ej.:    https://firms.modaps.eosdis.nasa.gov/data/country/viirs-snpp/2020/viirs-snpp_2020_Argentina.csv
  VIIRS S-NPP 375 m (VNP14IMGTDL/SP, desde 2012) y MODIS Collection 6.1 1 km (MCD14). Uso libre; cita y descargo en
  https://www.earthdata.nasa.gov/data/tools/firms . Atributos: AttributesReadme.txt de la misma carpeta.
Filtros (aplicados en el navegador al bajar, sin guardar los puntos): type = 0 ("presumed vegetation fire");
  VIIRS confidence ≠ 'l' (baja); MODIS confidence ≥ 30. Cada punto se asignó a su celda H3 res 5 (h3-js 4.1.0).
Entrada: raw/firms/firms_h3res5_2012_2025.json  {hx:{'<inst>_<año>':['h3[1:8],n,frp_sum,n_jul_oct',…]}, st:{…}}
Salidas (presiones/): fuego_ecorregion_anio.csv · fuego_hex4_anio.csv · fuego_resumen_nacional.csv
Ecorregión: por el centroide de la celda res 5 (~252 km²); error de borde menor a una celda.
AVISO: un foco = una detección de anomalía térmica de un pasaje satelital, NO un incendio ni una superficie quemada.
"""
import json, h3, pandas as pd, geopandas as gpd
from shapely.geometry import Point
d = json.load(open('raw/firms/firms_h3res5_2012_2025.json'))
filas = []
for k, rows in d['hx'].items():
    inst, anio = k.rsplit('_', 1)
    for r in rows:
        c, n, frp, njo = r.split(',')
        filas.append((inst, int(anio), '8' + c + 'fffffff', int(n), int(frp), int(njo)))
F = pd.DataFrame(filas, columns=['instrumento', 'anio', 'h3_r5', 'focos', 'frp_mw', 'focos_jul_oct'])
celdas = F.h3_r5.unique()
eco = gpd.read_file('ecorregiones.geojson')[['eco_id', 'geometry']]
pts = gpd.GeoDataFrame({'h3_r5': celdas}, geometry=[Point(h3.cell_to_latlng(c)[::-1]) for c in celdas], crs='EPSG:4326')
pe = gpd.sjoin(pts, eco, predicate='within', how='left').drop_duplicates('h3_r5').set_index('h3_r5').eco_id
F['eco_id'] = F.h3_r5.map(pe); F['h3'] = F.h3_r5.map(lambda c: h3.cell_to_parent(c, 4))
agg = dict(focos=('focos', 'sum'), frp_mw=('frp_mw', 'sum'), focos_jul_oct=('focos_jul_oct', 'sum'))
F.groupby(['instrumento', 'eco_id', 'anio'], dropna=False).agg(**agg).reset_index().to_csv('presiones/fuego_ecorregion_anio.csv', index=False)
F.groupby(['instrumento', 'h3', 'anio']).agg(**agg).reset_index().to_csv('presiones/fuego_hex4_anio.csv', index=False)
S = [dict(instrumento=k.rsplit('_', 1)[0], anio=int(k.rsplit('_', 1)[1]), filas_csv=v['rows'], focos_filtrados=v['kept'],
          **{f'mes_{i+1:02d}': m for i, m in enumerate(v['mes'])}) for k, v in d['st'].items()]
pd.DataFrame(S).sort_values(['instrumento', 'anio']).to_csv('presiones/fuego_resumen_nacional.csv', index=False)
print('sin ecorregión (centroide fuera):', F[F.eco_id.isna()].focos.sum(), 'de', F.focos.sum())
v = F[F.instrumento == 'viirs-snpp'].groupby(['eco_id']).focos.sum().sort_values(ascending=False); print(v.head(8))
