import 'api_client.dart';

class OfflineMapPack {
  final String region;
  final String pmtilesPath;
  final int estimatedSizeMb;

  const OfflineMapPack({
    required this.region,
    required this.pmtilesPath,
    required this.estimatedSizeMb,
  });

  factory OfflineMapPack.fromJson(Map<String, dynamic> json) {
    return OfflineMapPack(
      region: json['region']?.toString() ?? 'unknown',
      pmtilesPath: json['pmtiles_path']?.toString() ??
          json['pmtilesPath']?.toString() ??
          '',
      estimatedSizeMb: (json['estimated_size_mb'] as num?)?.toInt() ??
          (json['estimatedSizeMb'] as num?)?.toInt() ??
          0,
    );
  }
}

class MapService {
  MapService({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  static const String defaultProvider = 'maplibre_openfreemap';
  static const String paidProvider = 'google_maps_optional';

  Future<Map<String, dynamic>> fetchLayers() async {
    return _client.get('/mapping/layers');
  }

  Future<Map<String, dynamic>> fetchTile(int z, int x, int y) async {
    return _client.get('/tiles/$z/$x/$y');
  }

  Future<Map<String, dynamic>> fetchOfflinePack(
    String region, {
    bool includeSatellite = true,
  }) async {
    return _client.get(
      '/tiles/offline/$region',
      query: {'include_satellite': includeSatellite.toString()},
    );
  }

  OfflineMapPack kenyaPack({bool includeSatellite = true}) {
    return OfflineMapPack(
      region: 'kenya',
      pmtilesPath:
          includeSatellite ? 'kenya_satellite.pmtiles' : 'kenya_osm.pmtiles',
      estimatedSizeMb: includeSatellite ? 2048 : 800,
    );
  }
}
