import 'package:flutter/material.dart';

import 'data_capture.dart';

/// Legacy route alias — redirects to the full data capture hub.
class InstrumentCaptureScreen extends StatelessWidget {
  const InstrumentCaptureScreen({super.key});

  @override
  Widget build(BuildContext context) => const DataCaptureScreen();
}