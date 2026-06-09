import 'package:flutter/material.dart';

class HydrogeologyScreen extends StatelessWidget {
  const HydrogeologyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: Text('Hydrogeology map: water table, boreholes, aquifers, MODFLOW outputs')),
    );
  }
}
