import 'package:flutter/material.dart';

import '../services/terraforge_api.dart';
import '../widgets/capture/capture_result_view.dart';
import '../widgets/results/infer_display.dart';
import '../widgets/results/structured_json_view.dart';

class DigitalTwinScreen extends StatefulWidget {
  const DigitalTwinScreen({super.key});

  @override
  State<DigitalTwinScreen> createState() => _DigitalTwinScreenState();
}

class _DigitalTwinScreenState extends State<DigitalTwinScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  final _commodityController = TextEditingController(text: 'ta');
  final _oreTonnesController = TextEditingController(text: '3000000');

  double _priceShock = -8;
  double _oreTonnes = 3000000;
  String _commodity = 'ta';
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;

  @override
  void dispose() {
    _commodityController.dispose();
    _oreTonnesController.dispose();
    super.dispose();
  }

  Future<void> _runTwin() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await _api.digitalTwinLiveNpv(
        commodity: _commodity,
        oreTonnes: _oreTonnes,
        priceShockPct: _priceShock,
      );
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
    final npvBand = _result?['npv_band_usd'] as Map?;
    final alerts = _result?['alerts'] as List?;

    return Scaffold(
      appBar: AppBar(title: const Text('Digital Twin')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Live NPV twin with price and grade shock bands for the active deposit.',
          ),
          const SizedBox(height: 16),
          TextField(
            decoration: const InputDecoration(
              labelText: 'Commodity',
              border: OutlineInputBorder(),
            ),
            controller: _commodityController,
            onChanged: (value) => _commodity = value.trim(),
          ),
          const SizedBox(height: 12),
          TextField(
            decoration: const InputDecoration(
              labelText: 'Ore tonnes',
              border: OutlineInputBorder(),
            ),
            keyboardType: TextInputType.number,
            controller: _oreTonnesController,
            onChanged: (value) => _oreTonnes = double.tryParse(value) ?? _oreTonnes,
          ),
          const SizedBox(height: 12),
          Text('Price shock: ${_priceShock.toStringAsFixed(0)}%'),
          Slider(
            value: _priceShock,
            min: -30,
            max: 30,
            divisions: 12,
            label: '${_priceShock.toStringAsFixed(0)}%',
            onChanged: (value) => setState(() => _priceShock = value),
          ),
          ElevatedButton(
            onPressed: _loading ? null : _runTwin,
            child: Text(_loading ? 'Running...' : 'Run live NPV twin'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (npvBand != null) ...[
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                Chip(label: Text('P10: \$${npvBand['p10']}')),
                Chip(label: Text('P50: \$${npvBand['p50']}')),
                Chip(label: Text('P90: \$${npvBand['p90']}')),
              ],
            ),
          ],
          if (alerts != null && alerts.isNotEmpty) ...[
            const SizedBox(height: 8),
            ...alerts.map((alert) => ListTile(
                  dense: true,
                  leading: const Icon(Icons.notifications_active),
                  title: Text('$alert'),
                )),
          ],
          if (_result != null) ...[
            const SizedBox(height: 16),
            CaptureResultView(
              display: inferDisplay(_result),
              fallback: _result,
            ),
            const SizedBox(height: 12),
            StructuredJsonView(data: _result, title: 'Twin response'),
          ],
        ],
      ),
    );
  }
}