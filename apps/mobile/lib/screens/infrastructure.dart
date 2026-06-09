import 'package:flutter/material.dart';

class InfrastructureScreen extends StatelessWidget {
  const InfrastructureScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: Text('Infrastructure: roads, power grid, pipelines, telecoms, haulage')),
    );
  }
}
