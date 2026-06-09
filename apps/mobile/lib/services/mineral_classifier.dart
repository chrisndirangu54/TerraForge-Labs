import 'dart:io';

class MineralClassification {
  final String label;
  final double confidence;
  final List<Map<String, dynamic>> top3;

  MineralClassification({required this.label, required this.confidence, required this.top3});
}

class MineralClassifierService {
  static const double confidenceThreshold = 0.70;
  static const String modelAsset = 'assets/models/mineral_classifier_int8.tflite';

  Future<void> loadModel() async {}

  Future<MineralClassification> classify(File _imageFile) async {
    const confidence = 0.76;
    return MineralClassification(
      label: confidence >= confidenceThreshold ? 'coltan' : 'unknown',
      confidence: confidence,
      top3: const [
        {'label': 'coltan', 'score': 0.76},
        {'label': 'cassiterite', 'score': 0.14},
        {'label': 'ilmenite', 'score': 0.10},
      ],
    );
  }

  void dispose() {}
}
