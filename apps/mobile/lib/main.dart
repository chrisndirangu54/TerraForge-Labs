import 'package:flutter/material.dart';
import 'screens/classify_mineral.dart';
import 'screens/geobotany.dart';
import 'screens/home.dart';
import 'screens/instrument_capture.dart';
import 'screens/jorc_report.dart';
import 'screens/kriging_map.dart';
import 'screens/login.dart';
import 'screens/main_map.dart';
import 'screens/map_3d.dart';
import 'screens/hydrogeology.dart';
import 'screens/urban.dart';
import 'screens/infrastructure.dart';
import 'screens/satellite_browser.dart';
import 'screens/digital_twin.dart';
import 'screens/offline_manager.dart';
import 'screens/home.dart';
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
        '/map': (context) => const MainMapScreen(),
        '/map/3d': (context) => const Map3dScreen(),
        '/hydro': (context) => const HydrogeologyScreen(),
        '/urban': (context) => const UrbanScreen(),
        '/infrastructure': (context) => const InfrastructureScreen(),
        '/satellite': (context) => const SatelliteBrowserScreen(),
        '/twin': (context) => const DigitalTwinScreen(),
        '/offline': (context) => const OfflineManagerScreen(),
      },
    );
  }
}
