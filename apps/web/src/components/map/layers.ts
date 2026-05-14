export const layerGroups = {
  geological: ['kriging_grade_heatmap', 'deposit_model_mesh', 'drillhole_traces', 'sample_points', 'structural_measurements'],
  hydrogeology: ['groundwater_table_surface', 'aquifer_zones', 'borehole_water_levels', 'recharge_zones', 'contamination_plumes'],
  urban: ['settlement_boundaries', 'building_footprints', 'roads_tracks', 'utilities', 'land_use_zoning'],
  infrastructure: ['road_network', 'power_grid', 'water_pipelines', 'telecoms_towers', 'haulage_route'],
  satellite: ['latest_sentinel2_rgb', 'sar_intensity', 'thermal', 'insar_deformation'],
};

export const mapModes = ['2d_street', '2d_satellite', '2d_hybrid', '3d_terrain', '3d_geological', 'google_satellite', 'google_photorealistic_3d'];
