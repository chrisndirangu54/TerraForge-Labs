import 'api_client.dart';

class SpectralOverlayService {
  SpectralOverlayService({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<Map<String, dynamic>> fuseSpectral({
    String dataType = 'hyperspectral',
    String filepath = 'kwale_hsi.hdr',
  }) async {
    return _client.post('/fuse-spectral', {
      'data_type': dataType,
      'filepath': filepath,
    });
  }
}