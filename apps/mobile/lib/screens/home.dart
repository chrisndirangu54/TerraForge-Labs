import 'package:flutter/material.dart';

import '../services/auth_service.dart';
import '../services/project_store.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final email = AuthService.instance.user?['email'] ?? 'field user';
    final projectId = ProjectStore.instance.selectedProjectId;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Terraforge Field Home'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => Navigator.pushNamed(context, '/settings'),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Signed in: $email'),
          Text('Project: $projectId'),
          const SizedBox(height: 8),
          const _NavCard(
            icon: '📊',
            title: 'Mission Control',
            route: '/dashboard',
          ),
          const _NavCard(icon: '📁', title: 'Projects', route: '/projects'),
          const _NavCard(
            icon: '🛰',
            title: 'Platform Hub',
            route: '/platform',
          ),
          const _NavCard(
            icon: '💰',
            title: 'Ore Financials',
            route: '/financial',
          ),
          const _NavCard(
            icon: '🧠',
            title: 'Model Training',
            route: '/training',
          ),
          const _NavCard(icon: '🤖', title: 'Copilot', route: '/copilot'),
          const _NavCard(
            icon: '📡',
            title: 'Data Capture',
            route: '/capture',
          ),
          const _NavCard(icon: '🧭', title: 'Main Map', route: '/map'),
          const _NavCard(icon: '🌐', title: '3D Deposit Model', route: '/map/3d'),
          const _NavCard(
            icon: '🗺',
            title: 'View Kriging Map',
            route: '/kriging-map',
          ),
          const _NavCard(
            icon: '🔬',
            title: 'Classify Mineral',
            route: '/classify-mineral',
          ),
          const _NavCard(icon: '🌿', title: 'Geobotany Survey', route: '/geobotany'),
          const _NavCard(icon: '☁', title: 'Cloud GPU', route: '/cloud-gpu'),
          const _NavCard(icon: '🛒', title: 'Marketplace', route: '/marketplace'),
          const _NavCard(icon: '💧', title: 'Hydrogeology', route: '/hydro'),
          const _NavCard(icon: '🏙', title: 'Urban Planning', route: '/urban'),
          const _NavCard(
            icon: '🛣',
            title: 'Infrastructure',
            route: '/infrastructure',
          ),
          const _NavCard(
            icon: '🛰',
            title: 'Satellite Browser',
            route: '/satellite',
          ),
          const _NavCard(icon: '🧬', title: 'Digital Twin', route: '/twin'),
          const _NavCard(icon: '📳', title: 'Seismic Section', route: '/seismic'),
          const _NavCard(icon: '🌈', title: 'Spectral Map', route: '/spectral'),
          const _NavCard(
            icon: '🔍',
            title: 'Thin Section',
            route: '/thin-section',
          ),
          const _NavCard(icon: '📦', title: 'Offline Packs', route: '/offline'),
          const _NavCard(
            icon: '📄',
            title: 'Generate JORC Report',
            route: '/jorc-report',
          ),
        ],
      ),
    );
  }
}

class _NavCard extends StatelessWidget {
  final String icon;
  final String title;
  final String route;

  const _NavCard({
    required this.icon,
    required this.title,
    required this.route,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        title: Text('$icon  $title'),
        onTap: () => Navigator.pushNamed(context, route),
      ),
    );
  }
}