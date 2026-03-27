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
          _NavCard(icon: '🗺', title: 'View Kriging Map', route: '/kriging-map'),
          _NavCard(icon: '🔬', title: 'Classify Mineral', route: '/classify-mineral'),
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
    );
  }
}
