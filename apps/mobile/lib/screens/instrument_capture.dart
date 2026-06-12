import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/instrument_upload.dart';

const _sampleTerrameterXml = '''
<?xml version="1.0"?>
<survey>
  <measurement>
    <profile_id>P-01</profile_id>
    <electrode_spacing_m>10</electrode_spacing_m>
    <apparent_resistivity_ohm_m>120</apparent_resistivity_ohm_m>
    <ip_chargeability_ms>2.5</ip_chargeability_ms>
    <sp_mv>10</sp_mv>
    <lon>37.5</lon>
    <lat>-1.15</lat>
  </measurement>
</survey>
''';

class InstrumentCaptureScreen extends StatefulWidget {
  const InstrumentCaptureScreen({super.key});

  @override
  State<InstrumentCaptureScreen> createState() =>
      _InstrumentCaptureScreenState();
}

class _InstrumentCaptureScreenState extends State<InstrumentCaptureScreen> {
  final InstrumentUploadService _uploadService = InstrumentUploadService();
  String _instrumentType = 'terrameter';
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;

  Future<void> _uploadSample() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await _uploadService.upload(
        instrumentType: _instrumentType,
        fileBytes: utf8.encode(_sampleTerrameterXml),
        filename: 'sample_terrameter.xml',
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
    return Scaffold(
      appBar: AppBar(title: const Text('Instrument Capture')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Upload field instrument data to the TerraForge API.'),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            initialValue: _instrumentType,
            decoration: const InputDecoration(labelText: 'Instrument type'),
            items: const [
              DropdownMenuItem(value: 'terrameter', child: Text('Terrameter')),
              DropdownMenuItem(value: 'xrf_bruker', child: Text('XRF Bruker')),
              DropdownMenuItem(value: 'kappameter', child: Text('Kappameter')),
              DropdownMenuItem(value: 'gnss_trimble', child: Text('GNSS Trimble')),
            ],
            onChanged: _loading
                ? null
                : (value) {
                    if (value != null) {
                      setState(() => _instrumentType = value);
                    }
                  },
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _uploadSample,
            child: Text(_loading ? 'Uploading...' : 'Upload Sample File'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_result != null) ...[
            const SizedBox(height: 16),
            SelectableText(
              const JsonEncoder.withIndent('  ').convert(_result),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }
}