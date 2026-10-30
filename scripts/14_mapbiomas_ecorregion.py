"""14_mapbiomas_ecorregion.py — Cobertura y uso por ecorregión (Burkart) 1985–2025, MapBiomas Argentina Colección 3.
Fuente: MapBiomas Argentina (2026). Estadísticas por ecorregión, Colección 3 (CC BY 4.0).
https://argentina.mapbiomas.org/wp-content/uploads/sites/8/2026/09/Estadisticas_por_Ecorregion.xlsx
(página: https://argentina.mapbiomas.org/descargas/estadisticas/ ; sha256 c5b5fca7…b703f9)
Hojas '<Ecorregión> Hist': superficie (ha) por clase y año. Clases agrupadas según la propia jerarquía de la hoja 'Cob'
(1. Bosques · 2. Vegetación natural herbácea y arbustiva · 3. Uso agropecuario · 4. Sin vegetación · 5. Agua · 6. No observado).
Salidas (presiones/): mapbiomas_eco_clase_anio.csv (largo) · mapbiomas_eco_resumen.csv (natural/agro por año + cambios 2012→2025)
"""
import openpyxl, pandas as pd
src = 'raw/mapbiomas_col3/Estadisticas_por_Ecorregion.xlsx'
NOMBRE = {'Altos Andes': 'Altos Andes', 'Bosques Patag': 'Bosques Patagónicos', 'Campos Malezales': 'Campos y Malezales',
          'Chaco Húmedo': 'Chaco Húmedo', 'Chaco Seco': 'Chaco Seco', 'Delta Paraná': 'Delta e Islas del Paraná',
          'Espinal': 'Espinal', 'Estepa Patag': 'Estepa Patagónica', 'Esteros Iberá': 'Esteros del Iberá',
          'Monte Llanuras': 'Monte de Llanuras y Mesetas', 'Monte Sierras': 'Monte de Sierras y Bolsones', 'Pampa': 'Pampa',
          'Puna': 'Puna', 'Selva Paranaense': 'Selva Paranaense', 'Yungas': 'Yungas', 'Islas Atl Sur': 'Islas del Atlántico Sur'}
GRUPO = {'Bosques cerrados': 'bosque', 'Bosques abiertos': 'bosque', 'Bosques inundables': 'bosque',
         'Arbustales cerrados': 'veg_natural_no_bosque', 'Arbustales abiertos': 'veg_natural_no_bosque',
         'Mosaicos de arbustos y herbáceas': 'veg_natural_no_bosque', 'Herbáceas': 'veg_natural_no_bosque',
         'Herbáceas inundables': 'veg_natural_no_bosque', 'Turberas': 'veg_natural_no_bosque',
         'Cultivos temporarios': 'agropecuario', 'Cultivos perennes': 'agropecuario', 'Pasturas': 'agropecuario',
         'Silvicultura': 'agropecuario', 'Mosaico de usos': 'agropecuario', 'Áreas urbanas': 'urbano',
         'Otras áreas no vegetadas': 'sin_vegetacion', 'Ríos, lagunas, lagos y océano': 'agua',
         'Hielo y nieve permanente': 'agua', 'No observado': 'no_observado'}
wb = openpyxl.load_workbook(src, read_only=True)
filas = []
for ws in wb.worksheets:
    if not ws.title.endswith(' Hist'): continue
    eco = ws.title[:-5]; rows = list(ws.iter_rows(values_only=True)); hdr = rows[0]
    for r in rows[1:]:
        if not r[0]: continue
        for c, a in zip(hdr, r):
            if isinstance(c, int) and a is not None:
                filas.append(dict(ecorregion_burkart=NOMBRE[eco], clase=r[0], grupo=GRUPO[r[0]], anio=c, ha=float(a)))
L = pd.DataFrame(filas); L.to_csv('presiones/mapbiomas_eco_clase_anio.csv', index=False)
W = L.pivot_table(index=['ecorregion_burkart', 'anio'], columns='grupo', values='ha', aggfunc='sum', fill_value=0).reset_index()
W['natural'] = W.bosque + W.veg_natural_no_bosque
W.to_csv('presiones/mapbiomas_eco_resumen.csv', index=False)
a, b = W[W.anio == 2012].set_index('ecorregion_burkart'), W[W.anio == 2025].set_index('ecorregion_burkart')
c = pd.DataFrame({'natural_2012_ha': a.natural, 'natural_2025_ha': b.natural, 'bosque_2012_ha': a.bosque, 'bosque_2025_ha': b.bosque,
                  'agro_2012_ha': a.agropecuario, 'agro_2025_ha': b.agropecuario})
c['cambio_natural_ha'] = c.natural_2025_ha - c.natural_2012_ha
c['cambio_natural_pct'] = 100 * c.cambio_natural_ha / c.natural_2012_ha
c['cambio_bosque_ha'] = c.bosque_2025_ha - c.bosque_2012_ha
c['cambio_agro_ha'] = c.agro_2025_ha - c.agro_2012_ha
c.round(1).sort_values('cambio_natural_ha').to_csv('presiones/mapbiomas_cambio_2012_2025.csv')
pd.set_option('display.width', 250); print(c.round(0).sort_values('cambio_natural_ha')[['natural_2012_ha','cambio_natural_ha','cambio_natural_pct','cambio_bosque_ha','cambio_agro_ha']])
