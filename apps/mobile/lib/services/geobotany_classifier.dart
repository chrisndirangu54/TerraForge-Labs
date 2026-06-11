import 'api_client.dart';

class GeobotanyClassification {
  final String species;
  final double confidence;
  final Map<String, String> mineralAffinity;
  final String recommendedAction;

  GeobotanyClassification({
    required this.species,
    required this.confidence,
    required this.mineralAffinity,
    required this.recommendedAction,
  });

  factory GeobotanyClassification.fromJson(Map<String, dynamic> json) {
    final affinity = json['mineral_affinity'] ?? json['mineralAffinity'] ?? {};
    return GeobotanyClassification(
      species: json['species']?.toString() ?? 'unknown',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      mineralAffinity: affinity is Map
          ? affinity
              .map((key, value) => MapEntry(key.toString(), value.toString()))
          : {},
      recommendedAction: json['recommended_action']?.toString() ??
          json['recommendedAction']?.toString() ??
          'Review observation',
    );
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

  static const double confidenceThreshold = 0.65;
  static const String modelAsset =
      'assets/models/geobotany_classifier_int8.tflite';

  Future<void> loadModel() async {}

  Future<GeobotanyClassification> classify({
    String imageBase64 = '',
    double lon = 37.5,
    double lat = -1.15,
    String projectId = 'field-demo',
  }) async {
    final response = await _client.post('/geobotany/classify-plant', {
      'image_base64': imageBase64,
      'lon': lon,
      'lat': lat,
      'project_id': projectId,
    });
    return GeobotanyClassification.fromJson(response);
  }

  Future<Map<String, dynamic>> logObservation(
    GeobotanyObservationDraft draft,
  ) async {
    return _client.post('/geobotany/log-observation', draft.toJson());
  }
}
