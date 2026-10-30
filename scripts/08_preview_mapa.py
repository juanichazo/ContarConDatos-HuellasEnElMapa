"""Mapa de control (PNG): ecorregiones RESOLVE + provincias; si existe resumen_ecorregiones.csv
(salida de 04_agregar_gbif.py) colorea por n de especies amenazadas registradas.
Uso: python -I scripts/08_preview_mapa.py <dir_paquete> <salida.png>
"""
import os, sys
import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d, out = sys.argv[1:3]
eco = gpd.read_file(os.path.join(d, "ecorregiones.geojson"))
prov = gpd.read_file(os.path.join(d, "provincias.geojson"))
res_p = os.path.join(d, "resumen_ecorregiones.csv")
fig, ax = plt.subplots(figsize=(9, 11), dpi=130)
if os.path.exists(res_p):
    r = pd.read_csv(res_p)
    eco = eco.merge(r[["eco_id", "n_especies"]], on="eco_id", how="left")
    eco.plot(column="n_especies", cmap="Reds", legend=True, ax=ax, edgecolor="white", linewidth=0.4,
             legend_kwds={"label": "Especies de mamíferos amenazados con registros GBIF 2012–2025", "shrink": 0.5})
    titulo = "Riqueza de mamíferos amenazados (Res. 316/2021) por ecorregión"
else:
    eco.plot(column="nombre_es", cmap="tab20", ax=ax, edgecolor="white", linewidth=0.4, legend=True,
             legend_kwds={"loc": "lower left", "fontsize": 6, "frameon": False, "bbox_to_anchor": (0.98, 0.02)})
    titulo = "Ecorregiones RESOLVE 2017 recortadas a Argentina\n(riqueza: pendiente de datos GBIF)"
prov.boundary.plot(ax=ax, color="#333", linewidth=0.3)
ax.set_xlim(-75, -52); ax.set_ylim(-56, -21)
ax.set_title(titulo, fontsize=10)
ax.set_axis_off()
fig.text(0.02, 0.01, "Fuentes: Res. MAyDS 316/2021; GBIF.org (API, consulta 29/10/2026, no citable: usar DOI de descarga); RESOLVE 2017 (CC BY 4.0); INDEC vía geoAr. Mapa de control.",
         fontsize=6)
fig.savefig(out, bbox_inches="tight")
print(out)
