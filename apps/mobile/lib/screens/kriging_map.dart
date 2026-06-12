import 'package:flutter/material.dart';

import '../services/terraforge_api.dart';
import '../widgets/backend_action_screen.dart';

class KrigingMapScreen extends StatelessWidget {
  const KrigingMapScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = TerraforgeApi();
    return BackendActionScreen(
      title: 'Kriging Map',
      description:
          'Run the kriging pipeline against POST /fuse-geodata and display grid statistics.',
      actionLabel: 'Run Kriging',
      onAction: () => api.runKriging(),
    );
  }
}