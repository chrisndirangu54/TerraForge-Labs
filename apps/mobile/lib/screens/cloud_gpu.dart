import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/cloud_classification_service.dart';

class CloudGpuScreen extends StatefulWidget {
  const CloudGpuScreen({super.key});

  @override
  State<CloudGpuScreen> createState() => _CloudGpuScreenState();
}

class _CloudGpuScreenState extends State<CloudGpuScreen> {
  final CloudClassificationService _service = CloudClassificationService();
  String _task = 'mineral';
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _capabilities;
  Map<String, dynamic>? _result;

  @override
  void initState() {
    super.initState();
    _loadCapabilities();
  }

  Future<void> _loadCapabilities() async {
    try {
      final capabilities = await _service.capabilities();
      setState(() => _capabilities = capabilities);
    } catch (error) {
      setState(() => _error = error.toString());
    }
  }

  Future<void> _run({required bool async}) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = async
          ? await _service.classifyAsync(task: _task)
          : await _service.classifySync(task: _task);
      setState(() {
        _result = response;
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
      appBar: AppBar(title: const Text('Cloud GPU Classification')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'High-accuracy GPU-accelerated classification in the cloud. '
            'Uses CUDA + mixed precision when a GPU worker is available.',
          ),
          if (_capabilities != null) ...[
            const SizedBox(height: 12),
            SelectableText(
              JsonEncoder.withIndent('  ').convert(_capabilities),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            initialValue: _task,
            decoration: const InputDecoration(labelText: 'Task'),
            items: const [
              DropdownMenuItem(value: 'mineral', child: Text('Mineral')),
              DropdownMenuItem(value: 'geobotany', child: Text('Geobotany')),
              DropdownMenuItem(
                value: 'thin_section',
                child: Text('Thin section'),
              ),
              DropdownMenuItem(value: 'spectral', child: Text('Spectral')),
              DropdownMenuItem(
                value: 'grain_segmentation',
                child: Text('Grain segmentation'),
              ),
            ],
            onChanged: _loading
                ? null
                : (value) {
                    if (value != null) setState(() => _task = value);
                  },
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : () => _run(async: false),
            child: Text(_loading ? 'Running...' : 'Run Sync GPU Classify'),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: _loading ? null : () => _run(async: true),
            child: const Text('Run Async GPU Job'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_result != null) ...[
            const SizedBox(height: 16),
            SelectableText(
              JsonEncoder.withIndent('  ').convert(_result),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }
}
