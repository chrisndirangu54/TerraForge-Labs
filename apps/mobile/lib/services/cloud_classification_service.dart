import 'api_client.dart';
import 'job_poller.dart';

class CloudClassificationService {
  CloudClassificationService({
    ApiClient? client,
    JobPollerService? poller,
  })  : _client = client ?? ApiClient(),
        _poller = poller ?? JobPollerService();

  final ApiClient _client;
  final JobPollerService _poller;

  Future<Map<String, dynamic>> capabilities() {
    return _client.get('/classification/gpu/capabilities');
  }

  Future<Map<String, dynamic>> classifySync({
    required String task,
    String projectId = 'field-demo',
    double lon = 37.5,
    double lat = -1.15,
    String imageBase64 = '',
  }) {
    return _client.post('/classification/gpu/sync', {
      'task': task,
      'project_id': projectId,
      'lon': lon,
      'lat': lat,
      'image_base64': imageBase64,
      'async': false,
    });
  }

  Future<Map<String, dynamic>> classifyAsync({
    required String task,
    String projectId = 'field-demo',
    double lon = 37.5,
    double lat = -1.15,
    String imageBase64 = '',
  }) async {
    final started = await _client.post('/classification/gpu', {
      'task': task,
      'project_id': projectId,
      'lon': lon,
      'lat': lat,
      'image_base64': imageBase64,
      'async': true,
    });
    final jobId = started['job_id']?.toString();
    if (jobId == null) {
      return started;
    }
    return _poller.poll(jobId);
  }
}
