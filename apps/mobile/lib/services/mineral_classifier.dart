import 'dart:io';
import 'dart:math' as math;

import 'package:flutter/services.dart';

import 'rule_based_classifier.dart';
import 'tflite_loader.dart';

class MineralClassification {
  final String label;
  final double confidence;
  final List<Map<String, dynamic>> top3;
  final String accelerator;
  final int inferenceMs;

  MineralClassification({
    required this.label,
    required this.confidence,
    required this.top3,
    required this.accelerator,
    required this.inferenceMs,
  });
}

class MineralClassifierService {
  static const double confidenceThreshold = 0.70;
  static const int targetInferenceMs = 500;
  static const String modelAsset =
      'assets/models/mineral_classifier_int8.tflite';
  static const String labelsAsset = 'assets/models/mineral_labels.txt';

  final TfliteLoader _tflite = TfliteLoader();
  List<String> _labels = [];
  bool _modelReady = false;

  Future<void> loadModel() async {
    if (_modelReady) {
      return;
    }
    _labels = await _loadLabels();
    await _tflite.load(modelAsset);
    _modelReady = true;
  }

  Future<MineralClassification> classify(File imageFile) async {
    final started = DateTime.now();
    await loadModel();

    MineralClassification result;
    if (_tflite.isLoaded) {
      result = await _classifyWithTflite(imageFile);
    } else {
      result = await _classifyRuleBased(imageFile);
    }

    final elapsed = DateTime.now().difference(started).inMilliseconds;
    return MineralClassification(
      label: result.label,
      confidence: result.confidence,
      top3: result.top3,
      accelerator: result.accelerator,
      inferenceMs: elapsed,
    );
  }

  Future<MineralClassification> _classifyWithTflite(File imageFile) async {
    final bytes = await RuleBasedClassifier.readImageBytes(imageFile);
    final input = List<double>.generate(
      224 * 224 * 3,
      (index) => (bytes[index % bytes.length] / 255.0),
    );
    final logits = _tflite.predict(input, outputSize: _labels.length);
    if (logits.isEmpty) {
      return _classifyRuleBased(imageFile);
    }

    final ranked = _rankLabels(logits);
    final primary = ranked.first;
    final label = (primary['score'] as double) >= confidenceThreshold
        ? primary['label'] as String
        : 'unknown';
    return MineralClassification(
      label: label,
      confidence: primary['score'] as double,
      top3: ranked,
      accelerator: 'on-device-tflite',
      inferenceMs: 0,
    );
  }

  Future<MineralClassification> _classifyRuleBased(File imageFile) async {
    final bytes = await RuleBasedClassifier.readImageBytes(imageFile);
    final seed = RuleBasedClassifier.seedFromBytes(bytes, 'mineral');
    final top3 = RuleBasedClassifier.topLabels(_labels, seed);
    final primaryScore = top3.first['score'] as double;
    final label = primaryScore >= confidenceThreshold
        ? top3.first['label'] as String
        : 'unknown';

    return MineralClassification(
      label: label,
      confidence: primaryScore,
      top3: top3,
      accelerator: 'rule-based-labels',
      inferenceMs: 0,
    );
  }

  List<Map<String, dynamic>> _rankLabels(List<double> logits) {
    final pairs = <MapEntry<String, double>>[];
    for (var i = 0; i < logits.length && i < _labels.length; i++) {
      pairs.add(MapEntry(_labels[i], logits[i]));
    }
    pairs.sort((a, b) => b.value.compareTo(a.value));
    final maxLogit = pairs.isEmpty ? 1.0 : pairs.first.value;
    final expSum = pairs.fold<double>(
      0,
      (sum, entry) => sum + _exp(entry.value - maxLogit),
    );
    return pairs.take(3).map((entry) {
      final score = _exp(entry.value - maxLogit) / (expSum == 0 ? 1 : expSum);
      return {
        'label': entry.key,
        'score': double.parse(score.toStringAsFixed(4)),
      };
    }).toList();
  }

  double _exp(double value) => math.exp(value);

  Future<List<String>> _loadLabels() async {
    final raw = await rootBundle.loadString(labelsAsset);
    return raw
        .split('\n')
        .map((line) => line.trim())
        .where((line) => line.isNotEmpty)
        .toList();
  }

  void dispose() {
    _tflite.dispose();
    _modelReady = false;
  }
}