import 'package:flutter/material.dart';

import 'screens/classify_mineral.dart';
import 'screens/cloud_gpu.dart';
import 'screens/copilot.dart';
import 'screens/dashboard.dart';
import 'screens/digital_twin.dart';
import 'screens/financial.dart';
import 'screens/geobotany.dart';
import 'screens/home.dart';
import 'screens/hydrogeology.dart';
import 'screens/infrastructure.dart';
import 'screens/data_capture.dart';
import 'screens/jorc_report.dart';
import 'screens/kriging_map.dart';
import 'screens/login.dart';
import 'screens/main_map.dart';
import 'screens/map_3d.dart';
import 'screens/marketplace.dart';
import 'screens/model_training.dart';
import 'screens/offline_manager.dart';
import 'screens/platform_hub.dart';
import 'screens/projects.dart';
import 'screens/satellite_browser.dart';
import 'screens/seismic_section.dart';
import 'screens/settings.dart';
import 'screens/spectral_map.dart';
import 'screens/thin_section_viewer.dart';
import 'screens/urban.dart';
import 'services/auth_service.dart';
import 'services/project_store.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await AuthService.instance.loadSession();
  await ProjectStore.instance.load();
  runApp(const TerraforgeApp());
}

class TerraforgeApp extends StatelessWidget {
  const TerraforgeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Terraforge Labs',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      initialRoute: AuthService.instance.isAuthenticated ? '/home' : '/',
      routes: {
        '/': (context) => const LoginScreen(),
        '/home': (context) => const HomeScreen(),
        '/dashboard': (context) => const DashboardScreen(),
        '/projects': (context) => const ProjectsScreen(),
        '/platform': (context) => const PlatformHubScreen(),
        '/financial': (context) => const FinancialScreen(),
        '/training': (context) => const ModelTrainingScreen(),
        '/copilot': (context) => const CopilotScreen(),
        '/settings': (context) => const SettingsScreen(),
        '/instrument-capture': (context) => const DataCaptureScreen(),
        '/capture': (context) => const DataCaptureScreen(),
        '/kriging-map': (context) => const KrigingMapScreen(),
        '/classify-mineral': (context) => const ClassifyMineralScreen(),
        '/cloud-gpu': (context) => const CloudGpuScreen(),
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
        '/marketplace': (context) => const MarketplaceScreen(),
        '/seismic': (context) => const SeismicSectionScreen(),
        '/spectral': (context) => const SpectralMapScreen(),
        '/thin-section': (context) => const ThinSectionViewerScreen(),
      },
    );
  }
}