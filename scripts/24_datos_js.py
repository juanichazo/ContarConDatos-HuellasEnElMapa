"""24_datos_js.py — Envuelve los datos del explorador en archivos .js para que la página funcione también abierta con doble clic.
Abierta desde el disco (file://), el navegador bloquea fetch() de los .json y de la imagen del relieve; un <script> sí se puede cargar.
Entradas:  site/data/datos.json, presiones.json, puntos.json (scripts 20 y 21) y site/data/relieve_etopo.jpg (script 22)
Salidas:   site/data/datos.js, presiones.js, puntos.js, relieve.js — cada uno define window.HUELLAS.<nombre>
Correrlo cada vez que cambie alguna de las entradas.  Uso (desde la carpeta del paquete):  python -I scripts/24_datos_js.py
"""
import base64, json, os

D = 'site/data'
def escribir(nombre, valor_js):
    ruta = os.path.join(D, nombre + '.js')
    with open(ruta, 'w', encoding='utf-8', newline='\n') as f:
        f.write('(window.HUELLAS = window.HUELLAS || {}).%s = %s;\n' % (nombre, valor_js))
    print(ruta, os.path.getsize(ruta) // 1024, 'KB')

for nombre in ('datos', 'presiones', 'puntos'):
    with open(os.path.join(D, nombre + '.json'), encoding='utf-8') as f:
        datos = json.load(f)                        # se vuelve a serializar compacto (y se valida que sea JSON)
    escribir(nombre, json.dumps(datos, ensure_ascii=False, separators=(',', ':')))
with open(os.path.join(D, 'relieve_etopo.jpg'), 'rb') as f:
    escribir('relieve', json.dumps('data:image/jpeg;base64,' + base64.b64encode(f.read()).decode('ascii')))
