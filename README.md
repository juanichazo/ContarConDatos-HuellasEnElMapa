# Huellas en el mapa

¿Dónde viven las especies amenazadas de Argentina y qué le pasa al territorio que habitan?

Cruce de las **205 especies de mamíferos y aves nacionalmente amenazadas** (Res. 316/2021 y Res. 795/2017) con **162.717 registros de GBIF (2012–2025)**, ecorregiones y presiones sobre el territorio (áreas protegidas, focos de calor, vegetación nativa, incendios).

- **Explorador interactivo:** [`site/index.html`](site/index.html)
- **Historia visual:** [`site/historia.html`](site/historia.html)

Presentado al Concurso Nacional de Visualización de Datos «Contar con Datos» 2026.

## Verlo localmente

```
cd site
python -m http.server 8000
```

Abrir http://localhost:8000/ (no funciona con doble clic: el navegador bloquea la lectura de los `.json` desde `file://`).

## Estructura

```
site/        sitio estático (HTML + MapLibre GL JS + datos en JSON)
scripts/     procesamiento de datos, numerado en orden de ejecución
raw/         insumos crudos (salvo la descarga GBIF, ver abajo)
presiones/   capas de presión procesadas
gbif/, gbif_doi/, web_data/   resultados intermedios
```

Para rehacer los datos del sitio: `pip install -r requirements.txt`, ubicar la descarga GBIF en `raw/gbif_descarga/` y correr, desde la raíz, `python scripts/20_armar_datos_web.py` y `python scripts/21_registros_dentro_ap.py`.

## Fuentes

| Qué | Fuente | Licencia |
|---|---|---|
| Mamíferos amenazados | Res. MAyDS 316/2021, Anexo I. https://www.argentina.gob.ar/normativa/nacional/norma-354496/texto | Norma pública |
| Aves amenazadas | Res. MAyDS 795/2017, Anexo I. https://www.argentina.gob.ar/normativa/nacional/norma-287278/texto | Norma pública |
| Registros de presencia | GBIF.org (29/10/2026). GBIF Occurrence Download. https://doi.org/10.15468/dl.t87f4d | CC BY-NC 4.0 |
| Categoría UICN global | Lista Roja de la UICN, vía API de GBIF. https://www.iucnredlist.org | Uso no comercial |
| Ecorregiones | Dinerstein et al. (2017), *BioScience* 67(6). https://doi.org/10.1093/biosci/bix014 | CC BY 4.0 |
| Provincias | INDEC, Codgeo. https://www.indec.gob.ar/ftp/cuadros/territorio/codgeo/Codgeo_Pais_x_prov_datos.zip | Datos públicos |
| Áreas protegidas | Tomba, A. (2025). Mendeley Data, V1. https://doi.org/10.17632/wggsh3dszp.1 | CC BY 4.0 |
| Focos de calor | NASA FIRMS, VIIRS S-NPP y MODIS C6.1. https://firms.modaps.eosdis.nasa.gov/country/ | Libre con cita |
| Vegetación nativa | MapBiomas Argentina, Colección 3. https://argentina.mapbiomas.org/descargas/estadisticas/ | CC BY 4.0 |
| Incendios reportados | Servicio Nacional de Manejo del Fuego. https://datos.gob.ar/dataset/ambiente-incendios-forestales | Datos abiertos |
| Rangos de mamíferos | Marsh et al. (2022), *J. Biogeography* 49(5). https://doi.org/10.1111/jbi.14330 · https://zenodo.org/records/6644198 | CC BY 4.0 |
| Relieve del mapa base | Natural Earth (dominio público) — a confirmar | Dominio público |
| Mapas web | MapLibre GL JS 5.24.0. https://maplibre.org | BSD-3 |

La descarga GBIF original (142 MB) no está en el repositorio por tamaño; se obtiene desde el DOI. Los datos derivados de GBIF son de uso **no comercial** (CC BY-NC 4.0).
