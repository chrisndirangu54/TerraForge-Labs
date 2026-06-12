import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

import '../services/cloud_classification_service.dart';
import '../services/mineral_classifier.dart';

class ClassifyMineralScreen extends StatefulWidget {
  const ClassifyMineralScreen({super.key});

  @override
  State<ClassifyMineralScreen> createState() => _ClassifyMineralScreenState();
}

class _ClassifyMineralScreenState extends State<ClassifyMineralScreen> {
  final MineralClassifierService _classifier = MineralClassifierService();
  final CloudClassificationService _cloud = CloudClassificationService();
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _localResult;
  Map<String, dynamic>? _cloudResult;

  Future<void> _classifyLocal() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    final result = await _classifier.classify(File('demo_mineral.jpg'));
    setState(() {
      _localResult = {
        'label': result.label,
        'confidence': result.confidence,
        'top3': result.top3,
        'accelerator': 'on-device-tflite',
      };
      _loading = false;
    });
  }

  Future<void> _classifyCloud() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await _cloud.classifySync(task: 'mineral');
      setState(() {
        _cloudResult = response['result'] as Map<String, dynamic>? ?? response;
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
      appBar: AppBar(title: const Text('Classify Mineral')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Use on-device TFLite for offline field work, or cloud GPU for higher accuracy.',
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _classifyLocal,
            child: Text(_loading ? 'Classifying...' : 'Run Local Classifier'),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: _loading ? null : _classifyCloud,
            child: const Text('Run Cloud GPU Classifier'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_localResult != null) ...[
            const SizedBox(height: 16),
            const Text('Local result', style: TextStyle(fontWeight: FontWeight.bold)),
            SelectableText(
              JsonEncoder.withIndent('  ').convert(_localResult),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
          if (_cloudResult != null) ...[
            const SizedBox(height: 16),
            const Text('Cloud GPU result', style: TextStyle(fontWeight: FontWeight.bold)),
            SelectableText(
              JsonEncoder.withIndent('  ').convert(_cloudResult),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }
}