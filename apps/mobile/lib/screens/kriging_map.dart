import 'package:flutter/material.dart';

import '../config/api_config.dart';
import '../services/job_poller.dart';
import '../services/project_store.dart';
import '../services/terraforge_api.dart';
import '../widgets/geology/kriging_heatmap_view.dart';
import '../widgets/results/job_status_panel.dart';
import '../widgets/results/structured_json_view.dart';

const _variogramModels = ['spherical', 'exponential', 'gaussian', 'linear'];

class KrigingMapScreen extends StatefulWidget {
  const KrigingMapScreen({super.key});

  @override
  State<KrigingMapScreen> createState() => _KrigingMapScreenState();
}

class _KrigingMapScreenState extends State<KrigingMapScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  final JobPollerService _poller = JobPollerService();
  final _elementController = TextEditingController(text: 'ta_ppm');
  final _gridController = TextEditingController(text: '50');

  String _variogramModel = 'spherical';
  bool _running = false;
  bool _cvLoading = false;
  String? _error;
  Map<String, dynamic>? _job;
  Map<String, dynamic>? _variogram;

  @override
  void dispose() {
    _elementController.dispose();
    _gridController.dispose();
    super.dispose();
  }

  Future<void> _runCrossValidation() async {
    setState(() {
      _cvLoading = true;
      _error = null;
    });
    try {
      final result = await _api.variogramCrossValidate(
        element: _elementController.text.trim(),
        variogramModel: _variogramModel,
        projectId: ProjectStore.instance.selectedProjectId,
      );
      setState(() {
        _variogram = result;
        _cvLoading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _cvLoading = false;
      });
    }
  }

  Future<void> _runKriging() async {
    setState(() {
      _running = true;
      _error = null;
      _job = null;
    });
    try {
      final started = await _api.runKriging(
        element: _elementController.text.trim(),
        variogramModel: _variogramModel,
        gridResolutionM: int.tryParse(_gridController.text.trim()) ?? 50,
        projectId: ProjectStore.instance.selectedProjectId,
      );
      final jobId = started['job_id']?.toString();
      final job = jobId != null ? await _poller.poll(jobId) : started;
      setState(() {
        _job = job;
        _running = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _running = false;
      });
    }
  }

  String? _previewUrl() {
    final result = _job?['result'];
    if (result is! Map) return null;
    final url = result['cog_preview_url']?.toString();
    if (url == null || url.isEmpty) return null;
    if (url.startsWith('http')) return url;
    return '${ApiConfig.baseUrl}$url';
  }

  Map<String, dynamic>? _stats() {
    final result = _job?['result'];
    if (result is Map) {
      final stats = result['stats'];
      if (stats is Map) return Map<String, dynamic>.from(stats);
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final cv = _variogram?['cross_validation'] as Map?;

    return Scaffold(
      appBar: AppBar(title: const Text('Kriging Map')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Variogram cross-validation and grade interpolation for the active project.',
          ),
          const SizedBox(height: 16),
          TextField(
            decoration: const InputDecoration(
              labelText: 'Element field',
              border: OutlineInputBorder(),
            ),
            controller: _elementController,
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            key: ValueKey(_variogramModel),
            initialValue: _variogramModel,
            decoration: const InputDecoration(
              labelText: 'Variogram model',
              border: OutlineInputBorder(),
            ),
            items: _variogramModels
                .map((m) => DropdownMenuItem(value: m, child: Text(m)))
                .toList(),
            onChanged: (value) {
              if (value != null) setState(() => _variogramModel = value);
            },
          ),
          const SizedBox(height: 12),
          TextField(
            decoration: const InputDecoration(
              labelText: 'Grid resolution (m)',
              border: OutlineInputBorder(),
            ),
            keyboardType: TextInputType.number,
            controller: _gridController,
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: _cvLoading ? null : _runCrossValidation,
                  child: Text(_cvLoading ? 'Analyzing...' : 'Variogram CV'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: _running ? null : _runKriging,
                  child: Text(_running ? 'Running...' : 'Run kriging'),
                ),
              ),
            ],
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (cv != null) ...[
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              children: [
                Chip(label: Text('RMSE: ${cv['rmse']}')),
                Chip(label: Text('MAE: ${cv['mae']}')),
                Chip(label: Text('Bias: ${cv['bias']}')),
              ],
            ),
          ],
          if (_variogram != null) ...[
            const SizedBox(height: 16),
            StructuredJsonView(data: _variogram, title: 'Variogram analysis'),
          ],
          if (_job != null) ...[
            const SizedBox(height: 16),
            KrigingHeatmapView(
              stats: _stats(),
              previewUrl: _previewUrl(),
            ),
            const SizedBox(height: 12),
            JobStatusPanel(job: _job, title: 'Kriging job'),
          ],
        ],
      ),
    );
  }
}