import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Terraforge Field Home')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          _NavCard(icon: '📡', title: 'Collect Field Data', route: '/instrument-capture'),
          _NavCard(icon: '🧭', title: 'Main Map', route: '/map'),
          _NavCard(icon: '🌐', title: '3D Viewer', route: '/map/3d'),
          _NavCard(icon: '🗺', title: 'View Kriging Map', route: '/kriging-map'),
          _NavCard(icon: '🔬', title: 'Classify Mineral', route: '/classify-mineral'),
          _NavCard(icon: '🌿', title: 'Geobotany Survey', route: '/geobotany'),
          _NavCard(icon: '💧', title: 'Hydrogeology', route: '/hydro'),
          _NavCard(icon: '🏙', title: 'Urban Planning', route: '/urban'),
          _NavCard(icon: '🛣', title: 'Infrastructure', route: '/infrastructure'),
          _NavCard(icon: '🛰', title: 'Satellite Browser', route: '/satellite'),
          _NavCard(icon: '🧬', title: 'Digital Twin', route: '/twin'),
          _NavCard(icon: '📦', title: 'Offline Packs', route: '/offline'),
          _NavCard(icon: '🗺', title: 'View Kriging Map', route: '/kriging-map'),
          _NavCard(icon: '🔬', title: 'Classify Mineral', route: '/classify-mineral'),
          _NavCard(icon: '🌿', title: 'Geobotany Survey', route: '/geobotany'),
          _NavCard(icon: '📄', title: 'Generate JORC Report', route: '/jorc-report'),
        ],
      ),
    );
  }
}

class _NavCard extends StatelessWidget {
  final String icon;
  final String title;
  final String route;

  const _NavCard({required this.icon, required this.title, required this.route});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        title: Text('$icon  $title'),
        onTap: () => Navigator.pushNamed(context, route),
      ),
    return const Scaffold(
      body: Center(child: Text('Offline-first home scaffold')),
    );
  }
}
