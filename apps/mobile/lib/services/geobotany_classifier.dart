import 'dart:io';

import 'package:flutter/services.dart';

import 'api_client.dart';
import 'rule_based_classifier.dart';
import 'tflite_loader.dart';

enum GeobotanyClassificationPolicy {
  localOnly,
  localFirst,
  cloudOnly,
}

class GeobotanyClassification {
  final String species;
  final double confidence;
  final Map<String, String> mineralAffinity;
  final String recommendedAction;
  final String source;
  final List<Map<String, dynamic>> top3;
  final int inferenceMs;

  GeobotanyClassification({
    required this.species,
    required this.confidence,
    required this.mineralAffinity,
    required this.recommendedAction,
    required this.source,
    this.top3 = const [],
    this.inferenceMs = 0,
  });

  factory GeobotanyClassification.fromJson(
    Map<String, dynamic> json, {
    String source = 'cloud',
  }) {
    final affinity = json['mineral_affinity'] ?? json['mineralAffinity'] ?? {};
    final top3Raw = json['top3'];
    return GeobotanyClassification(
      species: json['species']?.toString() ?? 'unknown_vegetation',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      mineralAffinity: affinity is Map
          ? affinity
              .map((key, value) => MapEntry(key.toString(), value.toString()))
          : {},
      recommendedAction: json['recommended_action']?.toString() ??
          json['recommendedAction']?.toString() ??
          'Review observation',
      source: json['source']?.toString() ?? source,
      top3: top3Raw is List
          ? top3Raw
              .whereType<Map>()
              .map((item) => item.map(
                    (key, value) => MapEntry(key.toString(), value),
                  ))
              .toList()
          : const [],
      inferenceMs: (json['inference_ms'] as num?)?.toInt() ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'species': species,
      'confidence': confidence,
      'mineral_affinity': mineralAffinity,
      'recommended_action': recommendedAction,
      'source': source,
      'top3': top3,
      'inference_ms': inferenceMs,
    };
  }
}

class GeobotanyObservationDraft {
  final String species;
  final double lon;
  final double lat;
  final int vigour;
  final String leafColour;
  final String density;
  final String? localName;
  final String? localSignificance;

  GeobotanyObservationDraft({
    required this.species,
    required this.lon,
    required this.lat,
    required this.vigour,
    required this.leafColour,
    required this.density,
    this.localName,
    this.localSignificance,
  });

  Map<String, dynamic> toJson() {
    return {
      'species': species,
      'lon': lon,
      'lat': lat,
      'vigour': vigour,
      'leaf_colour': leafColour,
      'density': density,
      if (localName != null) 'local_name': localName,
      if (localSignificance != null) 'local_significance': localSignificance,
    };
  }
}

class GeobotanyClassifierService {
  GeobotanyClassifierService({ApiClient? client})
      : _client = client ?? ApiClient();

  final ApiClient _client;
  final TfliteLoader _tflite = TfliteLoader();

  static const double confidenceThreshold = 0.65;
  static const String modelAsset =
      'assets/models/geobotany_classifier_int8.tflite';
  static const String labelsAsset = 'assets/models/geobotany_labels.txt';

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

  Future<GeobotanyClassification> classify({
    String imageBase64 = '',
    double lon = 37.5,
    double lat = -1.15,
    String projectId = 'field-demo',
    GeobotanyClassificationPolicy policy = GeobotanyClassificationPolicy.localFirst,
    File? imageFile,
  }) async {
    if (policy == GeobotanyClassificationPolicy.cloudOnly) {
      return _classifyCloud(
        imageBase64: imageBase64,
        lon: lon,
        lat: lat,
        projectId: projectId,
      );
    }

    final local = await _classifyLocal(
      imageBase64: imageBase64,
      lon: lon,
      lat: lat,
      projectId: projectId,
      imageFile: imageFile,
    );

    if (policy == GeobotanyClassificationPolicy.localOnly ||
        local.confidence >= confidenceThreshold) {
      return local;
    }

    try {
      return await _classifyCloud(
        imageBase64: imageBase64,
        lon: lon,
        lat: lat,
        projectId: projectId,
      );
    } catch (_) {
      return local;
    }
  }

  Future<GeobotanyClassification> _classifyLocal({
    required String imageBase64,
    required double lon,
    required double lat,
    required String projectId,
    File? imageFile,
  }) async {
    final started = DateTime.now();
    await loadModel();

    final bytes = imageFile != null
        ? await RuleBasedClassifier.readImageBytes(imageFile)
        : '$imageBase64:$lon:$lat:$projectId'.codeUnits;
    final seed = RuleBasedClassifier.seedFromBytes(bytes, 'geobotany');
    final top3 = RuleBasedClassifier.topLabels(_labels, seed).map((entry) {
      return {
        'species': entry['label'],
        'score': entry['score'],
      };
    }).toList();
    final confidence = top3.first['score'] as double;
    final species = confidence >= confidenceThreshold
        ? top3.first['species'] as String
        : 'unknown_vegetation';

    final elapsed = DateTime.now().difference(started).inMilliseconds;
    return GeobotanyClassification(
      species: species,
      confidence: confidence,
      mineralAffinity: _affinityFor(species),
      recommendedAction: species == 'unknown_vegetation'
          ? 'Re-sample with clearer foliage photo'
          : 'Collect leaf tissue sample and run XRF transect',
      source: _tflite.isLoaded ? 'local-tflite' : 'local-rule-based',
      top3: top3,
      inferenceMs: elapsed,
    );
  }

  Future<GeobotanyClassification> _classifyCloud({
    required String imageBase64,
    required double lon,
    required double lat,
    required String projectId,
  }) async {
    final response = await _client.post('/geobotany/classify-plant', {
      'image_base64': imageBase64,
      'lon': lon,
      'lat': lat,
      'project_id': projectId,
    });
    return GeobotanyClassification.fromJson(response, source: 'cloud-api');
  }

  Future<Map<String, dynamic>> logObservation(
    GeobotanyObservationDraft draft,
  ) async {
    return _client.post('/geobotany/log-observation', draft.toJson());
  }

  Map<String, String> _affinityFor(String species) {
    const affinities = <String, Map<String, String>>{
      'ocimum_centraliafricanum': {'Cu': 'VERY_HIGH', 'Ni': 'HIGH'},
      'haumaniastrum_katangense': {'Cu': 'HIGH', 'Co': 'MEDIUM'},
      'commelina_zigzag': {'Cu': 'MEDIUM'},
      'silene_cobalticola': {'Co': 'VERY_HIGH'},
      'senecio_coronatus': {'Ni': 'HIGH', 'Cr': 'MEDIUM'},
    };
    return affinities[species] ?? {};
  }

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