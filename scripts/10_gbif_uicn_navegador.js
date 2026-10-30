/* 10_gbif_uicn_navegador.js — Lista roja, mapa rojo
 * Corre EN TU NAVEGADOR (Chrome/Safari/Firefox), sin instalar nada y sin cuenta.
 * 1. Abrí https://api.gbif.org/v1/occurrence/search?country=AR&limit=0
 * 2. Abrí la consola: Chrome = Cmd+Option+J. (Chrome puede pedir que escribas "allow pasting" antes de pegar.)
 * 3. Pegá TODO este archivo y apretá Enter. Tarda unos minutos (98 especies).
 * 4. Se descargan 3 archivos: gbif_match_conteos_uicn.csv, ocurrencias_gbif.csv y gbif_predicado_taxonkeys.json.
 *    Movelos a la carpeta gbif/ del paquete.
 *
 * Qué hace, por especie:
 *  - /species/match            -> taxonKey aceptado por GBIF (control de sinonimias)
 *  - /occurrence/search limit=0 -> conteo 2012–2025 con coordenadas y sin problemas geoespaciales
 *  - /species/{key}/iucnRedListCategory -> categoría UICN GLOBAL tal como la publica GBIF (que la toma de la Lista Roja UICN)
 *  - /occurrence/search paginado (tope CAP por especie) -> puntos
 * IMPORTANTE: la API de búsqueda NO es citable. El dataset final se cita con la descarga oficial con DOI
 * (ver README, sección "Cuentas"). La categoría UICN que devuelve GBIF hay que citarla como
 * "UICN, vía GBIF, consultado AAAA-MM-DD"; para el año de evaluación hay que mirar iucnredlist.org.
 */
