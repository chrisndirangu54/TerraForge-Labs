import 'package:flutter/material.dart';

import '../services/terraforge_api.dart';
import '../widgets/results/financial_summary_view.dart';

class FinancialScreen extends StatefulWidget {
  const FinancialScreen({super.key});

  @override
  State<FinancialScreen> createState() => _FinancialScreenState();
}

class _FinancialScreenState extends State<FinancialScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _presets;
  Map<String, dynamic>? _result;

  @override
  void initState() {
    super.initState();
    _loadPresets();
  }

  Future<void> _loadPresets() async {
    setState(() => _loading = true);
    try {
      final presets = await _api.financialPresets();
      setState(() {
        _presets = presets;
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _analyze() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await _api.financialAnalyze({
        'commodity': 'ta',
        'ore_tonnes': 2500000,
        'head_grade_ppm': 120,
        'recovery_pct': 72,
        'price_usd_per_kg': 280,
      });
      setState(() {
        _result = result;
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ore Financials')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Commodity presets and NPV analysis for ore economics.'),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _analyze,
            child: Text(_loading ? 'Loading...' : 'Run Ta NPV Analysis'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_result != null) ...[
            const SizedBox(height: 16),
            FinancialSummaryView(result: _result!, presets: _presets),
          ] else if (_presets != null) ...[
            const SizedBox(height: 16),
            FinancialSummaryView(
              result: const {},
              presets: _presets,
            ),
          ],
        ],
      ),
    );
  }
}