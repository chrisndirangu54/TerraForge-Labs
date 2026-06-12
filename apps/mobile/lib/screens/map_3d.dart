import 'package:flutter/material.dart';

import '../services/job_poller.dart';
import '../services/project_store.dart';
import '../services/terraforge_api.dart';
import '../widgets/geology/deposit_model_viewer.dart';
import '../widgets/results/job_status_panel.dart';
import '../widgets/results/structured_json_view.dart';

class Map3dScreen extends StatefulWidget {
  const Map3dScreen({super.key});

  @override
  State<Map3dScreen> createState() => _Map3dScreenState();
}

class _Map3dScreenState extends State<Map3dScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  final JobPollerService _poller = JobPollerService();

  bool _loading = true;
  bool _generating = false;
  String? _error;
  Map<String, dynamic>? _summary;
  Map<String, dynamic>? _job;

  @override
  void initState() {
    super.initState();
    _loadSummary();
  }

  Future<void> _loadSummary() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final summary = await _api.depositSummary(
        projectId: ProjectStore.instance.selectedProjectId,
      );
      setState(() {
        _summary = summary;
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _generateModel() async {
    setState(() {
      _generating = true;
      _error = null;
    });
    try {
      final started = await _api.generateDepositModel(async: true);
      final jobId = started['job_id']?.toString();
      Map<String, dynamic> job = started;
      if (jobId != null) {
        job = await _poller.poll(jobId);
      }
      final refreshed = await _api.depositSummary(
        projectId: ProjectStore.instance.selectedProjectId,
      );
      setState(() {
        _job = job;
        _summary = refreshed;
        _generating = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _generating = false;
      });
    }
  }

  List<Map<String, dynamic>> _blocks() {
    final raw = _summary?['blocks_preview'];
    if (raw is List) {
      return raw
          .whereType<Map>()
          .map((b) => Map<String, dynamic>.from(b))
          .toList();
    }
    return [];
  }

  @override
  Widget build(BuildContext context) {
    final meanGrade = (_summary?['mean_grade_ta_ppm'] as num?)?.toDouble();
    final centre = _summary?['centre'] as Map?;

    return Scaffold(
      appBar: AppBar(
        title: const Text('3D Deposit Model'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loading ? null : _loadSummary,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(
                  'Isometric block model preview for ${ProjectStore.instance.selectedProjectId}.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                ],
                const SizedBox(height: 16),
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    _StatChip(
                      label: 'Ore tonnes',
                      value: '${_summary?['ore_tonnes_estimate'] ?? 'n/a'}',
                    ),
                    _StatChip(
                      label: 'Mean grade',
                      value: meanGrade != null
                          ? '${meanGrade.toStringAsFixed(1)} ppm Ta'
                          : 'n/a',
                    ),
                    _StatChip(
                      label: 'Blocks',
                      value: '${_summary?['block_count'] ?? _blocks().length}',
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                DepositModelViewer(
                  blocks: _blocks(),
                  meanGrade: meanGrade,
                ),
                if (centre != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Centre: ${centre['lat']}, ${centre['lon']} · ${centre['elevation_m']} m',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: _generating ? null : _generateModel,
                  icon: _generating
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.view_in_ar),
                  label: Text(_generating ? 'Generating...' : 'Generate deposit model'),
                ),
                if (_job != null) ...[
                  const SizedBox(height: 16),
                  JobStatusPanel(job: _job, title: 'Deposit model job'),
                ],
                if (_summary != null) ...[
                  const SizedBox(height: 16),
                  StructuredJsonView(data: _summary, title: 'Deposit summary'),
                ],
              ],
            ),
    );
  }
}

class _StatChip extends StatelessWidget {
  final String label;
  final String value;

  const _StatChip({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Chip(
      label: Text('$label: $value', style: const TextStyle(fontSize: 12)),
    );
  }
}