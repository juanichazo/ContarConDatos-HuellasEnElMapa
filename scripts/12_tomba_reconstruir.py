"""12_tomba_reconstruir.py — Reconstruye las áreas protegidas de Tomba (2025) en el paquete.
Fuente: Tomba, A. (2025). Georeferenced database of Argentina's protected areas system. Mendeley Data, V1.
doi:10.17632/wggsh3dszp.1 · CC BY 4.0 · https://data.mendeley.com/datasets/wggsh3dszp/1
Transferencia: el .dbf llegó íntegro (sha256 = el publicado por Mendeley). El .shp (12 MB) se transfirió
cuantizado a 1e-4° (~11 m) y sin vértices consecutivos repetidos (745.057 -> 699.354 vértices), codificado en varint;
alcanza de sobra para áreas por ecorregión/hexágono H3 de ~1.770 km².
Texto: el .dbf original trae los acentos perdidos ('ï¿½' = carácter de reemplazo guardado como Latin-1). Se restauran
con un diccionario de palabras; ⚠ la restauración es conocimiento propio (ortografía del castellano y topónimos), no
está en la fuente. Se conserva la columna original `nombre_original`.
Uso: python3 -I 12_tomba_reconstruir.py <carpeta raw/tomba2025> <salida.gpkg>
"""
import sys, re, pyogrio, geopandas as gpd, shapely
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import make_valid

src, out = sys.argv[1], sys.argv[2]
d = open(f'{src}/geom_q1e4.varint', 'rb').read(); p = 0
def vu():
    global p
    n = 0; s = 1
    while True:
        b = d[p]; p += 1; n += (b & 127) * s; s *= 128
        if b < 128: return n
zz = lambda n: n // 2 if n % 2 == 0 else -(n + 1) // 2
N = vu(); px = py = 0; geoms = []
for _ in range(N):
    rings = []
    for _ in range(vu()):
        pts = []
        for _ in range(vu()):
            px += zz(vu()); py += zz(vu()); pts.append((px / 1e4, py / 1e4))
        rings.append(pts)
    polys = []
    for ring in rings:  # shapefile: anillo exterior horario, huecos antihorarios
        if len(ring) < 4: continue
        if not shapely.LinearRing(ring).is_ccw or not polys: polys.append([ring, []])
        else: polys[-1][1].append(ring)
    geoms.append(make_valid(MultiPolygon([Polygon(a, b) for a, b in polys])) if polys else None)
assert p == len(d) and N == 575

