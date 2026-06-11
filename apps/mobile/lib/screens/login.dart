import 'package:flutter/material.dart';

import '../config/api_config.dart';
import '../services/terraforge_api.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  bool _checking = false;
  String? _status;

  Future<void> _connect() async {
    setState(() {
      _checking = true;
      _status = null;
    });
    try {
      final health = await _api.health();
      if (!mounted) return;
      setState(() {
        _status = 'Connected: ${health['status']} (v${health['version']})';
        _checking = false;
      });
      Navigator.pushNamed(context, '/home');
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _status = 'Backend unreachable at ${ApiConfig.baseUrl}\n$error';
        _checking = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Terraforge Login')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('API: ${ApiConfig.baseUrl}'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _checking ? null : _connect,
              child: Text(_checking ? 'Connecting...' : 'Connect to Backend'),
            ),
            if (_status != null) ...[
              const SizedBox(height: 16),
              Text(_status!, textAlign: TextAlign.center),
            ],
          ],
        ),
      ),
    );
  }
}
