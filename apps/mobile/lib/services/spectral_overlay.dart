class SpectralOverlayService {
  Future<Map<String, dynamic>> fetchOverlay() async {
    return {'status': 'cached', 'url': 'minio://spectral/fused_anomaly.tif'};
  }
}
