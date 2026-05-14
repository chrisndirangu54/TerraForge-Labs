import 'package:flutter/material.dart';

class SatelliteBrowserScreen extends StatelessWidget {
  const SatelliteBrowserScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: Text('Satellite browser: Sentinel-2, SAR, thermal, change detection')),
    );
  }
}
