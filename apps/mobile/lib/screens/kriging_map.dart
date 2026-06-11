import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/job_poller.dart';
import '../services/terraforge_api.dart';

class KrigingMapScreen extends StatefulWidget {
  const KrigingMapScreen({super.key});

  @override
  State<KrigingMapScreen> createState() => _KrigingMapScreenState();
}

class _KrigingMapScreenState extends State<KrigingMapScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  final JobPollerService _poller = JobPollerService();
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;

  Map<String, dynamic> _uncertaintyMetadata(Map<String, dynamic> jobResult) {
    return {
      'mean_layer': jobResult['grid_geotiff_url'],
      'variance_layer': jobResult['variance_geotiff_url'],
      'ci_lower_layer': jobResult['ci_lower_geotiff_url'],
      'ci_upper_layer': jobResult['ci_upper_geotiff_url'],
      'variogram_params': jobResult['variogram_params'],
      'stats': jobResult['stats'],
      'warnings': jobResult['warnings'],
    };
  }

  Future<void> _runKriging() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final started = await _api.runKriging();
      final jobId = started['job_id']?.toString();
      Map<String, dynamic> job = started;
      if (jobId != null && started['status'] != 'complete') {
        job = await _poller.pollUntilComplete(jobId);
      }

      final jobResult = job['result'] as Map<String, dynamic>? ?? job;
      setState(() {
        _result = {
          'job_id': jobId ?? job['job_id'],
          'status': job['status']?.toString() ?? 'complete',
          'uncertainty_layers': _uncertaintyMetadata(jobResult),
        };
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
      appBar: AppBar(title: const Text('Kriging Map')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Run the kriging pipeline against POST /fuse-geodata and display '
            'uncertainty layer metadata from the completed job result.',
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _runKriging,
            child: Text(_loading ? 'Running...' : 'Run Kriging'),
          ),
          if (_result != null) ...[
            const SizedBox(height: 16),
            const Text('Uncertainty layers',
                style: TextStyle(fontWeight: FontWeight.bold)),
            SelectableText(
              JsonEncoder.withIndent('  ').convert(_result),
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