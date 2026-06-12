import 'package:flutter/material.dart';

import '../services/project_store.dart';
import '../services/terraforge_api.dart';
import '../widgets/capture/capture_result_view.dart';

class _PlatformFeature {
  final String id;
  final String title;
  final String description;
  final bool isGet;
  final String path;
  final Map<String, dynamic> body;

  const _PlatformFeature({
    required this.id,
    required this.title,
    required this.description,
    required this.path,
    this.isGet = false,
    this.body = const {},
  });
}

const _features = [
  _PlatformFeature(
    id: 'fusion',
    title: 'Fusion v2',
    description: 'Multi-source score + attribution',
    path: '/fusion/v2',
    body: {
      'sources': {'kriging_grade': 85, 'geobotany': 72, 'aeromag_structure': 60},
    },
  ),
  _PlatformFeature(
    id: 'qaqc',
    title: 'Assay QA/QC',
    description: 'Standards/blanks → kriging gate',
    path: '/geochem/qaqc-pipeline',
    body: {
      'samples': [
        {'sample_type': 'standard', 'expected_ppm': 100, 'measured_ppm': 102},
      ],
    },
  ),
  _PlatformFeature(
    id: 'uav',
    title: 'UAV survey',
    description: 'Orthomosaic + DSM',
    path: '/uav/survey',
    body: {'flight_id': 'uav-01'},
  ),
  _PlatformFeature(
    id: 'twin',
    title: 'Live NPV twin',
    description: 'Price–grade–recovery band',
    path: '/digital-twin/live-npv',
    body: {'commodity': 'ta', 'ore_tonnes': 3000000, 'price_shock_pct': -8},
  ),
  _PlatformFeature(
    id: 'climate',
    title: 'Climate-risk NPV',
    description: 'Water/flood/energy scenarios',
    path: '/climate-risk/npv',
    body: {'commodity': 'ta', 'ore_tonnes': 2500000, 'water_stress_index': 0.4},
  ),
  _PlatformFeature(
    id: 'lineage',
    title: 'Lineage list',
    description: 'Artifact provenance records',
    path: '/lineage/list',
    isGet: true,
  ),
  _PlatformFeature(
    id: 'checkout',
    title: 'Marketplace checkout',
    description: 'M-Pesa / Stripe scaffold',
    path: '/marketplace/checkout',
    body: {'amount_usd': 149, 'provider': 'mpesa'},
  ),
];

class PlatformHubScreen extends StatefulWidget {
  const PlatformHubScreen({super.key});

  @override
  State<PlatformHubScreen> createState() => _PlatformHubScreenState();
}

class _PlatformHubScreenState extends State<PlatformHubScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  final Map<String, Map<String, dynamic>> _results = {};
  final Map<String, String> _errors = {};
  String? _loadingId;

  Future<void> _run(_PlatformFeature feature) async {
    setState(() {
      _loadingId = feature.id;
      _errors.remove(feature.id);
    });
    try {
      final data = feature.isGet
          ? await _api.platformGet(feature.path)
          : await _api.platformPost(feature.path, feature.body);
      setState(() {
        _results[feature.id] = data;
        _loadingId = null;
      });
    } catch (error) {
      setState(() {
        _errors[feature.id] = error.toString();
        _loadingId = null;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final projectId = ProjectStore.instance.selectedProjectId;

    return Scaffold(
      appBar: AppBar(title: const Text('Platform Hub')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Active project: $projectId'),
          const SizedBox(height: 16),
          ..._features.map((feature) {
            final loading = _loadingId == feature.id;
            final result = _results[feature.id];
            final error = _errors[feature.id];
            return Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(feature.title, style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 4),
                    Text(feature.description),
                    const SizedBox(height: 8),
                    ElevatedButton(
                      onPressed: loading ? null : () => _run(feature),
                      child: Text(loading ? 'Running...' : 'Run pipeline'),
                    ),
                    if (error != null) ...[
                      const SizedBox(height: 8),
                      Text(error, style: const TextStyle(color: Colors.red, fontSize: 11)),
                    ],
                    if (result != null) ...[
                      const SizedBox(height: 8),
                      _PipelineResultCard(result: result),
                    ],
                  ],
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}

class _PipelineResultCard extends StatelessWidget {
  final Map<String, dynamic> result;

  const _PipelineResultCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final display = result['display'];
    if (display is Map) {
      return CaptureResultView(
        display: Map<String, dynamic>.from(display),
        fallback: result,
      );
    }

    final highlights = <String, dynamic>{};
    for (final key in [
      'fusion_score', 'npv_usd', 'status', 'checkout_id', 'lineage_count',
      'records', 'score', 'recommendation',
    ]) {
      if (result[key] != null) highlights[key] = result[key];
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (highlights.isNotEmpty)
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: highlights.entries
                .map(
                  (entry) => Chip(
                    label: Text('${entry.key}: ${entry.value}',
                        style: const TextStyle(fontSize: 11)),
                  ),
                )
                .toList(),
          ),
        CaptureResultView(fallback: result),
      ],
    );
  }
}