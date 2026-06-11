import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

import '../services/mineral_classifier.dart';

class ClassifyMineralScreen extends StatefulWidget {
  const ClassifyMineralScreen({super.key});

  @override
  State<ClassifyMineralScreen> createState() => _ClassifyMineralScreenState();
}

class _ClassifyMineralScreenState extends State<ClassifyMineralScreen> {
  final MineralClassifierService _classifier = MineralClassifierService();
  bool _loading = false;
  MineralClassification? _result;

  Future<void> _classify() async {
    setState(() => _loading = true);
    final result = await _classifier.classify(File('demo_mineral.jpg'));
    setState(() {
      _result = result;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Classify Mineral')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'On-device mineral classification (local model stub). Upload flows use the instrument API.',
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _classify,
            child: Text(_loading ? 'Classifying...' : 'Run Local Classifier'),
          ),
          if (_result != null) ...[
            const SizedBox(height: 16),
            SelectableText(
              JsonEncoder.withIndent('  ').convert({
                'label': _result!.label,
                'confidence': _result!.confidence,
                'top3': _result!.top3,
              }),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }
}
