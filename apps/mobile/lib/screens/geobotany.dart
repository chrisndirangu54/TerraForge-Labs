import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/cloud_classification_service.dart';
import '../services/geobotany_classifier.dart';

class GeobotanyScreen extends StatefulWidget {
  const GeobotanyScreen({super.key});

  @override
  State<GeobotanyScreen> createState() => _GeobotanyScreenState();
}

class _GeobotanyScreenState extends State<GeobotanyScreen> {
  final GeobotanyClassifierService _service = GeobotanyClassifierService();
  final CloudClassificationService _cloud = CloudClassificationService();
  GeobotanyClassificationPolicy _policy =
      GeobotanyClassificationPolicy.localFirst;
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;

  @override
  void initState() {
    super.initState();
    _service.loadModel();
  }

  @override
  void dispose() {
    _service.dispose();
    super.dispose();
  }

  Future<void> _classify() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final classification = await _service.classify(policy: _policy);
      setState(() {
        _result = classification.toJson()
          ..['policy'] = _policy.name
          ..['cloud_fallback_threshold'] =
              GeobotanyClassifierService.confidenceThreshold;
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _classifyCloud() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await _cloud.classifySync(task: 'geobotany');
      setState(() {
        _result = response['result'] as Map<String, dynamic>? ?? response;
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _logObservation() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await _service.logObservation(
        GeobotanyObservationDraft(
          species: 'ocimum_centraliafricanum',
          lon: 37.5,
          lat: -1.15,
          vigour: 4,
          leafColour: 'green',
          density: 'moderate',
          localName: 'demo-plant',
        ),
      );
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
      appBar: AppBar(title: const Text('Geobotany & Biogeochemistry')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Classify indicator plants locally with TFLite, falling back to cloud '
            'when confidence is below 0.65.',
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<GeobotanyClassificationPolicy>(
            initialValue: _policy,
            decoration: const InputDecoration(
              labelText: 'Classification policy',
            ),
            items: const [
              DropdownMenuItem(
                value: GeobotanyClassificationPolicy.localOnly,
                child: Text('Local only'),
              ),
              DropdownMenuItem(
                value: GeobotanyClassificationPolicy.localFirst,
                child: Text('Local first (cloud fallback <0.65)'),
              ),
              DropdownMenuItem(
                value: GeobotanyClassificationPolicy.cloudOnly,
                child: Text('Cloud only'),
              ),
            ],
            onChanged: _loading
                ? null
                : (value) {
                    if (value != null) {
                      setState(() => _policy = value);
                    }
                  },
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _classify,
            child: Text(_loading ? 'Classifying...' : 'Classify Plant'),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: _loading ? null : _classifyCloud,
            child: const Text('Classify Plant (Cloud GPU)'),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: _loading ? null : _logObservation,
            child: const Text('Log Observation'),
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