import 'package:flutter/material.dart';

import '../services/map_service.dart';
import '../widgets/backend_action_screen.dart';

class OfflineManagerScreen extends StatelessWidget {
  const OfflineManagerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final mapService = MapService();
    return BackendActionScreen(
      title: 'Offline Packs',
      description: 'Fetch offline PMTiles pack manifest from the backend.',
      actionLabel: 'Load Kenya Pack',
      onAction: () => mapService.fetchOfflinePack('kenya'),
    );
  }
}