FIX = {'Abdï¿½n':'Abdón','Acï¿½nquija':'Aconquija','Administraciï¿½n':'Administración','Agrï¿½nomo':'Agrónomo',
'Aguaraï¿½':'Aguaraí','Anï¿½nima':'Anónima','Apipï¿½':'Apipé','Aponapï¿½':'Aponapó','Arqueolï¿½gico':'Arqueológico',
'Asociaciï¿½n':'Asociación','Autï¿½noma':'Autónoma','Ayuï¿½':'Ayuí','Bahï¿½a':'Bahía','Baritï¿½':'Baritú',
'Basaldï¿½a':'Basaldúa','Baï¿½ado':'Bañado','Baï¿½ados':'Bañados','Belï¿½n':'Belén','Biogeogrï¿½fico':'Biogeográfico',
'Biolï¿½gica':'Biológica','Biolï¿½gico':'Biológico','Biï¿½sfera':'Biósfera','Botï¿½nico':'Botánico','Cabureï¿½':'Cabureí',
'Cachapï¿½':'Cachapé','Calchaquï¿½es':'Calchaquíes','Caldï¿½n':'Caldén','Cambyretï¿½':'Cambyretá','Carcaraï¿½ï¿½':'Carcarañá',
'Cayastï¿½':'Cayastá','CaÃ±uelas':'Cañuelas','Caï¿½':'Caá','Caï¿½ada':'Cañada','Caï¿½adï¿½n':'Cañadón','Chachï¿½n':'Chachín',
'Chajarï¿½':'Chajarí','Chancanï¿½':'Chancaní','Chasicï¿½':'Chasicó','Chaviyï¿½':'Chaviyú','Chaï¿½ar':'Chañar','Chaï¿½y':'Chañy',
'Chiflï¿½n':'Chiflón','Cientï¿½fico':'Científico','Ciï¿½naga':'Ciénaga','Constituciï¿½n':'Constitución','Corazï¿½n':'Corazón',
'Cordï¿½n':'Cordón','Cormorï¿½n':'Cormorán','Cretï¿½cico':'Cretácico','Cuarï¿½':'Cuaré','Curupï¿½':'Curupí','Curï¿½':'Curú',
'Cuyï¿½n':'Cuyín','Cuï¿½ï¿½':'Cuñá','Cï¿½rdoba':'Córdoba','Ecologï¿½a':'Ecología','Ecolï¿½gica':'Ecológica',
'Ecolï¿½gico':'Ecológico','Educaciï¿½n':'Educación','Engaï¿½o':'Engaño','Epuyï¿½n':'Epuyén','Errï¿½tico':'Errático',
'Especï¿½fico':'Específico','Estratï¿½gica':'Estratégica','Faunï¿½stica':'Faunística','Faunï¿½stico':'Faunístico',
'Florï¿½stica':'Florística','Formaciï¿½n':'Formación','Fundaciï¿½n':'Fundación','Fï¿½':'Fe','Fï¿½rtil':'Fértil',
'Geï¿½logica':'Geológica','Guaranï¿½':'Guaraní','Guatrachï¿½':'Guatraché','Guazï¿½':'Guazú','Gï¿½irï¿½':'Güirá',
'Hemisfï¿½rica':'Hemisférica','Histï¿½rico':'Histórico','Hï¿½bitat':'Hábitat','Hï¿½drica':'Hídrica','Ibatï¿½n':'Ibatín',
'Iberï¿½':'Iberá','Iguazï¿½':'Iguazú','Indï¿½gena':'Indígena','Investigaciï¿½n':'Investigación','Inï¿½s':'Inés',
'Isorï¿½':'Isoró','Ituzaingï¿½':'Ituzaingó','Josï¿½':'José','Juliï¿½n':'Julián','Kï¿½ppers':'Küppers','Lanï¿½n':'Lanín',
'Leï¿½n':'León','Lihuï¿½':'Lihué','Lujï¿½n':'Luján','Marquï¿½s':'Marqués','Martï¿½n':'Martín','Martï¿½nez':'Martínez',
'Marï¿½a':'María','Mbororï¿½':'Mbororé','Mburucuyï¿½':'Mburucuyá','Melincuï¿½':'Melincué','Moconï¿½':'Moconá',
'MontaÃ±a':'Montaña','Montaï¿½a':'Montaña','Mï¿½ltiple':'Múltiple','Mï¿½ltiples':'Múltiples','Neuquï¿½n':'Neuquén',
'Nicolï¿½s':'Nicolás','Nï¿½cleo':'Núcleo','Oberï¿½':'Oberá','Ombï¿½es':'Ombúes','Paisajï¿½stica':'Paisajística',
'Panorï¿½mica':'Panorámica','Paranï¿½':'Paraná','Paraï¿½so':'Paraíso','Penï¿½nsula':'Península','Perï¿½n':'Perón',
'PeÃ±a':'Peña','Peï¿½a':'Peña','Pigï¿½en':'Pigüé','Pingï¿½ino':'Pingüino','Piï¿½alito':'Piñalito',
'Planificaciï¿½n':'Planificación','Portuguï¿½s':'Portugués','Protecciï¿½n':'Protección','Puneï¿½as':'Puneñas',
'Pï¿½blica':'Pública','Pï¿½blico':'Público','Ramï¿½rez':'Ramírez','Raï¿½l':'Raúl','Rincï¿½n':'Rincón','Rolï¿½n':'Rolón',
'Rï¿½o':'Río','Rï¿½os':'Ríos','Samborombï¿½n':'Samborombón','Secretarï¿½a':'Secretaría','Somuncurï¿½':'Somuncurá',
'Tampï¿½n':'Tampón','Tecnologï¿½a':'Tecnología','Temaikï¿½n':'Temaikèn','Transiciï¿½n':'Transición','Tromï¿½n':'Tromen',
'Tucumï¿½n':'Tucumán','Turï¿½stica':'Turística','Turï¿½stico':'Turístico','Tï¿½ristica':'Turística','Valdï¿½s':'Valdés',
'Vaquerï¿½as':'Vaquerías','Velï¿½zquez':'Velázquez','Verï¿½nica':'Verónica','Volcï¿½n':'Volcán','Vï¿½a':'Vía',
'Yabotï¿½':'Yabotí','Yaguaroundï¿½':'Yaguaroundí','Yararï¿½':'Yararí','Zanjï¿½n':'Zanjón','ï¿½rea':'Área','ï¿½ï¿½rea':'Área',
'ï¿½rido':'Árido','ï¿½irihuau':'Ñirihuau','ï¿½orquinco':'Ñorquinco','ï¿½acunï¿½n':'Ñacuñán','ï¿½ochilei':'Ñochilei'}
FRASE = {'Caï¿½-Porï¿½':'Caá-Porá','Urugua-ï¿½':'Urugua-í','Tuyï¿½':'Tuyú','Teyï¿½':'Teyú','Uruzï¿½':'Uruzú',
'Pirï¿½':'Pirí','Guarambocï¿½':'Guarambocá','ï¿½uï¿½orcos':'Ñuñorcos','ï¿½unorcos':'Ñuñorcos','Pehuen-Cï¿½':'Pehuen-Có',
'Osununï¿½':'Osununú','Ralicï¿½':'Ralicó','Jaaukanigï¿½s':'Jaaukanigás','Tangarï¿½':'Tangará','Minï¿½':'Miní',
'Yvytï¿½':'Yvytú','Tenondï¿½':'Tenondé'}
def fix(s):
    if not isinstance(s, str): return s
    for a, b in FRASE.items(): s = s.replace(a, b)
    s = re.sub(r'[\wï¿½Ã±]*(?:ï¿½|Ã)[\wï¿½Ã±]*', lambda m: FIX.get(m.group(0), m.group(0)), s)
    return s.replace('ï¿½', '·').replace('Ã±', 'ñ')   # lo no resuelto queda marcado con '·'

df = pyogrio.read_dataframe(f'{src}/All protected areas.dbf', read_geometry=False)
g = gpd.GeoDataFrame({
    'ap_id': df['ID'].astype(int), 'nombre': df['Nombre'].map(fix), 'nombre_original': df['Nombre'],
    'operador': df['Operador'].map(fix), 'administracion': df['Administra'], 'clase_uicn': df['Clase IUCN'],
    'estricta_I_IV': df['Clase IUCN'].isin(['1a', '1b', '2', '3', '4']), 'proteccion': df['Proteccion'].map(fix),
    'anio_creacion': df['Creacion'], 'area_km2_fuente': df['Area km2']}, geometry=geoms, crs='EPSG:4326')
g['area_km2_calc'] = g.to_crs('ESRI:102033').area / 1e6   # Albers Sudamérica
g.to_file(out, layer='areas_protegidas', driver='GPKG')
print(len(g), 'AP;', 'nombres con · sin resolver:', g.nombre.str.contains('·').sum())
print('área fuente vs calculada (km²):', round(g.area_km2_fuente.sum()), round(g.area_km2_calc.sum()))
print(g[g.nombre.str.contains('·', na=False)].nombre.tolist())
