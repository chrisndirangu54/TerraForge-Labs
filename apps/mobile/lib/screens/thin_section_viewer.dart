import 'package:flutter/material.dart';

import '../services/terraforge_api.dart';
import '../widgets/backend_action_screen.dart';

class ThinSectionViewerScreen extends StatelessWidget {
  const ThinSectionViewerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = TerraforgeApi();
    return BackendActionScreen(
      title: 'Thin Section Viewer',
      description:
          'Classify a thin section through POST /classify-thin-section.',
      actionLabel: 'Classify Thin Section',
      onAction: api.classifyThinSection,
    );
  }
}
