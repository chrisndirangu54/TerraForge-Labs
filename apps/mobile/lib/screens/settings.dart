import 'package:flutter/material.dart';

import '../config/api_config.dart';
import '../services/auth_service.dart';
import '../services/project_store.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  Future<void> _logout(BuildContext context) async {
    await AuthService.instance.clear();
    if (!context.mounted) return;
    Navigator.pushNamedAndRemoveUntil(context, '/', (_) => false);
  }

  @override
  Widget build(BuildContext context) {
    final user = AuthService.instance.user;
    final projectId = ProjectStore.instance.selectedProjectId;

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ListTile(
            title: const Text('API base URL'),
            subtitle: Text(ApiConfig.baseUrl),
          ),
          ListTile(
            title: const Text('Signed in as'),
            subtitle: Text(user?['email']?.toString() ?? 'anonymous'),
          ),
          ListTile(
            title: const Text('Selected project'),
            subtitle: Text(projectId),
            trailing: TextButton(
              onPressed: () => Navigator.pushNamed(context, '/projects'),
              child: const Text('Change'),
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () => _logout(context),
            child: const Text('Sign Out'),
          ),
        ],
      ),
    );
  }
}