import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../services/capture_sync_service.dart';
import '../services/project_store.dart';
import '../services/sync_queue.dart';
import '../services/terraforge_api.dart';
import '../widgets/capture/capture_result_view.dart';
import '../widgets/capture/data_table.dart';

class DataCaptureScreen extends StatefulWidget {
  const DataCaptureScreen({super.key});

  @override
  State<DataCaptureScreen> createState() => _DataCaptureScreenState();
}

class _DataCaptureScreenState extends State<DataCaptureScreen>
    with SingleTickerProviderStateMixin {
  final TerraforgeApi _api = TerraforgeApi();
  final CaptureSyncService _sync = CaptureSyncService();

  late final TabController _tabs;
  bool _loading = false;
  String? _error;

  String _transport = 'file';
  String _instrumentType = 'auto';
  Map<String, dynamic>? _catalog;
  Map<String, dynamic>? _captureResult;
  List<dynamic> _sessions = [];
  List<dynamic> _devices = [];
  List<dynamic> _observations = [];
  String? _deviceSessionId;
  String? _connectedDeviceId;
  SyncQueueSummary? _queueSummary;
  List<SyncQueueEntry> _queueEntries = [];

  static const _supportedExtensions = [
    'csv', 'tsv', 'xml', 'json', 'geojson', 'pdf', 'nmea', 'txt', 'las', 'laz',
  ];

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 4, vsync: this);
    _bootstrap();
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _bootstrap() async {
    setState(() => _loading = true);
    try {
      final catalog = await _api.captureCatalog();
      final sessions = await _api.captureSessions(
        projectId: ProjectStore.instance.selectedProjectId,
      );
      final observations = await _api.listObservations(
        projectId: ProjectStore.instance.selectedProjectId,
      );
      final summary = await _sync.summary();
      final queue = await _sync.listAll(limit: 20);
      setState(() {
        _catalog = catalog;
        _sessions = sessions['items'] is List ? sessions['items'] as List : [];
        _observations =
            observations['items'] is List ? observations['items'] as List : [];
        _queueSummary = summary;
        _queueEntries = queue;
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  List<Map<String, dynamic>> get _transports {
    final raw = _catalog?['transports'];
    if (raw is List) {
      return raw.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
    }
    return [
      {'id': 'file', 'label': 'File upload'},
      {'id': 'bluetooth', 'label': 'Bluetooth'},
      {'id': 'wifi', 'label': 'Wi-Fi'},
      {'id': 'radio', 'label': 'Radio'},
    ];
  }

  List<String> get _instruments {
    final raw = _catalog?['instruments'];
    if (raw is List) return raw.map((e) => '$e').toList();
    return ['terrameter', 'xrf_bruker', 'kappameter', 'gnss_trimble'];
  }

  Future<void> _pickAndUpload({bool queueOffline = false}) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: _supportedExtensions,
        withData: true,
      );
      final file = result?.files.single;
      if (file == null) {
        setState(() => _loading = false);
        return;
      }

      final bytes = file.bytes ?? await File(file.path!).readAsBytes();
      final filename = file.name;
      final instrument = _instrumentType == 'auto' ? null : _instrumentType;

      if (queueOffline) {
        await _sync.enqueueFile(
          instrumentType: instrument ?? 'auto',
          filename: filename,
          fileBytes: bytes,
          metadata: {'transport': _transport},
        );
        await _refreshQueue();
        setState(() => _loading = false);
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Queued for offline sync')),
        );
        return;
      }

      final upload = await _api.uploadCaptureFile(
        fileBytes: bytes,
        filename: filename,
        instrumentType: instrument,
        transport: _transport,
      );
      setState(() {
        _captureResult = upload;
        _loading = false;
      });
      await _bootstrap();
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _scanDevices() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final scan = await _api.scanDevices(transport: _transport);
      setState(() {
        _devices = scan['devices'] is List ? scan['devices'] as List : [];
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _connectDevice(String deviceId) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await _api.connectDevice(
        deviceId: deviceId,
        transport: _transport,
      );
      setState(() {
        _deviceSessionId = response['session_id']?.toString();
        _connectedDeviceId = deviceId;
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _syncDevice() async {
    final sessionId = _deviceSessionId;
    if (sessionId == null) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await _api.syncDeviceSession(sessionId: sessionId);
      setState(() {
        _captureResult = result;
        _loading = false;
      });
      await _bootstrap();
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _refreshQueue() async {
    final summary = await _sync.summary();
    final queue = await _sync.listAll(limit: 20);
    setState(() {
      _queueSummary = summary;
      _queueEntries = queue;
    });
  }

  Future<void> _flushQueue() async {
    setState(() => _loading = true);
    try {
      final count = await _sync.flushPending(
        transport: _transport,
        projectId: ProjectStore.instance.selectedProjectId,
      );
      await _refreshQueue();
      setState(() => _loading = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Uploaded $count queued file(s)')),
      );
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final projectId = ProjectStore.instance.selectedProjectId;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Data Capture'),
        bottom: TabBar(
          controller: _tabs,
          isScrollable: true,
          tabs: const [
            Tab(text: 'Files'),
            Tab(text: 'Devices'),
            Tab(text: 'History'),
            Tab(text: 'Queue'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loading ? null : _bootstrap,
          ),
        ],
      ),
      body: _loading && _captureResult == null
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabs,
              children: [
                _filesTab(projectId),
                _devicesTab(projectId),
                _historyTab(),
                _queueTab(),
              ],
            ),
    );
  }

  Widget _filesTab(String projectId) {
    final formats = _catalog?['formats'];
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Project: $projectId'),
        const SizedBox(height: 8),
        Text(
          'Upload CSV, PDF, XML, GeoJSON, NMEA, LAS/LAZ and other survey exports.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        if (formats is Map) ...[
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            children: formats.keys
                .map((fmt) => Chip(label: Text('$fmt', style: const TextStyle(fontSize: 11))))
                .toList(),
          ),
        ],
        const SizedBox(height: 16),
        _transportPicker(),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          initialValue: _instrumentType,
          decoration: const InputDecoration(
            labelText: 'Instrument (auto-detect)',
            border: OutlineInputBorder(),
          ),
          items: [
            const DropdownMenuItem(value: 'auto', child: Text('Auto-detect from file')),
            ..._instruments.map(
              (item) => DropdownMenuItem(value: item, child: Text(item)),
            ),
          ],
          onChanged: _loading ? null : (v) => setState(() => _instrumentType = v ?? 'auto'),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: _loading ? null : () => _pickAndUpload(),
                icon: const Icon(Icons.upload_file),
                label: const Text('Pick & Upload'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: _loading ? null : () => _pickAndUpload(queueOffline: true),
                icon: const Icon(Icons.cloud_off),
                label: const Text('Queue Offline'),
              ),
            ),
          ],
        ),
        if (_error != null) ...[
          const SizedBox(height: 12),
          Text(_error!, style: const TextStyle(color: Colors.red)),
        ],
        if (_captureResult != null) ...[
          const SizedBox(height: 16),
          Text(
            'Capture result · ${_captureResult!['row_count'] ?? 0} rows',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          CaptureResultView(
            display: _captureResult!['display'] is Map
                ? Map<String, dynamic>.from(_captureResult!['display'] as Map)
                : null,
            fallback: _captureResult,
          ),
        ],
        const SizedBox(height: 24),
        Text('Stored observations', style: Theme.of(context).textTheme.titleSmall),
        const SizedBox(height: 8),
        _observationsTable(),
      ],
    );
  }

  Widget _devicesTab(String projectId) {
    final transportMeta = _transports.firstWhere(
      (t) => t['id'] == _transport,
      orElse: () => {},
    );
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Project: $projectId'),
        const SizedBox(height: 12),
        _transportPicker(),
        if (transportMeta['description'] != null) ...[
          const SizedBox(height: 8),
          Text('${transportMeta['description']}'),
        ],
        const SizedBox(height: 16),
        Row(
          children: [
            ElevatedButton(
              onPressed: _loading ? null : _scanDevices,
              child: const Text('Scan devices'),
            ),
            const SizedBox(width: 8),
            if (_deviceSessionId != null)
              ElevatedButton(
                onPressed: _loading ? null : _syncDevice,
                child: const Text('Sync readings'),
              ),
          ],
        ),
        if (_connectedDeviceId != null) ...[
          const SizedBox(height: 8),
          Text(
            'Connected: $_connectedDeviceId · session ${_deviceSessionId?.substring(0, 8)}…',
            style: TextStyle(color: Theme.of(context).colorScheme.primary),
          ),
        ],
        if (_error != null) ...[
          const SizedBox(height: 12),
          Text(_error!, style: const TextStyle(color: Colors.red)),
        ],
        const SizedBox(height: 16),
        ..._devices.whereType<Map>().map((device) {
          final id = '${device['device_id']}';
          return Card(
            child: ListTile(
              leading: Icon(_transportIcon(_transport)),
              title: Text('${device['name'] ?? id}'),
              subtitle: Text(
                '${device['instrument_type']} · ${device['battery_pct']}% battery · '
                '${(device['transports'] as List? ?? []).join(', ')}',
              ),
              trailing: ElevatedButton(
                onPressed: _loading ? null : () => _connectDevice(id),
                child: Text('Connect'),
              ),
            ),
          );
        }),
        if (_captureResult != null) ...[
          const SizedBox(height: 16),
          CaptureResultView(
            display: _captureResult!['display'] is Map
                ? Map<String, dynamic>.from(_captureResult!['display'] as Map)
                : null,
            fallback: _captureResult,
          ),
        ],
      ],
    );
  }

  Widget _historyTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (_sessions.isEmpty)
          const Text('No capture sessions yet for this project.')
        else
          ..._sessions.whereType<Map>().map((session) {
            return Card(
              child: ListTile(
                leading: Icon(_formatIcon('${session['file_format']}')),
                title: Text('${session['filename'] ?? session['upload_id']}'),
                subtitle: Text(
                  '${session['instrument_type']} · ${session['transport']} · '
                  '${session['row_count']} rows · ${session['captured_at']}',
                ),
                trailing: Chip(
                  label: Text('${session['display_type'] ?? 'data'}',
                      style: const TextStyle(fontSize: 10)),
                ),
              ),
            );
          }),
      ],
    );
  }

  Widget _queueTab() {
    final summary = _queueSummary;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (summary != null)
          Wrap(
            spacing: 8,
            children: [
              Chip(label: Text('Pending: ${summary.pending}')),
              Chip(label: Text('Uploading: ${summary.uploading}')),
              Chip(label: Text('Done: ${summary.completed}')),
              Chip(label: Text('Failed: ${summary.failed}')),
            ],
          ),
        const SizedBox(height: 12),
        ElevatedButton(
          onPressed: _loading ? null : _flushQueue,
          child: const Text('Upload queued files'),
        ),
        const SizedBox(height: 16),
        if (_queueEntries.isEmpty)
          const Text('Offline queue is empty.')
        else
          ..._queueEntries.map(
            (entry) => Card(
              child: ListTile(
                title: Text(entry.filename),
                subtitle: Text(
                  '${entry.instrumentType} · ${entry.status.name} · '
                  '${entry.attempts} attempts',
                ),
                trailing: entry.lastError != null
                    ? Icon(Icons.error_outline, color: Colors.red.shade300)
                    : null,
              ),
            ),
          ),
      ],
    );
  }

  Widget _transportPicker() {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: _transports.map((transport) {
        final id = '${transport['id']}';
        final selected = _transport == id;
        return ChoiceChip(
          label: Text('${transport['label'] ?? id}'),
          selected: selected,
          onSelected: _loading
              ? null
              : (_) => setState(() {
                    _transport = id;
                    _devices = [];
                    _connectedDeviceId = null;
                    _deviceSessionId = null;
                  }),
        );
      }).toList(),
    );
  }

  Widget _observationsTable() {
    if (_observations.isEmpty) {
      return const Text('No observations stored for this project yet.');
    }
    final rows = _observations.whereType<Map>().map((item) {
      final data = item['data'];
      return {
        'sample_id': item['sample_id'] ?? '${item['id']}'.substring(0, 8),
        'instrument': item['instrument_type'] ?? '—',
        'lon': item['lon'],
        'lat': item['lat'],
        'source': item['source'],
        'flagged': item['flagged'] == true ? 'yes' : 'no',
        'primary_value': data is Map ? (data.values.isNotEmpty ? data.values.first : '—') : '—',
      };
    }).toList();

    return CaptureDataTable(
      columns: const [
        'sample_id', 'instrument', 'lon', 'lat', 'source', 'flagged', 'primary_value',
      ],
      rows: rows.map((r) => Map<String, dynamic>.from(r)).toList(),
    );
  }

  IconData _transportIcon(String transport) {
    switch (transport) {
      case 'bluetooth':
        return Icons.bluetooth;
      case 'wifi':
        return Icons.wifi;
      case 'radio':
        return Icons.sensors;
      case 'usb':
        return Icons.usb;
      default:
        return Icons.folder_open;
    }
  }

  IconData _formatIcon(String format) {
    if (format.contains('pdf')) return Icons.picture_as_pdf;
    if (format.contains('csv') || format.contains('tsv')) return Icons.table_chart;
    if (format.contains('geo')) return Icons.map;
    return Icons.insert_drive_file;
  }
}