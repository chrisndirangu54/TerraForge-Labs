class InstrumentUploadService {
  Future<Map<String, dynamic>> upload({required String instrumentType, required String filePath}) async {
    return {'status': 'queued_offline', 'instrumentType': instrumentType, 'filePath': filePath};
  }
}
