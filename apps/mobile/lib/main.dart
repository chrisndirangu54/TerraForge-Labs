import 'package:flutter/material.dart';
import 'screens/classify_mineral.dart';
import 'screens/geobotany.dart';
import 'screens/home.dart';
import 'screens/instrument_capture.dart';
import 'screens/jorc_report.dart';
import 'screens/kriging_map.dart';
import 'screens/login.dart';

void main() {
  runApp(const TerraforgeApp());
}

class TerraforgeApp extends StatelessWidget {
  const TerraforgeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Terraforge Labs',
      routes: {
        '/': (context) => const LoginScreen(),
        '/home': (context) => const HomeScreen(),
        '/instrument-capture': (context) => const InstrumentCaptureScreen(),
        '/kriging-map': (context) => const KrigingMapScreen(),
        '/classify-mineral': (context) => const ClassifyMineralScreen(),
        '/jorc-report': (context) => const JorcReportScreen(),
        '/geobotany': (context) => const GeobotanyScreen(),
      },
    );
  }
}
