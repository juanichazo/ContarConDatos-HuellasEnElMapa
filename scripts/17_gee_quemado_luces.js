/* 17_gee_quemado_luces.js — Lista roja, mapa rojo · Google Earth Engine Code Editor
 * Reemplaza al script 09 (las áreas protegidas ya vienen de Tomba 2025, no de WDPA).
 * Calcula, por ecorregión RESOLVE (recortada a Argentina) y por hexágono H3 res 4 del paquete, año por año:
 *   ha_quemadas   MODIS/061/MCD64A1 (MCD64A1.061, 500 m, mensual). Un píxel cuenta una vez por año si BurnDate > 0
 *                 en algún mes. Solo celdas de tierra (QA bit 0 = 1). 2012–2025.
 *                 doi:10.5067/MODIS/MCD64A1.061 · sin restricciones de uso (LP DAAC).
 *   ntl_media     NOAA/VIIRS/DNB/ANNUAL_V21 (2013–2021) + ANNUAL_V22 (2022–2025), banda average_masked (nW/cm²/sr): radiancia media anual con fondo y
 *                 luces efímeras (fuego, barcos) enmascarados por EOG. CORREGIDO 30/10/2026 tras consultar la colección en Earth Engine:
 *                 V22 solo tiene 2022–2025, V21 tiene 2013–2021; 2012 no existe.
 *                 Elvidge et al. (2021) Remote Sensing 13(5):922, doi:10.3390/rs13050922 · dominio público.
 *   ntl_suma      ntl_media × km² del polígono (proxy de cantidad total de luz), 2013–2025.
 * Límite del país: USDOS/LSIB_SIMPLE/2017 (excluye Malvinas; ⚠ ID tomado de mi conocimiento, ya usado en el script 09).
 * Salida: dos tareas de exportación a Drive (carpeta huellas_en_el_mapa): gee_eco_anio.csv y gee_hex4_anio.csv.
 * HEX = [[h3, [[lon,lat],…]], …] se pega abajo (2.078 celdas, de presiones/hex_h4_base.geojson).
 */
var HEX = __HEX__;
var ECO = {'Patagonian steppe':'E01','Dry Chaco':'E02','Humid Pampas':'E03','Low Monte':'E04','Espinal':'E05',
  'Humid Chaco':'E06','High Monte':'E07','Southern Andean steppe':'E08','Central Andean puna':'E09',
  'Southern Andean Yungas':'E10','Valdivian temperate forests':'E11','Paraná flooded savanna':'E12',
  'Central Andean dry puna':'E13','Magellanic subpolar forests':'E14','Southern Cone Mesopotamian savanna':'E15',
  'Alto Paraná Atlantic forests':'E16','Araucaria moist forests':'E17','Rock and Ice':'E18',
  'Uruguayan savanna':'E19','Chilean Matorral':'E20'};
var arg = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filter(ee.Filter.eq('country_na', 'Argentina')).geometry();
var ecoFC = ee.FeatureCollection('RESOLVE/ECOREGIONS/2017')
  .filter(ee.Filter.inList('ECO_NAME', Object.keys(ECO))).filterBounds(arg)
  .map(function (f) { return ee.Feature(f.geometry().intersection(arg, ee.ErrorMargin(500)),
    {id: ee.Dictionary(ECO).get(f.get('ECO_NAME'))}); });
var hexFC = ee.FeatureCollection(HEX.map(function (h) { return ee.Feature(ee.Geometry.Polygon([h[1]]), {id: h[0]}); }));
var tierra = ee.Image('MODIS/061/MCD64A1/2012_01_01').select('QA').bitwiseAnd(1).eq(1);
var areaHa = ee.Image.pixelArea().divide(1e4);
function imagenAnio(y) {
  var ini = ee.Date.fromYMD(y, 1, 1), fin = ini.advance(1, 'year');
  var q = ee.ImageCollection('MODIS/061/MCD64A1').filterDate(ini, fin).select('BurnDate')
    .map(function (i) { return i.gt(0); }).max().unmask(0).updateMask(tierra);
  var img = q.multiply(areaHa).rename('ha_quemadas');
  var nl = ee.ImageCollection('NOAA/VIIRS/DNB/ANNUAL_V21').merge(ee.ImageCollection('NOAA/VIIRS/DNB/ANNUAL_V22')).filterDate(ini, fin);
  var luz = ee.Image(ee.Algorithms.If(nl.size().gt(0), ee.Image(nl.first()).select('average_masked').unmask(0),
                                      ee.Image.constant(-1))).rename('ntl');
  return {img: img, luz: luz};
}
function tabla(fc, escalaFuego) {
  var anios = ee.List.sequence(2012, 2025);
  return ee.FeatureCollection(anios.map(function (y) {
    y = ee.Number(y); var x = imagenAnio(y);
    var a = x.img.reduceRegions({collection: fc, reducer: ee.Reducer.sum().setOutputs(['ha_quemadas']), scale: escalaFuego, tileScale: 4});
    var b = x.luz.reduceRegions({collection: a, reducer: ee.Reducer.mean().setOutputs(['ntl']), scale: 463.83, tileScale: 4});
    return b.map(function (f) {
      var km2 = f.geometry().area(1000).divide(1e6), n = ee.Number(f.get('ntl'));
      return ee.Feature(null, {id: f.get('id'), anio: y, km2: km2, ha_quemadas: f.get('ha_quemadas'),
        ntl_media: n, ntl_suma: n.multiply(km2)});   // ntl_media = -1 significa "año sin dato" (2025)
    });
  })).flatten();
}
var tEco = tabla(ecoFC, 463.31), tHex = tabla(hexFC, 463.31);
var sel = ['id', 'anio', 'km2', 'ha_quemadas', 'ntl_media', 'ntl_suma'];
// getDownloadURL se cuelga con tablas tan grandes: se exporta a Drive (pestaña Tasks → RUN en cada una).
Export.table.toDrive({collection: tEco, description: 'gee_eco_anio', folder: 'huellas_en_el_mapa', fileFormat: 'CSV', selectors: sel});
Export.table.toDrive({collection: tHex, description: 'gee_hex4_anio', folder: 'huellas_en_el_mapa', fileFormat: 'CSV', selectors: sel});
print('control ecorregiones', ecoFC.size());
