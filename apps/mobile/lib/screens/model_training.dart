import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../services/job_poller.dart';
import '../services/project_store.dart';
import '../services/terraforge_api.dart';
import '../widgets/capture/capture_result_view.dart';
import '../widgets/results/job_status_panel.dart';
import '../widgets/results/structured_json_view.dart';

const _domainTasks = ['thin_section', 'spectral'];

class ModelTrainingScreen extends StatefulWidget {
  const ModelTrainingScreen({super.key});

  @override
  State<ModelTrainingScreen> createState() => _ModelTrainingScreenState();
}

class _ModelTrainingScreenState extends State<ModelTrainingScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  final JobPollerService _poller = JobPollerService();

  String _task = 'thin_section';
  String? _selectedClass;
  List<String> _classes = [];
  Map<String, dynamic>? _manifest;
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;
  Map<String, dynamic>? _uploadResult;

  @override
  void initState() {
    super.initState();
    _loadMeta();
  }

  Future<void> _loadMeta() async {
    try {
      final classes = await _api.trainingClasses(_task);
      final manifest = await _api.trainingManifest(_task);
      setState(() {
        _classes = classes;
        _selectedClass = classes.isNotEmpty ? classes.first : null;
        _manifest = manifest;
      });
    } catch (error) {
      setState(() => _error = error.toString());
    }
  }

  Future<void> _pullDatasets() async {
    await _run(() => _api.pullTrainingDatasets(async: true, extra: {
      'include_domain': true,
    }));
    await _loadMeta();
  }

  Future<void> _trainDomain() async {
    await _run(() async {
      final started = await _api.runTraining(_task, async: true, extra: {
        'data_source': 'corpus',
        'epochs': 6,
        'cv_folds': 5,
      });
      final jobId = started['job_id']?.toString();
      if (jobId == null) return started;
      return _poller.poll(jobId);
    });
    await _loadMeta();
  }

  Future<void> _uploadTrainingData() async {
    if (_selectedClass == null) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      Map<String, dynamic> uploaded;
      if (_task == 'spectral') {
        final picked = await FilePicker.platform.pickFiles(
          type: FileType.custom,
          allowedExtensions: ['npy', 'csv', 'tsv', 'json'],
          withData: true,
        );
        final file = picked?.files.single;
        if (file?.bytes == null) {
          setState(() => _loading = false);
          return;
        }
        uploaded = await _api.uploadSpectralTraining(
          className: _selectedClass!,
          fileBytes: file!.bytes!,
          filename: file.name,
          projectId: ProjectStore.instance.selectedProjectId,
        );
      } else {
        final pairPick = await FilePicker.platform.pickFiles(
          type: FileType.custom,
          allowedExtensions: ['npy'],
          withData: true,
        );
        final pair = pairPick?.files.single;
        if (pair?.bytes != null) {
          uploaded = await _api.uploadThinSectionTraining(
            className: _selectedClass!,
            pairBytes: pair!.bytes,
            pairFilename: pair.name,
            projectId: ProjectStore.instance.selectedProjectId,
          );
        } else {
          final images = await FilePicker.platform.pickFiles(
            type: FileType.image,
            allowMultiple: true,
            withData: true,
          );
          final files = images?.files ?? [];
          if (files.length < 2) {
            throw Exception('Select a .npy pair or two images (PPL and XPL).');
          }
          uploaded = await _api.uploadThinSectionTraining(
            className: _selectedClass!,
            pplBytes: files[0].bytes,
            pplFilename: files[0].name,
            xplBytes: files[1].bytes,
            xplFilename: files[1].name,
            projectId: ProjectStore.instance.selectedProjectId,
          );
        }
      }
      final manifest = await _api.trainingManifest(_task);
      setState(() {
        _uploadResult = uploaded;
        _manifest = manifest;
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
    return Scaffold(
      appBar: AppBar(
        title: const Text('Model Training'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadMeta),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Upload thin-section PPL/XPL pairs or USGS reflectance spectra, then train domain CNNs.',
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            key: ValueKey(_task),
            initialValue: _task,
            decoration: const InputDecoration(
              labelText: 'Training task',
              border: OutlineInputBorder(),
            ),
            items: _domainTasks
                .map((task) => DropdownMenuItem(value: task, child: Text(task)))
                .toList(),
            onChanged: (value) async {
              if (value == null) return;
              setState(() => _task = value);
              await _loadMeta();
            },
          ),
          const SizedBox(height: 12),
          if (_classes.isNotEmpty)
            DropdownButtonFormField<String>(
              key: ValueKey(_selectedClass),
              initialValue: _selectedClass,
              decoration: const InputDecoration(
                labelText: 'Mineral / grain class',
                border: OutlineInputBorder(),
              ),
              items: _classes
                  .map((name) => DropdownMenuItem(value: name, child: Text(name)))
                  .toList(),
              onChanged: (value) => setState(() => _selectedClass = value),
            ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _loading ? null : _uploadTrainingData,
            icon: const Icon(Icons.upload_file),
            label: Text(
              _task == 'spectral'
                  ? 'Upload reflectance (.npy/.csv/.json)'
                  : 'Upload PPL/XPL (.npy or images)',
            ),
          ),
          const SizedBox(height: 8),
          OutlinedButton(
            onPressed: _loading ? null : _pullDatasets,
            child: const Text('Pull training corpora'),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: _loading ? null : _trainDomain,
            child: Text(_loading ? 'Working...' : 'Train $_task model'),
          ),
          if (_manifest != null) ...[
            const SizedBox(height: 16),
            Text(
              'Manifest: ${_manifest!['source'] ?? 'unknown'} · '
              '${_manifest!['samples'] ?? _manifest!['sample_count'] ?? 0} samples',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_uploadResult != null) ...[
            const SizedBox(height: 16),
            CaptureResultView(fallback: _uploadResult),
          ],
          if (_result != null) ...[
            const SizedBox(height: 16),
            JobStatusPanel(job: _result, title: 'Training job'),
          ],
          if (_manifest != null) ...[
            const SizedBox(height: 16),
            StructuredJsonView(data: _manifest, title: 'Dataset manifest'),
          ],
        ],
      ),
    );
  }
}