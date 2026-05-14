export const phase4ApiEndpoints = {
  mapping: ['/tiles/{z}/{x}/{y}', '/tiles/offline/{region}', '/basemap/sentinel2', '/mapping/layers'],
  hydrogeology: ['/hydro/slug-test', '/hydro/pump-test', '/hydro/water-quality', '/hydro/modflow'],
  urban: ['/urban/classify-settlement', '/urban/service-access', '/urban/suitability', '/urban/conflict-check'],
  infrastructure: ['/infra/route', '/infra/pipeline-route', '/infra/mining-assessment'],
  satellite: ['/satellite/scenes', '/satellite/latest', '/satellite/change-detect', '/satellite/insar'],
};
