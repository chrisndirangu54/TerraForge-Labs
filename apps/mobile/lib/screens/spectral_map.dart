import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../services/project_store.dart';
import '../services/spectral_overlay.dart';
import '../services/terraforge_api.dart';
import '../widgets/capture/capture_result_view.dart';
import '../widgets/results/infer_display.dart';
import '../widgets/results/structured_json_view.dart';

class SpectralMapScreen extends StatefulWidget {
  const SpectralMapScreen({super.key});

  @override
  State<SpectralMapScreen> createState() => _SpectralMapScreenState();
}

class _SpectralMapScreenState extends State<SpectralMapScreen> {
  final SpectralOverlayService _spectral = SpectralOverlayService();
  final TerraforgeApi _api = TerraforgeApi();

  String _dataType = 'hyperspectral';
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;
  List<String> _classes = [];

  @override
  void initState() {
    super.initState();
    _loadClasses();
  }

  Future<void> _loadClasses() async {
    try {
      final classes = await _api.trainingClasses('spectral');
      setState(() => _classes = classes);
    } catch (_) {}
  }

  Future<void> _fuseSpectral() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await _spectral.fuseSpectral(dataType: _dataType);
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

  Future<void> _uploadReflectance() async {
    if (_classes.isEmpty) {
      setState(() => _error = 'Load spectral classes first (open Model Training).');
      return;
    }
    final className = await showDialog<String>(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('Mineral class'),
        children: _classes
            .map(
              (name) => SimpleDialogOption(
                onPressed: () => Navigator.pop(context, name),
                child: Text(name),
              ),
            )
            .toList(),
      ),
    );
    if (className == null) return;

    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['npy', 'csv', 'tsv', 'json'],
      withData: true,
    );
    final file = picked?.files.single;
    if (file?.bytes == null) return;

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final uploaded = await _api.uploadSpectralTraining(
        className: className,
        fileBytes: file!.bytes!,
        filename: file.name,
        projectId: ProjectStore.instance.selectedProjectId,
      );
      setState(() {
        _result = uploaded;
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
      appBar: AppBar(title: const Text('Spectral Map')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Fuse hyperspectral overlays or upload USGS-style reflectance curves for training.',
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            key: ValueKey(_dataType),
            initialValue: _dataType,
            decoration: const InputDecoration(
              labelText: 'Data type',
              border: OutlineInputBorder(),
            ),
            items: const [
              DropdownMenuItem(value: 'hyperspectral', child: Text('Hyperspectral')),
              DropdownMenuItem(value: 'radiometrics', child: Text('Radiometrics')),
            ],
            onChanged: (value) {
              if (value != null) setState(() => _dataType = value);
            },
          ),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: _loading ? null : _fuseSpectral,
            child: Text(_loading ? 'Running...' : 'Fuse spectral'),
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _loading ? null : _uploadReflectance,
            icon: const Icon(Icons.upload_file),
            label: const Text('Upload USGS reflectance sample'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_result != null) ...[
            const SizedBox(height: 16),
            CaptureResultView(
              display: inferDisplay(_result),
              fallback: _result,
            ),
            const SizedBox(height: 12),
            StructuredJsonView(data: _result, title: 'Full response'),
          ],
        ],
      ),
    );
  }
}