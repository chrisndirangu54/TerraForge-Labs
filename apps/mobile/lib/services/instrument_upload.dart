import 'api_client.dart';
import 'project_store.dart';

class InstrumentUploadService {
  InstrumentUploadService({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<Map<String, dynamic>> upload({
    required String instrumentType,
    required List<int> fileBytes,
    required String filename,
    String transport = 'file',
    String? projectId,
  }) async {
    return _client.uploadCapture(
      instrumentType: instrumentType,
      fileBytes: fileBytes,
      filename: filename,
      transport: transport,
      projectId: projectId ?? ProjectStore.instance.selectedProjectId,
    );
  }
}