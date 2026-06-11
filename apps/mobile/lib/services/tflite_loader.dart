import 'package:flutter/services.dart';
import 'package:tflite_flutter/tflite_flutter.dart';

/// Optional TFLite loader with graceful fallback when assets are placeholders.
class TfliteLoader {
  Interpreter? _interpreter;
  bool _loaded = false;

  bool get isLoaded => _loaded && _interpreter != null;

  Future<bool> load(String assetPath) async {
    if (_loaded) {
      return isLoaded;
    }
    _loaded = true;
    try {
      _interpreter = await Interpreter.fromAsset(assetPath);
      return true;
    } on PlatformException {
      _interpreter = null;
      return false;
    } catch (_) {
      _interpreter = null;
      return false;
    }
  }

  List<double> predict(List<double> input, {int outputSize = 8}) {
    final interpreter = _interpreter;
    if (interpreter == null) {
      return const [];
    }

    final inputTensor = [input];
    final outputTensor = [
      List<double>.filled(outputSize, 0.0),
    ];
    interpreter.run(inputTensor, outputTensor);
    return outputTensor.first;
  }

  void dispose() {
    _interpreter?.close();
    _interpreter = null;
    _loaded = false;
  }
}