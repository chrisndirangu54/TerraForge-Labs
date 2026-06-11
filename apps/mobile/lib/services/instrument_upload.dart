import 'api_client.dart';

class InstrumentUploadService {
  InstrumentUploadService({ApiClient? client})
      : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<Map<String, dynamic>> upload({
    required String instrumentType,
    required List<int> fileBytes,
    required String filename,
  }) async {
    return _client.uploadInstrument(
      instrumentType: instrumentType,
      fileBytes: fileBytes,
      filename: filename,
    );
  }
}
