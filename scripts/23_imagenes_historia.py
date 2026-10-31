"""23_imagenes_historia.py — Dibuja los mapas fijos de la historia visual (site/img/*.jpg) sobre el relieve ETOPO 2022.
Entradas (todas dentro del paquete):
  site/data/datos.json, site/data/puntos.json   salidas del script 20 (grilla H3 res 4, registros por celda y año, puntos ≈1 km)
  site/data/relieve_etopo.jpg                   salida del script 22 (Web Mercator, 80°O–44°O, 58°S–16°S)
  argentina_contorno.geojson                    contorno INDEC, para recortar las celdas a la tierra
Salidas:
  site/img/m1_riqueza.jpg      especies amenazadas registradas por celda, 2012–2024
  site/img/m2_esfuerzo.jpg     registros por celda, 2012–2024 (escala logarítmica)
  site/img/m3_p1..p3.jpg       especies por celda en 2012–2015, 2016–2019 y 2020–2024
  site/img/sp_<id>.jpg         puntos de registro (≈1 km) y celdas ocupadas de cuatro especies, 2012–2024
Reglas (dan las cifras que cita la historia: 2.015 celdas y máximo 34 en m1; 990/1.226/1.732 celdas en m3):
  se cuentan todas las especies y todas las celdas; el dibujo de las celdas se recorta al contorno terrestre.
Uso (desde la carpeta del paquete):  python -I scripts/23_imagenes_historia.py
"""
import json, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from PIL import Image

PAPEL, PAPEL2, TINTA, TINTA2, A = '#F3EDE0', '#FBF8F1', '#2B241D', '#6B5A48', '#9B3522'
LON = (-76.0, -52.5)            # el alto sale de la proporción de cada imagen
LAT_N = -21.0
RELIEVE = ('site/data/relieve_etopo.jpg', (-80.0, -58.0, -44.0, -16.0))
ESPECIES = ['MAM034', 'AVE071', 'AVE020', 'AVE104']

def mix(a, b, t):
    ha = [int(a[i:i + 2], 16) for i in (1, 3, 5)]; hb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join('%02x' % round(x + (y - x) * t) for x, y in zip(ha, hb))
ESCALA = [mix(PAPEL, TINTA, 0.22), mix(PAPEL, A, 0.45), mix(PAPEL, A, 0.8), mix(A, TINTA, 0.55)]   # 1–3, 4–9, 10–19, 20+
def color_riqueza(n): return ESCALA[0 if n < 4 else 1 if n < 10 else 2 if n < 20 else 3]

merc = lambda lat: math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))
def xy(c): return [(x, merc(y)) for x, y in c]
def anillos(geom):
    cs = geom['coordinates']
    return [r for p in (cs if geom['type'] == 'MultiPolygon' else [cs]) for r in p]

D = json.load(open('site/data/datos.json', encoding='utf-8'))
P = json.load(open('site/data/puntos.json', encoding='utf-8'))
contorno = json.load(open('argentina_contorno.geojson', encoding='utf-8'))['features'][0]['geometry']
hexs = {f['properties']['h']: xy(f['geometry']['coordinates'][0]) for f in D['hex']['features']}
prov = [xy(r) for f in D['prov']['features'] for r in anillos(f['geometry'])]
ecor = [xy(r) for f in D['ecor']['features'] for r in anillos(f['geometry'])]
tierra = [xy(r) for r in anillos(contorno)]
rel = np.asarray(Image.open(RELIEVE[0]))

def por_celda(y0, y1, ids=None):
    """especies y registros por celda en la ventana [y0, y1], y el conjunto de especies registradas"""
    sp, rec, todas = {}, {}, set()
    for e in D['especies']:
        if ids and e['id'] not in ids: continue
        for h, a in (D['occ'].get(e['id']) or {}).items():
            t = sum(a[y0 - 2012:y1 - 2012 + 1])
            if t > 0: sp[h] = sp.get(h, 0) + 1; rec[h] = rec.get(h, 0) + t; todas.add(e['id'])
    return sp, rec, todas

