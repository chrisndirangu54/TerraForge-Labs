import 'package:flutter/material.dart';

import '../services/terraforge_api.dart';
import '../widgets/backend_action_screen.dart';

class SatelliteBrowserScreen extends StatelessWidget {
  const SatelliteBrowserScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = TerraforgeApi();
    return BackendActionScreen(
      title: 'Satellite Browser',
      description: 'Browse available satellite scenes from GET /satellite/scenes.',
      actionLabel: 'Load Scenes',
      onAction: api.satelliteScenes,
    );
  }
}