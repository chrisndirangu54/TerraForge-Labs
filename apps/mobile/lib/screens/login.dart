import 'package:flutter/material.dart';

import '../config/api_config.dart';
import '../services/auth_service.dart';
import '../services/terraforge_api.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  final _emailController = TextEditingController(text: 'geo@terraforge.test');
  final _passwordController = TextEditingController(text: 'securepass1');
  bool _checking = false;
  String? _status;

  Future<void> _connect() async {
    setState(() {
      _checking = true;
      _status = null;
    });
    try {
      final health = await _api.health();
      final login = await _api.login(
        email: _emailController.text.trim(),
        password: _passwordController.text,
      );
      AuthService.instance.setSession(
        token: login['access_token'] as String,
        user: Map<String, dynamic>.from(login['user'] as Map),
      );
      if (!mounted) return;
      setState(() {
        _status =
            'Connected: ${health['status']} (v${health['version']}) as ${login['user']['email']}';
        _checking = false;
      });
      Navigator.pushNamed(context, '/home');
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _status =
            'Login failed for ${ApiConfig.baseUrl}. Register a user via POST /auth/register first.\n$error';
        _checking = false;
      });
    }
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
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
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(labelText: 'Email'),
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _passwordController,
              decoration: const InputDecoration(labelText: 'Password'),
              obscureText: true,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _checking ? null : _connect,
              child: Text(_checking ? 'Signing in...' : 'Sign In'),
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