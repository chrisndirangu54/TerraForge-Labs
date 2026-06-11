import 'package:flutter/material.dart';

import '../services/map_service.dart';
import '../widgets/backend_action_screen.dart';

class MainMapScreen extends StatelessWidget {
  const MainMapScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final mapService = MapService();
    return BackendActionScreen(
      title: 'Main Map',
      description:
          'Fetch mapping layers and a sample vector tile from the backend.',
      actionLabel: 'Load Map Data',
      onAction: () async {
        final layers = await mapService.fetchLayers();
        final tile = await mapService.fetchTile(10, 500, 400);
        return {'layers': layers, 'sample_tile': tile};
      },
    );
  }
}
