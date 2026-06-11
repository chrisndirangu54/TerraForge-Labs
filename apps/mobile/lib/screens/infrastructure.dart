import 'package:flutter/material.dart';

import '../services/terraforge_api.dart';
import '../widgets/backend_action_screen.dart';

class InfrastructureScreen extends StatelessWidget {
  const InfrastructureScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = TerraforgeApi();
    return BackendActionScreen(
      title: 'Infrastructure',
      description: 'Fetch road network metadata from GET /infra/roads.',
      actionLabel: 'Load Roads',
      onAction: api.roads,
    );
  }
}