(async () => {
const LISTA = [["MAM001", "Dromiciops gliroides", "terrestre/dulceacuícola"], ["MAM002", "Rhyncholestes raphanurus", "terrestre/dulceacuícola"], ["MAM003", "Caluromys lanatus", "terrestre/dulceacuícola"], ["MAM004", "Chironectes minimus", "terrestre/dulceacuícola"], ["MAM005", "Gracilinanus microtarsus", "terrestre/dulceacuícola"], ["MAM006", "Metachirus nudicaudatus", "terrestre/dulceacuícola"], ["MAM007", "Monodelphis scalops", "terrestre/dulceacuícola"], ["MAM008", "Philander quica", "terrestre/dulceacuícola"], ["MAM009", "Myrmecophaga tridactyla", "terrestre/dulceacuícola"], ["MAM010", "Priodontes maximus", "terrestre/dulceacuícola"], ["MAM011", "Anoura caudifer", "terrestre/dulceacuícola"], ["MAM012", "Carollia perspicillata", "terrestre/dulceacuícola"], ["MAM013", "Glossophaga soricina", "terrestre/dulceacuícola"], ["MAM014", "Macrophyllum macrophyllum", "terrestre/dulceacuícola"], ["MAM015", "Micronycteris microtis", "terrestre/dulceacuícola"], ["MAM016", "Pygoderma bilabiatum", "terrestre/dulceacuícola"], ["MAM017", "Sturnira oporaphilum", "terrestre/dulceacuícola"], ["MAM018", "Vampyressa pusilla", "terrestre/dulceacuícola"], ["MAM019", "Myotis keaysi", "terrestre/dulceacuícola"], ["MAM020", "Alouatta caraya", "terrestre/dulceacuícola"], ["MAM021", "Alouatta guariba", "terrestre/dulceacuícola"], ["MAM022", "Aotus azarae", "terrestre/dulceacuícola"], ["MAM023", "Sapajus cay", "terrestre/dulceacuícola"], ["MAM024", "Sapajus nigritus", "terrestre/dulceacuícola"], ["MAM025", "Chrysocyon brachyurus", "terrestre/dulceacuícola"], ["MAM026", "Speothos venaticus", "terrestre/dulceacuícola"], ["MAM027", "Leopardus colocolo", "terrestre/dulceacuícola"], ["MAM028", "Leopardus guigna", "terrestre/dulceacuícola"], ["MAM029", "Leopardus guttulus", "terrestre/dulceacuícola"], ["MAM030", "Leopardus jacobita", "terrestre/dulceacuícola"], ["MAM031", "Leopardus pardalis", "terrestre/dulceacuícola"], ["MAM032", "Leopardus tigrinus", "terrestre/dulceacuícola"], ["MAM033", "Leopardus wiedii", "terrestre/dulceacuícola"], ["MAM034", "Panthera onca", "terrestre/dulceacuícola"], ["MAM035", "Lontra provocax", "terrestre/dulceacuícola"], ["MAM036", "Dicotyles tajacu", "terrestre/dulceacuícola"], ["MAM037", "Parachoerus wagneri", "terrestre/dulceacuícola"], ["MAM038", "Tayassu pecari", "terrestre/dulceacuícola"], ["MAM039", "Blastocerus dichotomus", "terrestre/dulceacuícola"], ["MAM040", "Hippocamelus antisensis", "terrestre/dulceacuícola"], ["MAM041", "Hippocamelus bisulcus", "terrestre/dulceacuícola"], ["MAM042", "Mazama americana", "terrestre/dulceacuícola"], ["MAM043", "Ozotoceros bezoarticus", "terrestre/dulceacuícola"], ["MAM044", "Pudu puda", "terrestre/dulceacuícola"], ["MAM045", "Balaenoptera borealis", "marino"], ["MAM046", "Balaenoptera musculus", "marino"], ["MAM047", "Balaenoptera physalus", "marino"], ["MAM048", "Cephalorhynchus eutropia", "marino"], ["MAM049", "Tursiops truncatus", "marino"], ["MAM050", "Physeter macrocephalus", "marino"], ["MAM051", "Pontoporia blainvillei", "marino"], ["MAM052", "Tapirus terrestris", "terrestre/dulceacuícola"], ["MAM053", "Abrawayaomys ruschii", "terrestre/dulceacuícola"], ["MAM054", "Akodon philipmyersi", "terrestre/dulceacuícola"], ["MAM055", "Bibimys torresi", "terrestre/dulceacuícola"], ["MAM056", "Castoria angustidens", "terrestre/dulceacuícola"], ["MAM057", "Delomys dorsalis", "terrestre/dulceacuícola"], ["MAM058", "Holochilus lagigliai", "terrestre/dulceacuícola"], ["MAM059", "Juliomys pictipes", "terrestre/dulceacuícola"], ["MAM060", "Oecomys franciscorum", "terrestre/dulceacuícola"], ["MAM061", "Oxymycterus wayku", "terrestre/dulceacuícola"], ["MAM062", "Phyllotis nogalaris", "terrestre/dulceacuícola"], ["MAM063", "Salinomys delicatus", "terrestre/dulceacuícola"], ["MAM064", "Tapecomys primus", "terrestre/dulceacuícola"], ["MAM065", "Abrocoma budini", "terrestre/dulceacuícola"], ["MAM066", "Abrocoma famatina", "terrestre/dulceacuícola"], ["MAM067", "Abrocoma schistacea", "terrestre/dulceacuícola"], ["MAM068", "Abrocoma uspallata", "terrestre/dulceacuícola"], ["MAM069", "Abrocoma vaccarum", "terrestre/dulceacuícola"], ["MAM070", "Dolichotis patagonum", "terrestre/dulceacuícola"], ["MAM071", "Chinchilla chinchilla", "terrestre/dulceacuícola"], ["MAM072", "Ctenomys australis", "terrestre/dulceacuícola"], ["MAM073", "Ctenomys bergi", "terrestre/dulceacuícola"], ["MAM074", "Ctenomys bonettoi", "terrestre/dulceacuícola"], ["MAM075", "Ctenomys dorbignyi", "terrestre/dulceacuícola"], ["MAM076", "Ctenomys emilianus", "terrestre/dulceacuícola"], ["MAM077", "Ctenomys latro", "terrestre/dulceacuícola"], ["MAM078", "Ctenomys magellanicus", "terrestre/dulceacuícola"], ["MAM079", "Ctenomys occultus", "terrestre/dulceacuícola"], ["MAM080", "Ctenomys osvaldoreigi", "terrestre/dulceacuícola"], ["MAM081", "Ctenomys pearsoni", "terrestre/dulceacuícola"], ["MAM082", "Ctenomys perrensi", "terrestre/dulceacuícola"], ["MAM083", "Ctenomys porteousi", "terrestre/dulceacuícola"], ["MAM084", "Ctenomys pundti", "terrestre/dulceacuícola"], ["MAM085", "Ctenomys rionegrensis", "terrestre/dulceacuícola"], ["MAM086", "Ctenomys roigi", "terrestre/dulceacuícola"], ["MAM087", "Ctenomys sociabilis", "terrestre/dulceacuícola"], ["MAM088", "Ctenomys talarum", "terrestre/dulceacuícola"], ["MAM089", "Ctenomys tuconax", "terrestre/dulceacuícola"], ["MAM090", "Ctenomys tucumanus", "terrestre/dulceacuícola"], ["MAM091", "Coendou bicolor", "terrestre/dulceacuícola"], ["MAM092", "Coendou prehensilis", "terrestre/dulceacuícola"], ["MAM093", "Aconaemys sagei", "terrestre/dulceacuícola"], ["MAM094", "Octodon ricardojeda", "terrestre/dulceacuícola"], ["MAM095", "Octomys mimax", "terrestre/dulceacuícola"], ["MAM096", "Tympanoctomys aureus", "terrestre/dulceacuícola"], ["MAM097", "Tympanoctomys kirchnerorum", "terrestre/dulceacuícola"], ["MAM098", "Tympanoctomys loschalchalerosorum", "terrestre/dulceacuícola"]]; // [especie_id, nombre_cientifico, ambito] — de especies_amenazadas.csv (Res. MAyDS 316/2021, Anexo I)
const CAP = 3000, API = "https://api.gbif.org/v1";
const F = "country=AR&year=2012,2025&hasCoordinate=true&hasGeospatialIssue=false&occurrenceStatus=PRESENT";
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function get(u){ for(let i=0;i<5;i++){ try{ const r=await fetch(u); if(r.ok) return r.json(); if(r.status===404) return null; }catch(e){} await sleep(1000*2**i);} return null; }
const q = s => '"' + String(s ?? "").replaceAll('"','""') + '"';
const filas=[["especie_id","nombre_lista","ambito","matchType","status","taxonKey","nombre_gbif","rank","n_2012_2025","n_total_AR","uicn_codigo","uicn_categoria"]];
const occ=[["especie_id","nombre_lista","species","taxonKey","decimalLatitude","decimalLongitude","year","coordinateUncertaintyInMeters","gbifID","datasetKey","license","basisOfRecord","dataGeneralizations"]];
const keys=[];
for (const [id, n, amb] of LISTA){
  const m = await get(`${API}/species/match?name=${encodeURIComponent(n)}&kingdom=Animalia&class=Mammalia`) || {};
  const key = m.acceptedUsageKey || m.usageKey;
  let c=null, cAll=null, u={};
  if (key && ["SPECIES","SUBSPECIES"].includes(m.rank)){
    keys.push(key);
    c = (await get(`${API}/occurrence/search?taxonKey=${key}&${F}&limit=0`))?.count ?? null;
    cAll = (await get(`${API}/occurrence/search?taxonKey=${key}&country=AR&limit=0`))?.count ?? null;
    u = await get(`${API}/species/${key}/iucnRedListCategory`) || {};
    for (let off=0; c && off<Math.min(c,CAP); off+=300){
      const p = await get(`${API}/occurrence/search?taxonKey=${key}&${F}&limit=300&offset=${off}`);
      if(!p) break;
      for (const o of p.results) occ.push([id,n,o.species,key,o.decimalLatitude,o.decimalLongitude,o.year,o.coordinateUncertaintyInMeters,o.gbifID ?? o.key,o.datasetKey,o.license,o.basisOfRecord,o.dataGeneralizations]);
      if (p.endOfRecords) break;
    }
  }
  filas.push([id,n,amb,m.matchType,m.status,key,m.species||m.canonicalName,m.rank,c,cAll,u.code,u.category]);
  console.log(id, n, "->", key, c, u.code||"");
}
const baja=(nombre,txt,tipo)=>{const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([txt],{type:tipo}));a.download=nombre;document.body.appendChild(a);a.click();a.remove();};
baja("gbif_match_conteos_uicn.csv", filas.map(r=>r.map(q).join(",")).join("\n"), "text/csv");
baja("ocurrencias_gbif.csv", occ.map(r=>r.map(q).join(",")).join("\n"), "text/csv");
const pred = {format:"SIMPLE_CSV", predicate:{type:"and", predicates:[
  {type:"in", key:"TAXON_KEY", values:[...new Set(keys)].map(String)},
  {type:"equals", key:"COUNTRY", value:"AR"},
  {type:"equals", key:"HAS_COORDINATE", value:"true"},
  {type:"equals", key:"HAS_GEOSPATIAL_ISSUE", value:"false"},
  {type:"equals", key:"OCCURRENCE_STATUS", value:"PRESENT"},
  {type:"greaterThanOrEquals", key:"YEAR", value:"2012"},
  {type:"lessThanOrEquals", key:"YEAR", value:"2025"}]}};
baja("gbif_predicado_taxonkeys.json", JSON.stringify(pred,null,2), "application/json");
console.log("Listo:", filas.length-1, "especies,", occ.length-1, "puntos");
})();
