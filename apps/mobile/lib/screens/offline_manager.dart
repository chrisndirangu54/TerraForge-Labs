import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/instrument_upload.dart';
import '../services/map_service.dart';
import '../services/sync_queue.dart';

class OfflineManagerScreen extends StatefulWidget {
  const OfflineManagerScreen({super.key});

  @override
  State<OfflineManagerScreen> createState() => _OfflineManagerScreenState();
}

class _OfflineManagerScreenState extends State<OfflineManagerScreen> {
  final InstrumentUploadService _uploadService = InstrumentUploadService();
  final MapService _mapService = MapService();
  bool _loading = false;
  String? _error;
  SyncQueueSummary? _summary;
  List<SyncQueueEntry> _entries = const [];
  Map<String, dynamic>? _packResult;

  @override
  void initState() {
    super.initState();
    _refreshQueue();
  }

  Future<void> _refreshQueue() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final summary = await _uploadService.queueSummary();
      final entries = await _uploadService.listQueue(limit: 20);
      setState(() {
        _summary = summary;
        _entries = entries;
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _flushQueue() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await _uploadService.flushQueue();
      await _refreshQueue();
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _loadPack() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await _mapService.fetchOfflinePack('kenya');
      setState(() {
        _packResult = result;
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Offline Manager')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Manage offline map packs and inspect the instrument upload sync queue.',
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _loadPack,
            child: Text(_loading ? 'Loading...' : 'Load Kenya Pack'),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: _loading ? null : _refreshQueue,
            child: const Text('Refresh Sync Queue'),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: _loading ? null : _flushQueue,
            child: const Text('Flush Pending Uploads'),
          ),
          if (_summary != null) ...[
            const SizedBox(height: 16),
            const Text('Sync queue status',
                style: TextStyle(fontWeight: FontWeight.bold)),
            Text('Pending: ${_summary!.pending}'),
            Text('Uploading: ${_summary!.uploading}'),
            Text('Completed: ${_summary!.completed}'),
            Text('Failed: ${_summary!.failed}'),
            Text('Total: ${_summary!.total}'),
          ],
          if (_entries.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text('Recent queue entries',
                style: TextStyle(fontWeight: FontWeight.bold)),
            ..._entries.map(
              (entry) => ListTile(
                title: Text('${entry.instrumentType} • ${entry.filename}'),
                subtitle: Text(
                  '${entry.status.name} • hash ${entry.contentHash}',
                ),
              ),
            ),
          ],
          if (_packResult != null) ...[
            const SizedBox(height: 16),
            const Text('Offline pack',
                style: TextStyle(fontWeight: FontWeight.bold)),
            SelectableText(
              JsonEncoder.withIndent('  ').convert(_packResult),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
        ],
      ),
    );
  }
}