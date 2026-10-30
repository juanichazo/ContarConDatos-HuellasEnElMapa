"""Cuenta detecciones de fuego VIIRS (FIRMS) por ecorregión y año, 2012-2025.

Cómo conseguir el insumo (no accesible desde el entorno donde se armó el paquete):
  1. https://firms.modaps.eosdis.nasa.gov/download/  -> "Create New Request"
     Country: Argentina | Source: VIIRS S-NPP 375 m (SV-C2, archivo estándar) — opcional NOAA-20 desde 2018
     Fechas: 2012-01-20 a 2025-12-31 | Formato: CSV. El link llega por email.
     (Alternativa sin login: https://firms.modaps.eosdis.nasa.gov/country/ trae CSVs anuales por país: viirs-snpp_<AÑO>_Argentina.csv)
  2. Columnas esperadas: latitude, longitude, acq_date, confidence (VIIRS: l/n/h), type (0=vegetación presunta,
     1=volcán, 2=fuente estática terrestre, 3=offshore) — se conservan type 0 y confidence n/h.

Uso:
  python -I scripts/06_firms_por_ecorregion.py --firms viirs1.csv [viirs2.csv ...] \
      --ecorregiones ecorregiones_full.gpkg --out fuegos_viirs_por_ecorregion_anio.csv [--areas_protegidas areas_protegidas.geojson]

Salida tidy: eco_id, nombre, anio, n_detecciones, detecciones_por_1000km2 [, n_dentro_ap]
Nota: son DETECCIONES de anomalías térmicas (píxeles de 375 m), no superficie quemada.
"""
import argparse
import pandas as pd
import geopandas as gpd

ap = argparse.ArgumentParser()
ap.add_argument("--firms", nargs="+", required=True)
ap.add_argument("--ecorregiones", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--areas_protegidas", default=None)
ap.add_argument("--conf", default="n,h", help="confianzas VIIRS a conservar")
a = ap.parse_args()

df = pd.concat([pd.read_csv(f, usecols=lambda c: c in {"latitude", "longitude", "acq_date", "confidence", "type", "satellite"})
                for f in a.firms], ignore_index=True)
df["anio"] = pd.to_datetime(df.acq_date).dt.year
df = df[(df.anio >= 2012) & (df.anio <= 2025)]
if "confidence" in df:
    df = df[df.confidence.astype(str).str.lower().str[0].isin(a.conf.split(","))]
if "type" in df:
    df = df[df["type"].fillna(0).astype(int) == 0]
g = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs=4326)
eco = gpd.read_file(a.ecorregiones).to_crs(4326)
j = gpd.sjoin(g, eco[["eco_id", "nombre", "area_km2", "geometry"]], predicate="within")
if a.areas_protegidas:
    ap_ = gpd.read_file(a.areas_protegidas).to_crs(4326)[["geometry"]]
    inside = gpd.sjoin(j.drop(columns="index_right"), ap_, predicate="within").index.unique()
    j["dentro_ap"] = j.index.isin(inside)
agg = {"n_detecciones": ("anio", "size")}
if "dentro_ap" in j:
    agg["n_dentro_ap"] = ("dentro_ap", "sum")
out = j.groupby(["eco_id", "nombre", "area_km2", "anio"]).agg(**agg).reset_index()
# completar años sin detecciones con 0
full = pd.MultiIndex.from_product([eco.eco_id, range(2012, 2026)], names=["eco_id", "anio"]).to_frame(index=False)
full = full.merge(eco[["eco_id", "nombre", "area_km2"]], on="eco_id")
out = full.merge(out, on=["eco_id", "nombre", "area_km2", "anio"], how="left")
for c in [c for c in ("n_detecciones", "n_dentro_ap") if c in out]:
    out[c] = out[c].fillna(0).astype(int)
out["detecciones_por_1000km2"] = (out.n_detecciones / out.area_km2 * 1000).round(3)
out.to_csv(a.out, index=False)
print(out.groupby("anio").n_detecciones.sum())
