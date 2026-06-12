import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../services/project_store.dart';
import '../services/terraforge_api.dart';
import '../widgets/capture/capture_result_view.dart';
import '../widgets/results/classification_result_view.dart';
import '../widgets/results/infer_display.dart';
import '../widgets/results/structured_json_view.dart';

class ThinSectionViewerScreen extends StatefulWidget {
  const ThinSectionViewerScreen({super.key});

  @override
  State<ThinSectionViewerScreen> createState() => _ThinSectionViewerScreenState();
}

class _ThinSectionViewerScreenState extends State<ThinSectionViewerScreen> {
  final TerraforgeApi _api = TerraforgeApi();

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
      final classes = await _api.trainingClasses('thin_section');
      setState(() => _classes = classes);
    } catch (_) {}
  }

  Future<void> _classifyDemo() async {
    await _run(() => _api.classifyThinSection());
  }

  Future<void> _uploadSample() async {
    if (_classes.isEmpty) {
      setState(() => _error = 'Load training classes first (open Model Training).');
      return;
    }
    final className = await showDialog<String>(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('Label for upload'),
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

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final pairPick = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['npy'],
        withData: true,
      );
      Map<String, dynamic> uploaded;
      final pair = pairPick?.files.single;
      if (pair?.bytes != null) {
        uploaded = await _api.uploadThinSectionTraining(
          className: className,
          pairBytes: pair!.bytes,
          pairFilename: pair.name,
        );
      } else {
        final images = await FilePicker.platform.pickFiles(
          type: FileType.image,
          allowMultiple: true,
          withData: true,
        );
        final files = images?.files ?? [];
        if (files.length < 2) {
          throw Exception('Select a .npy pair or PPL + XPL images.');
        }
        uploaded = await _api.uploadThinSectionTraining(
          className: className,
          pplBytes: files[0].bytes,
          pplFilename: files[0].name,
          xplBytes: files[1].bytes,
          xplFilename: files[1].name,
          projectId: ProjectStore.instance.selectedProjectId,
        );
      }
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

  Future<void> _run(Future<Map<String, dynamic>> Function() action) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await action();
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
    final display = inferDisplay(_result);

    return Scaffold(
      appBar: AppBar(title: const Text('Thin Section Viewer')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Classify PPL/XPL thin sections or upload labeled pairs into the training corpus.',
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _classifyDemo,
            child: Text(_loading ? 'Running...' : 'Classify demo thin section'),
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _loading ? null : _uploadSample,
            icon: const Icon(Icons.upload_file),
            label: const Text('Upload PPL/XPL training sample'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_result != null) ...[
            const SizedBox(height: 16),
            if (display?['chart'] != null || _result!['label'] != null)
              ClassificationResultView(result: _result!),
            CaptureResultView(display: display, fallback: _result),
            const SizedBox(height: 12),
            StructuredJsonView(data: _result, title: 'Full response'),
          ],
        ],
      ),
    );
  }
}