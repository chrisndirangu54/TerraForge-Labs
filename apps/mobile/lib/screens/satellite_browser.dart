import 'package:flutter/material.dart';

import '../services/terraforge_api.dart';
import '../widgets/results/structured_json_view.dart';
import '../widgets/satellite/satellite_scene_list.dart';

class SatelliteBrowserScreen extends StatefulWidget {
  const SatelliteBrowserScreen({super.key});

  @override
  State<SatelliteBrowserScreen> createState() => _SatelliteBrowserScreenState();
}

class _SatelliteBrowserScreenState extends State<SatelliteBrowserScreen> {
  final TerraforgeApi _api = TerraforgeApi();

  bool _loading = true;
  bool _insarLoading = false;
  String? _error;
  Map<String, dynamic>? _catalogue;
  List<dynamic> _scenes = [];
  List<dynamic> _indices = [];
  String _selectedIndex = 'ndvi';
  Map<String, dynamic>? _latest;
  Map<String, dynamic>? _insar;

  @override
  void initState() {
    super.initState();
    _loadScenes();
  }

  Future<void> _loadScenes() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final scenes = await _api.satelliteScenes();
      setState(() {
        _catalogue = scenes;
        _scenes = scenes['scenes'] as List? ?? [];
        _indices = scenes['indices_available'] as List? ?? [];
        if (_indices.isNotEmpty) {
          _selectedIndex = '${_indices.first}';
        }
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _loadLatest() async {
    try {
      final latest = await _api.satelliteLatest(index: _selectedIndex);
      setState(() => _latest = latest);
    } catch (error) {
      setState(() => _error = error.toString());
    }
  }

  Future<void> _runInsar() async {
    setState(() {
      _insarLoading = true;
      _error = null;
    });
    try {
      final insar = await _api.satelliteInsar();
      setState(() {
        _insar = insar;
        _insarLoading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _insarLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final stats = _latest?['statistics'] as Map?;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Satellite Browser'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loading ? null : _loadScenes,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Text(
                  'Sentinel-2, SAR, and thermal scenes with spectral indices and InSAR.',
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                ],
                const SizedBox(height: 16),
                if (_indices.isNotEmpty) ...[
                  DropdownButtonFormField<String>(
                    key: ValueKey(_selectedIndex),
                    initialValue: _selectedIndex,
                    decoration: const InputDecoration(
                      labelText: 'Spectral index',
                      border: OutlineInputBorder(),
                    ),
                    items: _indices
                        .map(
                          (idx) => DropdownMenuItem(
                            value: '$idx',
                            child: Text('$idx'),
                          ),
                        )
                        .toList(),
                    onChanged: (value) {
                      if (value != null) setState(() => _selectedIndex = value);
                    },
                  ),
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                    onPressed: _loadLatest,
                    icon: const Icon(Icons.satellite_alt),
                    label: Text('Load latest $_selectedIndex'),
                  ),
                  if (stats != null) ...[
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      children: [
                        Chip(label: Text('min: ${stats['min']}')),
                        Chip(label: Text('mean: ${stats['mean']}')),
                        Chip(label: Text('max: ${stats['max']}')),
                      ],
                    ),
                  ],
                  const SizedBox(height: 16),
                ],
                SatelliteSceneList(scenes: _scenes, indices: _indices),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: _insarLoading ? null : _runInsar,
                  icon: _insarLoading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.waves),
                  label: Text(_insarLoading ? 'Running InSAR...' : 'Run InSAR'),
                ),
                if (_insar != null) ...[
                  const SizedBox(height: 12),
                  SatelliteInsarPanel(insar: _insar!),
                ],
                if (_latest != null) ...[
                  const SizedBox(height: 16),
                  StructuredJsonView(data: _latest, title: 'Latest index'),
                ],
                if (_catalogue != null) ...[
                  const SizedBox(height: 16),
                  StructuredJsonView(data: _catalogue, title: 'Scene catalogue'),
                ],
              ],
            ),
    );
  }
}