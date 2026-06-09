import 'package:flutter/material.dart';

class GeobotanyScreen extends StatelessWidget {
  const GeobotanyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Geobotany & Biogeochemistry')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          Text(
            'Track Q field workflow',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 12),
          Text('• Photograph indicator plants for on-device species classification.'),
          Text('• Log vigour, leaf colour, density, local name, and local significance.'),
          Text('• Recommend leaf tissue ICP-MS follow-up and XRF transects.'),
          Text('• Queue low-confidence observations for active-learning retraining.'),
        ],
      ),
    );
  }
}
