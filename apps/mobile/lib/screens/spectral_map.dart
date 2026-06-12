import 'package:flutter/material.dart';

import '../services/spectral_overlay.dart';
import '../widgets/backend_action_screen.dart';

class SpectralMapScreen extends StatelessWidget {
  const SpectralMapScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final service = SpectralOverlayService();
    return BackendActionScreen(
      title: 'Spectral Map',
      description: 'Run spectral fusion through POST /fuse-spectral.',
      actionLabel: 'Fuse Spectral',
      onAction: service.fuseSpectral,
    );
  }
}