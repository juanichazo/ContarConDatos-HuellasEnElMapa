"""MapBiomas Argentina Col. 3 — 'Estadísticas por Ecorregión' (XLSX) -> CSV tidy de vegetación natural por ecorregión y año.

Insumo (no accesible desde el entorno donde se armó el paquete; bajarlo a mano):
  https://argentina.mapbiomas.org/wp-content/uploads/sites/8/2026/09/Estadisticas_por_Ecorregion.xlsx
  Licencia CC BY 4.0. Citar: "Proyecto MapBiomas Argentina – Colección 3 de la Serie Anual de Mapas de
  Cobertura y Uso del Suelo de Argentina, accedido el <fecha> a través del link: <url>".
  Las ecorregiones de MapBiomas son las de Burkart et al. 1999 (NO las RESOLVE de ecorregiones.geojson):
  para cruzar, usar los nombres de Burkart o armar una tabla de equivalencias a mano.

El script es defensivo porque no se pudo inspeccionar el archivo: primero corré con --inspeccionar para ver
hojas y columnas, y después ajustá --hoja, --col_region, --col_clase.

Uso:
  python -I scripts/07_mapbiomas_ecorregion.py --xlsx Estadisticas_por_Ecorregion.xlsx --inspeccionar
  python -I scripts/07_mapbiomas_ecorregion.py --xlsx Estadisticas_por_Ecorregion.xlsx --hoja COBERTURA \
      --col_region ecorregion --col_clase class_level_0 --clases_naturales "Natural" --out mapbiomas_vegetacion_natural_ecorregion.csv

Salida tidy: ecorregion, clase, anio, area_ha  (filtrado 2012-2025; se suma por clase si se pide nivel agregado)
"""
import argparse
import re
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--xlsx", required=True)
ap.add_argument("--inspeccionar", action="store_true")
ap.add_argument("--hoja")
ap.add_argument("--col_region")
ap.add_argument("--col_clase")
ap.add_argument("--clases_naturales", default="", help="valores de --col_clase a conservar, separados por ';' (vacío = todas)")
ap.add_argument("--out", default="mapbiomas_vegetacion_natural_ecorregion.csv")
a = ap.parse_args()

xl = pd.ExcelFile(a.xlsx)
if a.inspeccionar:
    for h in xl.sheet_names:
        d = xl.parse(h, nrows=5)
        print(f"== {h}: {list(d.columns)}\n{d.head(3).to_string()}\n")
    raise SystemExit
d = xl.parse(a.hoja)
anios = [c for c in d.columns if re.fullmatch(r"\d{4}", str(c).strip())]
if anios:  # formato ancho: una columna por año
    long = d.melt(id_vars=[a.col_region, a.col_clase], value_vars=anios, var_name="anio", value_name="area_ha")
else:      # formato largo: buscar columnas año/área
    ca = [c for c in d.columns if str(c).lower() in ("year", "anio", "año")][0]
    cv = [c for c in d.columns if "area" in str(c).lower()][0]
    long = d.rename(columns={ca: "anio", cv: "area_ha"})[[a.col_region, a.col_clase, "anio", "area_ha"]]
long["anio"] = long.anio.astype(int)
long = long[(long.anio >= 2012) & (long.anio <= 2025)]
if a.clases_naturales:
    long = long[long[a.col_clase].astype(str).isin(a.clases_naturales.split(";"))]
out = (long.groupby([a.col_region, a.col_clase, "anio"], as_index=False).area_ha.sum()
           .rename(columns={a.col_region: "ecorregion", a.col_clase: "clase"}))
out.to_csv(a.out, index=False)
print(out.head(20).to_string())
