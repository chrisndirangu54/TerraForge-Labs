import 'api_client.dart';

class JobPollerService {
  JobPollerService({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<Map<String, dynamic>> poll(String jobId) async {
    return _client.get('/jobs/$jobId');
  }
}
