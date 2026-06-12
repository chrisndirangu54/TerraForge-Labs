export const phase4ApiEndpoints = {
  cloudGpu: [
    '/classification/gpu/capabilities',
    '/classification/gpu',
    '/classification/gpu/sync',
    '/classification/gpu/batch',
  ],
  mapping: ['/tiles/{z}/{x}/{y}', '/tiles/offline/{region}', '/basemap/sentinel2', '/mapping/layers'],
  hydrogeology: ['/hydro/slug-test', '/hydro/pump-test', '/hydro/water-quality', '/hydro/modflow'],
  urban: ['/urban/classify-settlement', '/urban/service-access', '/urban/suitability', '/urban/conflict-check'],
  infrastructure: ['/infra/route', '/infra/pipeline-route', '/infra/mining-assessment'],
  satellite: ['/satellite/scenes', '/satellite/latest', '/satellite/change-detect', '/satellite/insar'],
  gapClosure: ['/targeting/drill-plan-optimise', '/geochemistry/qaqc', '/platform/lims/sample-event', '/environment/flood-inundation'],
  ethnolinguistics: ['/ethnolinguistics/record-term', '/ethnolinguistics/toponym-analysis', '/ethnolinguistics/knowledge-layer'],
};