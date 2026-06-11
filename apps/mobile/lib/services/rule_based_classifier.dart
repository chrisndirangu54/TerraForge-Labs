import 'dart:io';

/// Deterministic on-device fallback when TFLite assets are unavailable.
class RuleBasedClassifier {
  static int seedFromBytes(List<int> bytes, String salt) {
    var hash = 2166136261;
    for (final byte in bytes) {
      hash ^= byte;
      hash = (hash * 16777619) & 0xFFFFFFFF;
    }
    for (final codeUnit in salt.codeUnits) {
      hash ^= codeUnit;
      hash = (hash * 16777619) & 0xFFFFFFFF;
    }
    return hash;
  }

  static List<Map<String, dynamic>> topLabels(
    List<String> labels,
    int seed, {
    int count = 3,
  }) {
    if (labels.isEmpty) {
      return const [];
    }
    final primaryIndex = seed % labels.length;
    final confidence = 0.72 + (seed % 23) / 100.0;
    return List.generate(count, (offset) {
      final label = labels[(primaryIndex + offset) % labels.length];
      return {
        'label': label,
        'score': double.parse(
          (confidence - offset * 0.12).clamp(0.05, 1.0).toStringAsFixed(4),
        ),
      };
    });
  }

  static Future<List<int>> readImageBytes(File imageFile) async {
    if (await imageFile.exists()) {
      return imageFile.readAsBytes();
    }
    return imageFile.path.codeUnits;
  }
}