import 'package:flutter/material.dart';

class OfflineManagerScreen extends StatelessWidget {
  const OfflineManagerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: Text('Offline manager: PMTiles country packs, cached scenes, sync status')),
    );
  }
}
