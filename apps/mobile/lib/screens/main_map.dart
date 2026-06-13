import 'package:flutter/material.dart';

import '../services/map_service.dart';
import '../services/terraforge_api.dart';
import '../widgets/map/map_canvas.dart';
import '../widgets/results/structured_json_view.dart';

class MainMapScreen extends StatefulWidget {
  const MainMapScreen({super.key});

  @override
  State<MainMapScreen> createState() => _MainMapScreenState();
}

class _MainMapScreenState extends State<MainMapScreen> {
  final MapService _mapService = MapService();
  final TerraforgeApi _api = TerraforgeApi();

  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _layers;
  Map<String, dynamic>? _featureLayers;
  List<Map<String, dynamic>> _points = [];
  String _mapMode = '2d_satellite';
  final Set<String> _activeLayers = {};

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final layers = await _mapService.fetchLayers();
      final boreholes = await _api.boreholes();
      final holes = boreholes['boreholes'];
      final points = <Map<String, dynamic>>[];
      if (holes is List) {
        for (final hole in holes.whereType<Map>()) {
          final lon = hole['lon'];
          final lat = hole['lat'];
          if (lon != null && lat != null) {
            points.add(Map<String, dynamic>.from(hole));
          }
        }
      }

      final modes = layers['map_modes'];
      final featureLayers = layers['feature_layers'];

      setState(() {
        _layers = layers;
        _featureLayers = featureLayers is Map
            ? Map<String, dynamic>.from(featureLayers)
            : null;
        _points = points;
        if (modes is List && modes.isNotEmpty) {
          _mapMode = '${modes.first}';
        }
        _activeLayers
          ..clear()
          ..addAll(_defaultLayers(layers));
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Iterable<String> _defaultLayers(Map<String, dynamic> layers) sync* {
    final featureLayers = layers['feature_layers'];
    if (featureLayers is Map) {
      for (final layerId in featureLayers.keys) {
        yield '$layerId';
      }
      return;
    }
    final groups = layers['layer_groups'];
    if (groups is Map) {
      for (final entry in groups.entries) {
        final groupLayers = entry.value;
        if (groupLayers is List && groupLayers.isNotEmpty) {
          yield '${entry.key}:${groupLayers.first}';
        }
      }
    }
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  Widget build(BuildContext context) {
    final layerGroups = _layers?['layer_groups'];
    final mapModes = _layers?['map_modes'] as List? ?? [];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Main Map'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loading ? null : _load,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Text(
                  'Mission map with layer catalogue and borehole overlay.',
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                ],
                const SizedBox(height: 12),
                if (mapModes.isNotEmpty)
                  DropdownButtonFormField<String>(
                    key: ValueKey(_mapMode),
                    initialValue: _mapMode,
                    decoration: const InputDecoration(
                      labelText: 'Map mode',
                      border: OutlineInputBorder(),
                    ),
                    items: mapModes
                        .map(
                          (mode) => DropdownMenuItem(
                            value: '$mode',
                            child: Text('$mode'.replaceAll('_', ' ')),
                          ),
                        )
                        .toList(),
                    onChanged: (value) {
                      if (value != null) setState(() => _mapMode = value);
                    },
                  ),
                const SizedBox(height: 16),
                MapCanvas(
                  points: _points,
                  activeLayers: _activeLayers.toList(),
                  featureLayers: _featureLayers,
                ),
                const SizedBox(height: 16),
                Text('Layers', style: Theme.of(context).textTheme.titleSmall),
                if (layerGroups is Map)
                  ...layerGroups.entries.map((entry) {
                    final groupLayers = entry.value;
                    return ExpansionTile(
                      title: Text('${entry.key}'.replaceAll('_', ' ')),
                      initiallyExpanded: entry.key == 'geological',
                      children: [
                        if (groupLayers is List)
                          ...groupLayers.map((layer) {
                            final layerId = '${entry.key}:$layer';
                            final hasData = _featureLayers?.containsKey(layerId) ?? false;
                            return SwitchListTile(
                              dense: true,
                              title: Text('$layer'.replaceAll('_', ' ')),
                              subtitle: hasData ? null : const Text('No data yet'),
                              value: _activeLayers.contains(layerId),
                              onChanged: hasData
                                  ? (enabled) {
                                      setState(() {
                                        if (enabled == true) {
                                          _activeLayers.add(layerId);
                                        } else {
                                          _activeLayers.remove(layerId);
                                        }
                                      });
                                    }
                                  : null,
                            );
                          }),
                      ],
                    );
                  }),
                if (_layers != null) ...[
                  const SizedBox(height: 16),
                  StructuredJsonView(data: _layers, title: 'Map catalogue'),
                ],
              ],
            ),
    );
  }
}