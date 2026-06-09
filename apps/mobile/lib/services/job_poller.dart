class JobPollerService {
  Future<Map<String, dynamic>> poll(String jobId) async {
    return {'job_id': jobId, 'status': 'complete'};
  }
}
