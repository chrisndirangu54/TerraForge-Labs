import 'dart:convert';
import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:sqflite/sqflite.dart';

import 'rule_based_classifier.dart';

enum SyncQueueStatus {
  pending,
  uploading,
  completed,
  failed,
}

class SyncQueueEntry {
  final int id;
  final String instrumentType;
  final String filename;
  final String contentHash;
  final String filePath;
  final Map<String, dynamic> metadata;
  final SyncQueueStatus status;
  final int attempts;
  final String? lastError;
  final DateTime createdAt;
  final DateTime updatedAt;

  SyncQueueEntry({
    required this.id,
    required this.instrumentType,
    required this.filename,
    required this.contentHash,
    required this.filePath,
    required this.metadata,
    required this.status,
    required this.attempts,
    required this.lastError,
    required this.createdAt,
    required this.updatedAt,
  });

  factory SyncQueueEntry.fromMap(Map<String, dynamic> map) {
    return SyncQueueEntry(
      id: map['id'] as int,
      instrumentType: map['instrument_type'] as String,
      filename: map['filename'] as String,
      contentHash: map['content_hash'] as String,
      filePath: map['file_path'] as String,
      metadata: _decodeMetadata(map['metadata'] as String?),
      status: _statusFromString(map['status'] as String),
      attempts: map['attempts'] as int? ?? 0,
      lastError: map['last_error'] as String?,
      createdAt: DateTime.parse(map['created_at'] as String),
      updatedAt: DateTime.parse(map['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'instrument_type': instrumentType,
      'filename': filename,
      'content_hash': contentHash,
      'file_path': filePath,
      'metadata': metadata,
      'status': status.name,
      'attempts': attempts,
      'last_error': lastError,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}

class SyncQueueSummary {
  final int pending;
  final int uploading;
  final int completed;
  final int failed;

  const SyncQueueSummary({
    required this.pending,
    required this.uploading,
    required this.completed,
    required this.failed,
  });

  int get total => pending + uploading + completed + failed;
}

class SyncQueue {
  SyncQueue({Database? database, String? baseDirectory})
      : _database = database,
        _baseDirectory = baseDirectory;

  Database? _database;
  String? _queueDir;
  final String? _baseDirectory;

  static String contentHash(List<int> bytes) {
    final seed = RuleBasedClassifier.seedFromBytes(bytes, 'sync-queue');
    return seed.toRadixString(16).padLeft(8, '0');
  }

  Future<Database> _db() async {
    if (_database != null) {
      return _database!;
    }
    final basePath = _baseDirectory ??
        (await getApplicationDocumentsDirectory()).path;
    final dbPath = p.join(basePath, 'terraforge_sync_queue.db');
    _database = await openDatabase(
      dbPath,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE upload_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument_type TEXT NOT NULL,
            filename TEXT NOT NULL,
            content_hash TEXT NOT NULL UNIQUE,
            file_path TEXT NOT NULL,
            metadata TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
          )
        ''');
      },
    );
    return _database!;
  }

  Future<String> _ensureQueueDir() async {
    if (_queueDir != null) {
      return _queueDir!;
    }
    final basePath = _baseDirectory ??
        (await getApplicationDocumentsDirectory()).path;
    final queueDir = Directory(p.join(basePath, 'upload_queue'));
    if (!await queueDir.exists()) {
      await queueDir.create(recursive: true);
    }
    _queueDir = queueDir.path;
    return _queueDir!;
  }

  Future<SyncQueueEntry?> enqueue({
    required String instrumentType,
    required String filename,
    required List<int> fileBytes,
    Map<String, dynamic>? metadata,
  }) async {
    final hash = contentHash(fileBytes);
    final existing = await findByHash(hash);
    if (existing != null) {
      return existing;
    }

    final queueDir = await _ensureQueueDir();
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final storedName = '${timestamp}_$filename';
    final filePath = p.join(queueDir, storedName);
    await File(filePath).writeAsBytes(fileBytes, flush: true);

    final now = DateTime.now().toIso8601String();
    final db = await _db();
    final id = await db.insert(
      'upload_queue',
      {
        'instrument_type': instrumentType,
        'filename': filename,
        'content_hash': hash,
        'file_path': filePath,
        'metadata': jsonEncode(metadata ?? {}),
        'status': SyncQueueStatus.pending.name,
        'attempts': 0,
        'created_at': now,
        'updated_at': now,
      },
    );
    return getById(id);
  }

  Future<SyncQueueEntry?> findByHash(String contentHash) async {
    final db = await _db();
    final rows = await db.query(
      'upload_queue',
      where: 'content_hash = ?',
      whereArgs: [contentHash],
      limit: 1,
    );
    if (rows.isEmpty) {
      return null;
    }
    return SyncQueueEntry.fromMap(rows.first);
  }

  Future<SyncQueueEntry?> getById(int id) async {
    final db = await _db();
    final rows = await db.query(
      'upload_queue',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    if (rows.isEmpty) {
      return null;
    }
    return SyncQueueEntry.fromMap(rows.first);
  }

  Future<List<SyncQueueEntry>> listPending() async {
    final db = await _db();
    final rows = await db.query(
      'upload_queue',
      where: 'status IN (?, ?)',
      whereArgs: [
        SyncQueueStatus.pending.name,
        SyncQueueStatus.failed.name,
      ],
      orderBy: 'created_at ASC',
    );
    return rows.map(SyncQueueEntry.fromMap).toList();
  }

  Future<List<SyncQueueEntry>> listAll({int limit = 100}) async {
    final db = await _db();
    final rows = await db.query(
      'upload_queue',
      orderBy: 'created_at DESC',
      limit: limit,
    );
    return rows.map(SyncQueueEntry.fromMap).toList();
  }

  Future<SyncQueueSummary> summary() async {
    final db = await _db();
    final rows = await db.rawQuery(
      'SELECT status, COUNT(*) as count FROM upload_queue GROUP BY status',
    );
    var pending = 0;
    var uploading = 0;
    var completed = 0;
    var failed = 0;
    for (final row in rows) {
      final status = _statusFromString(row['status'] as String);
      final count = row['count'] as int? ?? 0;
      switch (status) {
        case SyncQueueStatus.pending:
          pending = count;
        case SyncQueueStatus.uploading:
          uploading = count;
        case SyncQueueStatus.completed:
          completed = count;
        case SyncQueueStatus.failed:
          failed = count;
      }
    }
    return SyncQueueSummary(
      pending: pending,
      uploading: uploading,
      completed: completed,
      failed: failed,
    );
  }

  Future<void> markUploading(int id) async {
    await _updateStatus(id, SyncQueueStatus.uploading);
  }

  Future<void> markCompleted(int id) async {
    await _updateStatus(id, SyncQueueStatus.completed);
  }

  Future<void> markFailed(int id, String error) async {
    final db = await _db();
    final attempts = Sqflite.firstIntValue(
          await db.rawQuery(
            'SELECT attempts FROM upload_queue WHERE id = ?',
            [id],
          ),
        ) ??
        0;
    await db.update(
      'upload_queue',
      {
        'status': SyncQueueStatus.failed.name,
        'last_error': error,
        'attempts': attempts + 1,
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> _updateStatus(int id, SyncQueueStatus status) async {
    final db = await _db();
    await db.update(
      'upload_queue',
      {
        'status': status.name,
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> close() async {
    await _database?.close();
    _database = null;
  }
}

SyncQueueStatus _statusFromString(String value) {
  return SyncQueueStatus.values.firstWhere(
    (status) => status.name == value,
    orElse: () => SyncQueueStatus.pending,
  );
}

Map<String, dynamic> _decodeMetadata(String? raw) {
  if (raw == null || raw.isEmpty) {
    return {};
  }
  try {
    final decoded = jsonDecode(raw);
    if (decoded is Map<String, dynamic>) {
      return decoded;
    }
  } catch (_) {}
  return {};
}