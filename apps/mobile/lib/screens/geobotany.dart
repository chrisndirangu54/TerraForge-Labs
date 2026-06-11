import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/geobotany_classifier.dart';

class GeobotanyScreen extends StatefulWidget {
  const GeobotanyScreen({super.key});

  @override
  State<GeobotanyScreen> createState() => _GeobotanyScreenState();
}

class _GeobotanyScreenState extends State<GeobotanyScreen> {
  final GeobotanyClassifierService _service = GeobotanyClassifierService();
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;

  Future<void> _classify() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final classification = await _service.classify();
      setState(() {
        _result = {
          'species': classification.species,
          'confidence': classification.confidence,
          'mineral_affinity': classification.mineralAffinity,
          'recommended_action': classification.recommendedAction,
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
            'Classify indicator plants and log field observations through the backend API.',
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _classify,
            child: const Text('Classify Plant'),
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
              const JsonEncoder.withIndent('  ').convert(_result),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }
}
