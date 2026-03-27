import 'package:flutter/material.dart';
import 'screens/home.dart';
import 'screens/login.dart';

void main() {
  runApp(const TerraforgeApp());
}

class TerraforgeApp extends StatelessWidget {
  const TerraforgeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Terraforge Labs',
      routes: {
        '/': (context) => const LoginScreen(),
        '/home': (context) => const HomeScreen(),
      },
    );
  }
}
