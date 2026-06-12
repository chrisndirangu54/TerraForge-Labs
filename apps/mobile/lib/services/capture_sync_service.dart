import 'dart:io';

import 'instrument_upload.dart';
import 'sync_queue.dart';

class CaptureSyncService {
  CaptureSyncService({
    SyncQueue? queue,
    InstrumentUploadService? uploadService,
  })  : _queue = queue ?? SyncQueue(),
        _upload = uploadService ?? InstrumentUploadService();

  final SyncQueue _queue;
  final InstrumentUploadService _upload;

  Future<SyncQueueSummary> summary() => _queue.summary();

  Future<List<SyncQueueEntry>> listAll({int limit = 100}) =>
      _queue.listAll(limit: limit);

  Future<SyncQueueEntry?> enqueueFile({
    required String instrumentType,
    required String filename,
    required List<int> fileBytes,
    Map<String, dynamic>? metadata,
  }) {
    return _queue.enqueue(
      instrumentType: instrumentType,
      filename: filename,
      fileBytes: fileBytes,
      metadata: metadata,
    );
  }

  Future<int> flushPending({
    String transport = 'file',
    String? projectId,
  }) async {
    final pending = await _queue.listPending();
    var uploaded = 0;
    for (final entry in pending) {
      await _queue.markUploading(entry.id);
      try {
        final bytes = await File(entry.filePath).readAsBytes();
        await _upload.upload(
          instrumentType: entry.instrumentType,
          fileBytes: bytes,
          filename: entry.filename,
          transport: transport,
          projectId: projectId,
        );
        await _queue.markCompleted(entry.id);
        uploaded++;
      } catch (error) {
        await _queue.markFailed(entry.id, error.toString());
      }
    }
    return uploaded;
  }
}