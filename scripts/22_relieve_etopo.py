"""22_relieve_etopo.py — Relieve sombreado del mapa base, a partir de ETOPO 2022 (NOAA NCEI).
Fuente: NOAA National Centers for Environmental Information (2022). ETOPO 2022 15 Arc-Second Global Relief Model.
  https://doi.org/10.25921/fd45-gt74 · dominio público. Se usa la versión de 30" (superficie), recortada por WCS.
Entradas:
  raw/etopo2022/etopo2022_30s_surface_80W44W_58S16S.tif   recorte 80°O–44°O, 58°S–16°S (se descarga si falta, 87 MB)
Salida:
  site/data/relieve_etopo.jpg   en Web Mercator (EPSG:3857), para la fuente «image» de MapLibre con las esquinas de BBOX
Pasos:
  1. sombreado multidireccional (azimuts 270/315/360°, sol a 45°) con exageración vertical, en grados corregidos por cos(lat)
  2. mar = celdas ≤ 0 m conectadas con el borde (las depresiones continentales, como el Bajo del Gualicho, quedan como tierra)
  3. reproyección de filas a Mercator (las columnas ya son lineales en longitud)
  4. color «herbario»: tierra entre sepia oscuro y papel según la luz; mar y bordes del recorte = color papel del sitio
Uso (desde la carpeta del paquete):  python -I scripts/22_relieve_etopo.py
"""
import math, os, urllib.request
import numpy as np
from PIL import Image
from scipy import ndimage

BBOX = (-80.0, -58.0, -44.0, -16.0)  # oeste, sur, este, norte
TIF = 'raw/etopo2022/etopo2022_30s_surface_80W44W_58S16S.tif'
URL = ('https://www.ngdc.noaa.gov/thredds/wcs/global/ETOPO2022/30s/30s_surface_elev_netcdf/ETOPO_2022_v1_30s_N90W180_surface.nc'
       '?service=WCS&version=1.0.0&request=GetCoverage&coverage=z&format=GeoTIFF_Float&bbox=%g,%g,%g,%g' % BBOX)
SALIDA = 'site/data/relieve_etopo.jpg'
ANCHO = 2400                      # px de la imagen final (≈ 0,015° por px)
EXAG = 6.0                        # exageración vertical del sombreado
PAPEL = np.array([0xF3, 0xED, 0xE0], float)
SOMBRA = np.array([0x6B, 0x5A, 0x48], float)
LUZ = np.array([0xFB, 0xF8, 0xF1], float)
FUNDIDO = 0.07                    # fracción de cada borde que se funde con el papel

if not os.path.exists(TIF):
    os.makedirs(os.path.dirname(TIF), exist_ok=True)
    print('descargando ETOPO 2022…'); urllib.request.urlretrieve(URL, TIF)
Image.MAX_IMAGE_PIXELS = None
src = Image.open(TIF)
z = np.array(src, dtype=np.float32)            # filas de norte a sur
res = src.tag_v2[33550][0]; lon0, lat0 = src.tag_v2[33922][3], src.tag_v2[33922][4]
h, w = z.shape
lats = lat0 - (np.arange(h) + 0.5) * res
print('ETOPO', z.shape, 'z', z.min(), z.max())

# 1. sombreado
m_por_grado = 111320.0
dy = res * m_por_grado
dx = res * m_por_grado * np.cos(np.radians(lats))[:, None]
gy, gx = np.gradient(z * EXAG)
gx = gx / dx; gy = -gy / dy                     # gy positivo hacia el norte
pend = np.arctan(np.hypot(gx, gy))
asp = np.arctan2(-gx, gy)                       # dirección de la ladera, 0 = norte
alt = math.radians(45)
luz = np.zeros_like(z)
for az, peso in ((270, 0.25), (315, 0.5), (360, 0.25)):
    a = math.radians(az)
    luz += peso * (np.sin(alt) * np.cos(pend) + np.cos(alt) * np.sin(pend) * np.cos(a - asp))
luz = np.clip(luz, 0, 1)

# 2. máscara de mar: ≤ 0 m y conectado con el borde
grupos, _ = ndimage.label(z <= 0)
borde_ids = np.unique(np.concatenate([grupos[0], grupos[-1], grupos[:, 0], grupos[:, -1]]))
mar = np.isin(grupos, borde_ids[borde_ids > 0])

# 3. reproyección a Mercator
merc = lambda la: np.log(np.tan(np.pi / 4 + np.radians(la) / 2))
yN, yS = merc(BBOX[3]), merc(BBOX[1])
alto = int(round(ANCHO * (yN - yS) / math.radians(BBOX[2] - BBOX[0])))
yy = yN - (np.arange(alto) + 0.5) / alto * (yN - yS)
lat_out = np.degrees(2 * np.arctan(np.exp(yy)) - np.pi / 2)
fila = np.clip(np.round((lat0 - lat_out) / res - 0.5).astype(int), 0, h - 1)
col = np.clip(np.round(((np.arange(ANCHO) + 0.5) / ANCHO * (BBOX[2] - BBOX[0])) / res - 0.5).astype(int), 0, w - 1)
L = luz[fila][:, col]; M = mar[fila][:, col]; Z = z[fila][:, col]

# 4. color
t = np.clip((L - 0.4) / 0.55, 0, 1) ** 1.1                                  # 0 sombra, 1 luz
alto_t = np.clip(Z / 4500, 0, 1)[..., None]                                  # leve oscurecimiento con la altura
rgb = SOMBRA + (LUZ - SOMBRA) * t[..., None]
rgb = rgb * (1 - 0.12 * alto_t) + SOMBRA * 0.12 * alto_t
rgb = 0.72 * rgb + 0.28 * (PAPEL * 0.84)                                     # tierra un poco más oscura que el papel
fx = np.minimum(np.arange(ANCHO), ANCHO - 1 - np.arange(ANCHO)) / (FUNDIDO * ANCHO)
fy = np.minimum(np.arange(alto), alto - 1 - np.arange(alto)) / (FUNDIDO * alto)
borde = np.clip(np.minimum(fy[:, None], fx[None, :]), 0, 1)
borde = (borde * borde * (3 - 2 * borde))[..., None]                         # suavizado
k = np.where(M[..., None], 0.0, borde)
rgb = PAPEL + (rgb - PAPEL) * k
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(SALIDA, quality=84, optimize=True, progressive=True)
print(SALIDA, ANCHO, 'x', alto, '·', os.path.getsize(SALIDA) // 1024, 'KB · esquinas MapLibre:',
      [[BBOX[0], BBOX[3]], [BBOX[2], BBOX[3]], [BBOX[2], BBOX[1]], [BBOX[0], BBOX[1]]])
