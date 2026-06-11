import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';

import 'api_client.dart';
import 'sync_queue.dart';

class InstrumentUploadService {
  InstrumentUploadService({
    ApiClient? client,
    SyncQueue? queue,
    Connectivity? connectivity,
  })  : _client = client ?? ApiClient(),
        _queue = queue ?? SyncQueue(),
        _connectivity = connectivity ?? Connectivity();

  final ApiClient _client;
  final SyncQueue _queue;
  final Connectivity _connectivity;

  Future<bool> _isOnline() async {
    final results = await _connectivity.checkConnectivity();
    return !results.contains(ConnectivityResult.none);
  }

  Future<Map<String, dynamic>> upload({
    required String instrumentType,
    required List<int> fileBytes,
    required String filename,
    Map<String, dynamic>? metadata,
  }) async {
    final contentHash = SyncQueue.contentHash(fileBytes);
    final existing = await _queue.findByHash(contentHash);
    if (existing != null &&
        existing.status != SyncQueueStatus.completed) {
      return {
        'queued': true,
        'deduplicated': true,
        'queue_id': existing.id,
        'content_hash': contentHash,
        'status': existing.status.name,
      };
    }

    if (!await _isOnline()) {
      final entry = await _queue.enqueue(
        instrumentType: instrumentType,
        filename: filename,
        fileBytes: fileBytes,
        metadata: metadata,
      );
      return {
        'queued': true,
        'queue_id': entry?.id,
        'content_hash': contentHash,
        'status': 'pending',
        'metadata': metadata ?? {},
      };
    }

    return _uploadNow(
      instrumentType: instrumentType,
      fileBytes: fileBytes,
      filename: filename,
      metadata: metadata,
      contentHash: contentHash,
    );
  }

  Future<Map<String, dynamic>> _uploadNow({
    required String instrumentType,
    required List<int> fileBytes,
    required String filename,
    Map<String, dynamic>? metadata,
    required String contentHash,
    SyncQueueEntry? queuedEntry,
  }) async {
    final entry = queuedEntry ??
        await _queue.enqueue(
          instrumentType: instrumentType,
          filename: filename,
          fileBytes: fileBytes,
          metadata: metadata,
        );
    if (entry == null) {
      throw StateError('Unable to persist upload for retry');
    }

    await _queue.markUploading(entry.id);
    try {
      final response = await _client.uploadInstrument(
        instrumentType: instrumentType,
        fileBytes: fileBytes,
        filename: filename,
      );
      await _queue.markCompleted(entry.id);
      return {
        ...response,
        'queue_id': entry.id,
        'content_hash': contentHash,
        'metadata': metadata ?? entry.metadata,
        'resumable': true,
      };
    } catch (error) {
      await _queue.markFailed(entry.id, error.toString());
      return {
        'queued': true,
        'queue_id': entry.id,
        'content_hash': contentHash,
        'status': 'failed',
        'error': error.toString(),
        'metadata': metadata ?? entry.metadata,
      };
    }
  }

  Future<List<Map<String, dynamic>>> flushQueue() async {
    if (!await _isOnline()) {
      return const [];
    }

    final pending = await _queue.listPending();
    final results = <Map<String, dynamic>>[];
    for (final entry in pending) {
      final file = File(entry.filePath);
      if (!await file.exists()) {
        await _queue.markFailed(entry.id, 'Queued file missing on disk');
        continue;
      }
      final bytes = await file.readAsBytes();
      final response = await _uploadNow(
        instrumentType: entry.instrumentType,
        fileBytes: bytes,
        filename: entry.filename,
        metadata: entry.metadata,
        contentHash: entry.contentHash,
        queuedEntry: entry,
      );
      results.add({
        'queue_id': entry.id,
        'content_hash': entry.contentHash,
        ...response,
      });
    }
    return results;
  }

  Future<SyncQueueSummary> queueSummary() => _queue.summary();

  Future<List<SyncQueueEntry>> listQueue({int limit = 100}) {
    return _queue.listAll(limit: limit);
  }
}