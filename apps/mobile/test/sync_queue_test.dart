import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:terraforge_mobile/services/sync_queue.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory tempDir;

  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  setUp(() async {
    tempDir = await Directory(
      p.join(Directory.systemTemp.path, 'terraforge_sync_test'),
    ).create(recursive: true);
  });

  tearDown(() async {
    if (await tempDir.exists()) {
      await tempDir.delete(recursive: true);
    }
  });

  test('content hash is stable for identical payloads', () {
    final hashA = SyncQueue.contentHash([1, 2, 3, 4]);
    final hashB = SyncQueue.contentHash([1, 2, 3, 4]);
    expect(hashA, hashB);
  });

  test('enqueue deduplicates by content hash', () async {
    final queue = SyncQueue(baseDirectory: tempDir.path);
    final bytes = [10, 20, 30, 40];

    final first = await queue.enqueue(
      instrumentType: 'terrameter',
      filename: 'sample_a.xml',
      fileBytes: bytes,
      metadata: {'profile_id': 'P-01'},
    );
    final second = await queue.enqueue(
      instrumentType: 'terrameter',
      filename: 'sample_b.xml',
      fileBytes: bytes,
      metadata: {'profile_id': 'P-02'},
    );

    expect(first, isNotNull);
    expect(second, isNotNull);
    expect(first!.id, second!.id);
    expect(first.contentHash, second.contentHash);

    final summary = await queue.summary();
    expect(summary.pending, 1);

    await queue.close();
  });
}