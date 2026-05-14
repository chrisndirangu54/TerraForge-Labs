class OfflineMapPack {
  final String region;
  final String pmtilesPath;
  final int estimatedSizeMb;

  const OfflineMapPack({required this.region, required this.pmtilesPath, required this.estimatedSizeMb});
}

class MapService {
  static const String defaultProvider = 'maplibre_openfreemap';
  static const String paidProvider = 'google_maps_optional';

  OfflineMapPack kenyaPack({bool includeSatellite = true}) {
    return OfflineMapPack(
      region: 'kenya',
      pmtilesPath: includeSatellite ? 'kenya_satellite.pmtiles' : 'kenya_osm.pmtiles',
      estimatedSizeMb: includeSatellite ? 2048 : 800,
    );
  }
}
