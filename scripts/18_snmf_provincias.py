"""18_snmf_provincias.py — Superficie afectada por incendios reportados, por provincia y año 2012–2025 (fuente oficial).
Fuentes (Subsecretaría de Ambiente, dataset «Incendios forestales» de datos.gob.ar; datos del Servicio Nacional de Manejo
del Fuego), bajadas el 29/10/2026 desde https://ciam.ambiente.gob.ar/dt_csv.php?dt_id=… :
  dt 510  superficie total incendiada y de bosque nativo, por jurisdicción, 1993–2023
  dt 416  superficie afectada por incendios reportados, por jurisdicción, 2017–2026 (2026 parcial)
Regla: 2012–2016 de dt 510; 2017–2025 de dt 416 (serie más nueva, con 2024 y 2025).
AVISO: en los años en que se superponen (2017–2023) las dos tablas no siempre coinciden (p. ej. Chubut 2022: 93 ha en dt 510
y 80.294 ha en dt 416). Se guardan ambas columnas para que quede a la vista. 's/d' y '-' = sin dato.
Salida: presiones/snmf_provincia_anio.csv
"""
import pandas as pd
a = pd.read_csv('raw/snmf_ciam/ciam_dt510_superficie_total_y_bosque_nativo_incendiada_jurisdiccion.csv', sep=';')
b = pd.read_csv('raw/snmf_ciam/ciam_dt416_superficie_incendios_reportados_jurisdiccion.csv', sep=';')
num = lambda x: pd.to_numeric(str(x).replace(',', '.'), errors='coerce')
a = a.rename(columns={'jurisdicción': 'prov', 'año': 'anio'})
a['prov'] = a.prov.replace({'CABA': 'Ciudad Autónoma de Buenos Aires', 'Ciudad Autónoma de Buenos Aires': 'Ciudad Autónoma de Buenos Aires'})
a['ha_dt510'] = a.superficie_total_incendiada.map(num); a['ha_bn_dt510'] = a.superficie_afectada_por_incendios_bosque_nativo.map(num)
b = b[b['jurisdicción'] != 'Total'].melt(id_vars='jurisdicción', var_name='c', value_name='v')
b['anio'] = b.c.str[-4:].astype(int); b['ha_dt416'] = b.v.map(num); b = b.rename(columns={'jurisdicción': 'prov'})
b['prov'] = b.prov.replace({'CABA': 'Ciudad Autónoma de Buenos Aires'})
m = pd.merge(a[['prov', 'anio', 'ha_dt510', 'ha_bn_dt510']], b[['prov', 'anio', 'ha_dt416']], on=['prov', 'anio'], how='outer')
m = m[(m.anio >= 2012) & (m.anio <= 2025)]
m['ha'] = m.ha_dt416.where(m.anio >= 2017, m.ha_dt510)
m['fuente_ha'] = m.anio.map(lambda y: 'dt416' if y >= 2017 else 'dt510')
m['prov'] = m.prov.replace({'CABA': 'Ciudad Autónoma de Buenos Aires'})
m.sort_values(['prov', 'anio']).to_csv('presiones/snmf_provincia_anio.csv', index=False)
p = m.pivot_table(index='prov', columns='anio', values='ha', aggfunc='first')
print(p.sum(axis=1).sort_values(ascending=False).round().head(12)); print(p.loc[['Chubut', 'Neuquén', 'Río Negro']].to_string())
d = m[(m.anio.between(2017, 2023)) & m.ha_dt510.notna() & m.ha_dt416.notna()]
d = d[(d.ha_dt510 - d.ha_dt416).abs() > 0.5 * d[['ha_dt510', 'ha_dt416']].max(axis=1)]
print('años-provincia con >50 % de diferencia entre tablas:', len(d))