def lienzo(ancho, alto):
    fig = plt.figure(figsize=(ancho / 100, alto / 100), dpi=100, facecolor=PAPEL)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_facecolor(PAPEL)
    yN = merc(LAT_N); yS = yN - (LON[1] - LON[0]) * alto / ancho
    ax.set_xlim(*LON); ax.set_ylim(yS, yN)
    w, s, e, n = RELIEVE[1]
    ax.imshow(rel, extent=[w, e, merc(s), merc(n)], interpolation='bilinear', alpha=0.6, zorder=0)   # igual que el mapa interactivo
    camino = Path.make_compound_path(*[Path(r) for r in tierra])
    clip = PathPatch(camino, transform=ax.transData, facecolor='none', edgecolor='none'); ax.add_patch(clip)
    return fig, ax, clip, ancho / 1100

def celdas(ax, clip, colores, k, borde=True):
    hs = [h for h in colores if h in hexs]
    pc = PolyCollection([hexs[h] for h in hs], facecolors=[colores[h] for h in hs],
                        edgecolors=mix(PAPEL2, TINTA, 0.08) if borde else 'none', linewidths=0.35 * k, zorder=2)
    pc.set_clip_path(clip); ax.add_collection(pc)

def lineas(ax, k, ecorregiones=False):
    if ecorregiones:
        ax.add_collection(LineCollection(ecor, colors=TINTA2, linewidths=0.5 * k, linestyles=(0, (3, 2)), alpha=0.35, zorder=3))
    ax.add_collection(LineCollection(prov, colors=TINTA, linewidths=0.7 * k, alpha=0.4, zorder=3))
    ax.add_collection(LineCollection(tierra, colors=mix(TINTA, PAPEL, 0.35), linewidths=0.7 * k, alpha=0.7, zorder=3))

def guardar(fig, ruta):
    fig.canvas.draw()
    img = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3]); plt.close(fig)
    img.save(ruta, quality=88, optimize=True, progressive=True); print(ruta, img.size)

# m1 · riqueza 2012–2024
sp, rec, _ = por_celda(2012, 2024)
print('m1: celdas', len(sp), 'máximo', max(sp.values()))
fig, ax, clip, k = lienzo(1100, 2160)
celdas(ax, clip, {h: color_riqueza(n) for h, n in sp.items()}, k); lineas(ax, k, True); guardar(fig, 'site/img/m1_riqueza.jpg')

# m2 · esfuerzo: registros por celda, escala logarítmica en grises
lmax = math.log10(max(rec.values()))
claro, oscuro = mix(PAPEL, TINTA, 0.14), mix(PAPEL, TINTA, 0.85)
fig, ax, clip, k = lienzo(1100, 2160)
celdas(ax, clip, {h: mix(claro, oscuro, math.log10(n) / lmax) for h, n in rec.items()}, k); lineas(ax, k, True); guardar(fig, 'site/img/m2_esfuerzo.jpg')

# m3 · tres períodos
for i, (y0, y1) in enumerate([(2012, 2015), (2016, 2019), (2020, 2024)], 1):
    sp, rec, todas = por_celda(y0, y1)
    print('m3 %d–%d: celdas %d · especies %d · registros %d' % (y0, y1, len(sp), len(todas), sum(rec.values())))
    fig, ax, clip, k = lienzo(640, 1257)
    celdas(ax, clip, {h: color_riqueza(n) for h, n in sp.items()}, k); lineas(ax, k); guardar(fig, 'site/img/m3_p%d.jpg' % i)

# retratos de especies: celdas ocupadas en rosado y puntos ≈1 km con tamaño según registros
for sid in ESPECIES:
    sp, _, _ = por_celda(2012, 2024, {sid})
    pts = np.array([q for q in P.get(sid, []) if 2012 <= q[2] <= 2024], float)
    fig, ax, clip, k = lienzo(640, 1257)
    celdas(ax, clip, {h: mix(PAPEL, A, 0.32) for h in sp}, k, borde=False); lineas(ax, k)
    if len(pts):
        n = {}
        for lon, lat, _, c in pts: n[(lon, lat)] = n.get((lon, lat), 0) + c
        ll = np.array(list(n.keys())); cnt = np.array(list(n.values()))
        ax.scatter(ll[:, 0], [merc(y) for y in ll[:, 1]], s=18 + 26 * np.log10(cnt), c=A, edgecolors=PAPEL2, linewidths=0.7, zorder=4)
    print(sid, 'celdas', len(sp), 'puntos', len(pts))
    guardar(fig, 'site/img/sp_%s.jpg' % sid)
