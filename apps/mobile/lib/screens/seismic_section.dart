import 'package:flutter/material.dart';

import '../services/terraforge_api.dart';
import '../widgets/backend_action_screen.dart';

class SeismicSectionScreen extends StatelessWidget {
  const SeismicSectionScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = TerraforgeApi();
    return BackendActionScreen(
      title: 'Seismic Section',
      description: 'Fuse seismic data through POST /fuse-seismic.',
      actionLabel: 'Fuse Seismic',
      onAction: api.fuseSeismic,
    );
  }
}
