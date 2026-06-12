import 'package:flutter/material.dart';

import '../services/capture_sync_service.dart';
import '../services/map_service.dart';
import '../widgets/capture/capture_result_view.dart';

class OfflineManagerScreen extends StatefulWidget {
  const OfflineManagerScreen({super.key});

  @override
  State<OfflineManagerScreen> createState() => _OfflineManagerScreenState();
}

class _OfflineManagerScreenState extends State<OfflineManagerScreen> {
  final CaptureSyncService _sync = CaptureSyncService();
  final MapService _mapService = MapService();
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _packResult;

  Future<void> _loadPack() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final pack = await _mapService.fetchOfflinePack('kenya');
      setState(() {
        _packResult = pack;
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
    setState(() => _loading = true);
    try {
      final count = await _sync.flushPending();
      setState(() => _loading = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Synced $count queued capture(s)')),
      );
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
      appBar: AppBar(title: const Text('Offline Packs')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Manage offline map packs and queued field captures waiting for connectivity.',
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _loadPack,
            child: const Text('Load Kenya Offline Pack'),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: _loading ? null : _flushQueue,
            child: const Text('Sync Queued Captures'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_packResult != null) ...[
            const SizedBox(height: 16),
            Text('Offline pack', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            if (_packResult!['name'] != null || _packResult!['region'] != null)
              Card(
                child: ListTile(
                  leading: const Icon(Icons.map_outlined),
                  title: Text('${_packResult!['name'] ?? _packResult!['region']}'),
                  subtitle: Text(
                    'Tiles: ${_packResult!['tile_count'] ?? 'n/a'} · '
                    'Size: ${_packResult!['size_mb'] ?? 'n/a'} MB',
                  ),
                ),
              ),
            CaptureResultView(fallback: _packResult),
          ],
        ],
      ),
    );
  }
}