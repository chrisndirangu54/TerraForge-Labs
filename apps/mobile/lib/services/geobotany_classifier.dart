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
}

class GeobotanyClassifierService {
  static const double confidenceThreshold = 0.65;
  static const String modelAsset = 'assets/models/geobotany_classifier_int8.tflite';

  Future<void> loadModel() async {}

  Future<GeobotanyClassification> classify(String imagePath) async {
    return GeobotanyClassification(
      species: 'ocimum_centraliafricanum',
      confidence: 0.82,
      mineralAffinity: const {'Cu': 'VERY_HIGH', 'Ni': 'HIGH'},
      recommendedAction: 'Collect leaf tissue sample and run XRF transect',
    );
  }
}
