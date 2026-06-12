import 'package:flutter/material.dart';

import '../services/terraforge_api.dart';
import '../widgets/backend_action_screen.dart';

class UrbanScreen extends StatelessWidget {
  const UrbanScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = TerraforgeApi();
    return BackendActionScreen(
      title: 'Urban Planning',
      description: 'Fetch settlement records from GET /urban/settlements.',
      actionLabel: 'Load Settlements',
      onAction: api.settlements,
    );
  }
}