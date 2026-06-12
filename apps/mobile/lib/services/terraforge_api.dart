import 'api_client.dart';

class TerraforgeApi {
  TerraforgeApi({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<Map<String, dynamic>> health() => _client.get('/health');

  Future<Map<String, dynamic>> runKriging({
    String element = 'ta_ppm',
    List<Map<String, dynamic>>? observations,
  }) {
    return _client.post('/fuse-geodata', {
      'element': element,
      if (observations != null) 'observations': observations,
    });
  }

  Future<Map<String, dynamic>> generateJorcReport({
    String projectName = 'TerraForge Demo',
    String commodity = 'Ta',
  }) {
    return _client.post('/reports/jorc', {
      'project_name': projectName,
      'commodity': commodity,
    });
  }

  Future<Map<String, dynamic>> groundwaterTable({String bbox = ''}) {
    return _client.get('/hydro/groundwater-table', query: {'bbox': bbox});
  }

  Future<Map<String, dynamic>> boreholes({String bbox = ''}) {
    return _client.get('/hydro/boreholes', query: {'bbox': bbox});
  }

  Future<Map<String, dynamic>> settlements({String bbox = ''}) {
    return _client.get('/urban/settlements', query: {'bbox': bbox});
  }

  Future<Map<String, dynamic>> roads({String bbox = ''}) {
    return _client.get('/infra/roads', query: {'bbox': bbox});
  }

  Future<Map<String, dynamic>> satelliteScenes({
    String bbox = '37.45,-1.20,37.55,-1.10',
  }) {
    return _client.get(
      '/satellite/scenes',
      query: {'bbox': bbox, 'start': '2026-01-01', 'end': '2026-06-30'},
    );
  }

  Future<Map<String, dynamic>> fuseSeismic() {
    return _client.post('/fuse-seismic', {'filepath': 'demo_segy.sgy'});
  }

  Future<Map<String, dynamic>> classifyThinSection() {
    return _client.post('/classify-thin-section', {
      'image_path': 'demo_thin_section.jpg',
    });
  }
}