/* 09_gee_ecorregion_anual.js — Lista roja, mapa rojo
 * Corre en el Code Editor de Google Earth Engine: https://code.earthengine.google.com
 * (necesita tu cuenta de Earth Engine registrada para uso no comercial; ver README, sección "Cuentas").
 * Pegá el script, apretá "Run", y en la pestaña "Tasks" (derecha) apretá "RUN" en la tarea de exportación.
 * El CSV llega a tu Google Drive (carpeta "lista_roja_mapa_rojo"). Bajalo y ponelo en el paquete como eco_anio.csv.
 *
 * Salida: una fila por ecorregión × año (2012–2025) con:
 *   nombre (RESOLVE ECO_NAME, igual al campo `nombre` de ecorregiones.geojson), anio, area_ha,
 *   ha_quemadas          área quemada (MODIS MCD64A1 v6.1, 500 m; un píxel cuenta una vez por año)
 *   ha_ap_nominal        superficie bajo alguna área protegida creada hasta ese año (WDPA, STATUS_YR <= anio)
 *   ha_ap_estricta       ídem, solo categorías UICN Ia, Ib, II, III, IV
 *   ha_quemadas_en_ap    área quemada dentro de áreas protegidas vigentes ese año
 *   viirs_media          radiancia nocturna media (VIIRS VNL v2.2 anual; vacío si el año no existe en el catálogo)
 *
 * Fuentes (ver FUENTES_Y_CITAS.md):
 *   RESOLVE/ECOREGIONS/2017 (CC BY 4.0) · USDOS/LSIB_SIMPLE/2017 (dominio público, límite país)
 *   MODIS/061/MCD64A1 (NASA LP DAAC, sin restricciones) · NOAA/VIIRS/DNB/ANNUAL_V22 (EOG/Payne Institute, CC BY 4.0)
 *   WCMC/WDPA/current/polygons (UNEP-WCMC & IUCN, uso no comercial con atribución)
 * AVISOS:
 *   - Los IDs de los catálogos salen de la documentación de Earth Engine, NO de las fuentes que bajó el paquete:
 *     si alguno da error "not found", buscá el nombre en el catálogo y reemplazá el ID.
 *   - WDPA es la alternativa dentro de Earth Engine a Tomba 2025 (Mendeley). Sus coberturas no van a coincidir
 *     con Tomba ni con SIFAP: declaralo en el método. Áreas con STATUS_YR = 0 (año desconocido) quedan fuera.
 *   - 500 m subestima quemas chicas (pastizales, Delta). El límite LSIB excluye Malvinas; el paquete las incluye.
 *   - Opcional (no incluido): gHM v3 y MapBiomas ráster. Agregalos solo con el ID verificado en el catálogo.
 */
var ANIOS = ee.List.sequence(2012, 2025);
var arg = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
  .filter(ee.Filter.eq('country_na', 'Argentina')).geometry();

var eco = ee.FeatureCollection('RESOLVE/ECOREGIONS/2017')
  .filterBounds(arg)
  .map(function (f) {
    var g = f.geometry().intersection(arg, ee.ErrorMargin(500));
    return ee.Feature(g, {nombre: f.get('ECO_NAME'), area_ha: g.area(500).divide(1e4)});
  })
  .filter(ee.Filter.gt('area_ha', 1000));

var ap = ee.FeatureCollection('WCMC/WDPA/current/polygons')
  .filter(ee.Filter.eq('ISO3', 'ARG'))
  .filter(ee.Filter.inList('STATUS', ['Designated', 'Established', 'Inscribed']))
  .filter(ee.Filter.neq('MARINE', '2'))
  .filter(ee.Filter.gt('STATUS_YR', 0));
var apAnio = ap.reduceToImage(['STATUS_YR'], ee.Reducer.min());
var apAnioEstricta = ap.filter(ee.Filter.inList('IUCN_CAT', ['Ia', 'Ib', 'II', 'III', 'IV']))
  .reduceToImage(['STATUS_YR'], ee.Reducer.min());
var ha = ee.Image.pixelArea().divide(1e4);

function porAnio(y) {
  y = ee.Number(y);
  var ini = ee.Date.fromYMD(y, 1, 1), fin = ini.advance(1, 'year');
  var ba = ee.ImageCollection('MODIS/061/MCD64A1').filterDate(ini, fin).select('BurnDate');
  var quem = ee.Image(ee.Algorithms.If(ba.size().gt(0),
    ba.map(function (i) { return i.gt(0); }).max(), ee.Image(0))).unmask(0).rename('q');
  var enAp = apAnio.lte(y).unmask(0);
  var enApE = apAnioEstricta.lte(y).unmask(0);
  var img = quem.multiply(ha).rename('ha_quemadas')
    .addBands(enAp.multiply(ha).rename('ha_ap_nominal'))
    .addBands(enApE.multiply(ha).rename('ha_ap_estricta'))
    .addBands(quem.multiply(enAp).multiply(ha).rename('ha_quemadas_en_ap'));
  var sumas = img.reduceRegions({collection: eco, reducer: ee.Reducer.sum(), scale: 500, tileScale: 8});

  var vc = ee.ImageCollection('NOAA/VIIRS/DNB/ANNUAL_V22').filterDate(ini, fin).select('average');
  var conViirs = ee.FeatureCollection(ee.Algorithms.If(vc.size().gt(0),
    vc.first().reduceRegions({collection: sumas, reducer: ee.Reducer.mean().setOutputs(['viirs_media']),
      scale: 1000, tileScale: 8}),
    sumas));
  return conViirs.map(function (f) { return f.set('anio', y); });
}

var tabla = ee.FeatureCollection(ANIOS.map(porAnio)).flatten();
print('Ejemplo (primeras filas):', tabla.limit(5));
Map.addLayer(eco, {}, 'Ecorregiones RESOLVE recortadas');
Map.centerObject(arg, 4);

Export.table.toDrive({
  collection: tabla,
  description: 'eco_anio_2012_2025',
  folder: 'lista_roja_mapa_rojo',
  fileFormat: 'CSV',
  selectors: ['nombre', 'anio', 'area_ha', 'ha_quemadas', 'ha_ap_nominal', 'ha_ap_estricta',
              'ha_quemadas_en_ap', 'viirs_media']
});
