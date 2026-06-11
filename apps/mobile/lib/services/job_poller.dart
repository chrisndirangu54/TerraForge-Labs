import 'dart:async';

import 'api_client.dart';

class JobPollerService {
  JobPollerService({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<Map<String, dynamic>> poll(String jobId) async {
    return _client.get('/jobs/$jobId');
  }

  Future<Map<String, dynamic>> pollUntilComplete(
    String jobId, {
    Duration timeout = const Duration(seconds: 30),
    Duration interval = const Duration(milliseconds: 500),
  }) async {
    final deadline = DateTime.now().add(timeout);
    while (DateTime.now().isBefore(deadline)) {
      final status = await poll(jobId);
      final state = status['status']?.toString();
      if (state == 'complete' || state == 'failed') {
        return status;
      }
      await Future.delayed(interval);
    }
    throw TimeoutException('Job $jobId did not complete within $timeout');
  }
}
