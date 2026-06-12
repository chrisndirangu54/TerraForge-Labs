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
  final _emailController = TextEditingController(text: 'geo@example.com');
  final _passwordController = TextEditingController(text: 'securepass1');
  bool _checking = false;
  bool _registerMode = false;
  String? _status;

  @override
  void initState() {
    super.initState();
    if (AuthService.instance.isAuthenticated) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          Navigator.pushReplacementNamed(context, '/home');
        }
      });
    }
  }

  Future<void> _connect() async {
    setState(() {
      _checking = true;
      _status = null;
    });
    try {
      final health = await _api.health();
      final email = _emailController.text.trim();
      final password = _passwordController.text;

      Map<String, dynamic> login;
      if (_registerMode) {
        await _api.register(email: email, password: password);
        login = await _api.login(email: email, password: password);
      } else {
        login = await _api.login(email: email, password: password);
      }

      final user = Map<String, dynamic>.from(login['user'] as Map);
      await AuthService.instance.setSession(
        token: login['access_token'] as String,
        user: user,
      );
      if (!mounted) return;
      setState(() {
        _status =
            'Connected: ${health['status']} (v${health['version']}) as ${user['email']}';
        _checking = false;
      });
      Navigator.pushReplacementNamed(context, '/home');
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _status = _registerMode
            ? 'Registration failed for ${ApiConfig.baseUrl}.\n$error'
            : 'Login failed for ${ApiConfig.baseUrl}. Try Register first.\n$error';
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
              child: Text(
                _checking
                    ? (_registerMode ? 'Registering...' : 'Signing in...')
                    : (_registerMode ? 'Register & Sign In' : 'Sign In'),
              ),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: _checking
                  ? null
                  : () => setState(() => _registerMode = !_registerMode),
              child: Text(
                _registerMode
                    ? 'Already have an account? Sign in'
                    : 'New user? Register first',
              ),
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