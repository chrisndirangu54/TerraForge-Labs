import 'api_client.dart';
import 'project_store.dart';

class TerraforgeApi {
  TerraforgeApi({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  String get _projectId => ProjectStore.instance.selectedProjectId;

  Future<Map<String, dynamic>> health() => _client.get('/health');

  // --- Auth ---

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) {
    return _client.post('/auth/login', {
      'email': email,
      'password': password,
    });
  }

  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    String displayName = 'Field Geologist',
    String role = 'geologist',
  }) {
    return _client.post('/auth/register', {
      'email': email,
      'password': password,
      'display_name': displayName,
      'role': role,
    });
  }

  Future<Map<String, dynamic>> me() => _client.get('/auth/me');

  // --- Projects ---

  Future<List<dynamic>> listProjects() async {
    final result = await _client.get('/projects');
    final data = result['data'];
    if (data is List) return data;
    return [];
  }

  Future<Map<String, dynamic>> createProject({
    required String slug,
    required String name,
  }) {
    return _client.post('/projects', {'slug': slug, 'name': name});
  }

  Future<Map<String, dynamic>> explorationSummary() =>
      _client.get('/projects/exploration-summary');

  // --- Dashboard ---

  Future<Map<String, dynamic>> dashboardSummary() =>
      _client.get('/dashboard/summary');

  // --- Capture ---

  Future<Map<String, dynamic>> captureCatalog() => _client.get('/capture/catalog');

  Future<Map<String, dynamic>> captureSessions({
    String? projectId,
    int limit = 20,
  }) {
    return _client.get('/capture/sessions', query: {
      if (projectId != null) 'project_id': projectId,
      'limit': '$limit',
    });
  }

  Future<Map<String, dynamic>> captureSessionDetail(String uploadId) =>
      _client.get('/capture/sessions/$uploadId');

  Future<Map<String, dynamic>> uploadCaptureFile({
    required List<int> fileBytes,
    required String filename,
    String? instrumentType,
    String transport = 'file',
    String? projectId,
    List<int>? gpsBytes,
    String? gpsFilename,
    List<int>? calibrationBytes,
    String? calibrationFilename,
  }) {
    return _client.uploadCapture(
      fileBytes: fileBytes,
      filename: filename,
      instrumentType: instrumentType,
      transport: transport,
      projectId: projectId ?? _projectId,
      gpsBytes: gpsBytes,
      gpsFilename: gpsFilename,
      calibrationBytes: calibrationBytes,
      calibrationFilename: calibrationFilename,
    );
  }

  Future<Map<String, dynamic>> captureStream({
    required List<Map<String, dynamic>> readings,
    String? instrumentType,
    String transport = 'wifi',
    String? projectId,
    String? deviceId,
    String? sessionId,
  }) {
    return _client.post('/capture/stream', {
      'readings': readings,
      'instrument_type': instrumentType ?? 'generic_csv',
      'transport': transport,
      'project_id': projectId ?? _projectId,
      if (deviceId != null) 'device_id': deviceId,
      if (sessionId != null) 'session_id': sessionId,
    });
  }

  Future<Map<String, dynamic>> scanDevices({String transport = 'bluetooth'}) {
    return _client.get('/capture/devices/scan', query: {'transport': transport});
  }

  Future<Map<String, dynamic>> connectDevice({
    required String deviceId,
    required String transport,
  }) {
    return _client.post('/capture/devices/$deviceId/connect', {
      'transport': transport,
    });
  }

  Future<Map<String, dynamic>> disconnectDevice(String sessionId) {
    return _client.post('/capture/devices/sessions/$sessionId/disconnect', {});
  }

  Future<Map<String, dynamic>> syncDeviceSession({
    required String sessionId,
    String? projectId,
    int count = 6,
  }) {
    return _client.post('/capture/devices/sessions/$sessionId/sync', {
      'project_id': projectId ?? _projectId,
      'count': count,
    });
  }

  Future<Map<String, dynamic>> listObservations({
    String? projectId,
    int limit = 50,
  }) {
    return _client.get('/ingest/observations', query: {
      if (projectId != null) 'project_id': projectId,
      'limit': '$limit',
    });
  }

  // --- Geodata / jobs ---

  Future<Map<String, dynamic>> runKriging({
    String element = 'ta_ppm',
    String variogramModel = 'spherical',
    int gridResolutionM = 50,
    String dataset = 'matuu_synthetic',
    bool async = true,
    List<Map<String, dynamic>>? observations,
    String? projectId,
  }) {
    return _client.post('/fuse-geodata', {
      'element': element,
      'variogram_model': variogramModel,
      'grid_resolution_m': gridResolutionM,
      'dataset': dataset,
      'async': async,
      'project_id': projectId ?? _projectId,
      if (observations != null) 'observations': observations,
    });
  }

  Future<Map<String, dynamic>> variogramCrossValidate({
    String element = 'ta_ppm',
    String variogramModel = 'spherical',
    String dataset = 'matuu_synthetic',
    String? projectId,
  }) {
    return _client.post('/geodata/variogram/cross-validate', {
      'element': element,
      'variogram_model': variogramModel,
      'dataset': dataset,
      'project_id': projectId ?? _projectId,
    });
  }

  Future<Map<String, dynamic>> getJob(String jobId) => _client.get('/jobs/$jobId');

  Future<Map<String, dynamic>> depositSummary({String? projectId}) {
    return _client.get('/deposit/summary', query: {
      if (projectId != null) 'project_id': projectId,
    });
  }

  Future<Map<String, dynamic>> generateDepositModel({
    String? projectId,
    bool async = true,
    Map<String, dynamic>? extra,
  }) {
    return _client.post('/deposit-model', {
      'project_id': projectId ?? _projectId,
      'async': async,
      ...?extra,
    });
  }

  // --- Reports ---

  Future<Map<String, dynamic>> generateJorcReport({
    String projectName = 'TerraForge Demo',
    String commodity = 'Ta',
    String? projectId,
  }) {
    return _client.post('/reports/jorc', {
      'project_name': projectName,
      'commodity': commodity,
      'project_id': projectId ?? _projectId,
    });
  }

  // --- Financial ---

  Future<Map<String, dynamic>> financialPresets() =>
      _client.get('/financial/ore/presets');

  Future<Map<String, dynamic>> financialAnalyze(Map<String, dynamic> body) =>
      _client.post('/financial/ore/analyze', body);

  Future<Map<String, dynamic>> financialSensitivity(Map<String, dynamic> body) =>
      _client.post('/financial/ore/sensitivity', body);

  // --- Training ---

  Future<Map<String, dynamic>> pullTrainingDatasets({
    bool async = false,
    Map<String, dynamic>? extra,
  }) {
    return _client.post('/training/datasets/pull', {
      'async': async,
      ...?extra,
    });
  }

  Future<Map<String, dynamic>> runTraining(
    String task, {
    bool async = true,
    Map<String, dynamic>? extra,
  }) {
    return _client.post('/training/$task/run', {
      'async': async,
      ...?extra,
    });
  }

  Future<Map<String, dynamic>> trainingManifest(String task) =>
      _client.get('/training/$task/manifest');

  Future<List<String>> trainingClasses(String task) async {
    final response = await _client.get('/training/$task/classes');
    final classes = response['classes'];
    if (classes is List) return classes.map((c) => '$c').toList();
    return [];
  }

  Future<Map<String, dynamic>> uploadThinSectionTraining({
    required String className,
    String? projectId,
    List<int>? pairBytes,
    String? pairFilename,
    List<int>? pplBytes,
    String? pplFilename,
    List<int>? xplBytes,
    String? xplFilename,
  }) {
    return _client.uploadTrainingData(
      task: 'thin_section',
      className: className,
      projectId: projectId ?? _projectId,
      pairBytes: pairBytes,
      pairFilename: pairFilename,
      pplBytes: pplBytes,
      pplFilename: pplFilename,
      xplBytes: xplBytes,
      xplFilename: xplFilename,
    );
  }

  Future<Map<String, dynamic>> uploadSpectralTraining({
    required String className,
    required List<int> fileBytes,
    required String filename,
    String? projectId,
  }) {
    return _client.uploadTrainingData(
      task: 'spectral',
      className: className,
      projectId: projectId ?? _projectId,
      spectralBytes: fileBytes,
      spectralFilename: filename,
    );
  }

  // --- Platform ---

  Future<Map<String, dynamic>> platformPost(
    String path,
    Map<String, dynamic> body,
  ) {
    final withProject = {
      ...body,
      if (!body.containsKey('project_id')) 'project_id': _projectId,
    };
    return _client.post('/platform$path', withProject);
  }

  Future<Map<String, dynamic>> platformGet(String path) =>
      _client.get('/platform$path');

  Future<Map<String, dynamic>> digitalTwinLiveNpv({
    String commodity = 'ta',
    double oreTonnes = 3000000,
    double priceShockPct = -8,
  }) {
    return platformPost('/digital-twin/live-npv', {
      'commodity': commodity,
      'ore_tonnes': oreTonnes,
      'price_shock_pct': priceShockPct,
    });
  }

  // --- Copilot ---

  Future<Map<String, dynamic>> copilotStatus() => _client.get('/copilot/status');

  Future<Map<String, dynamic>> copilotQuery({
    required String query,
    String? projectId,
  }) {
    return _client.post('/copilot/query', {
      'query': query,
      'project_id': projectId ?? _projectId,
    });
  }

  // --- Legacy exploration endpoints ---

  Future<Map<String, dynamic>> groundwaterTable({String bbox = ''}) {
    return _client.get('/hydro/groundwater-table', query: {'bbox': bbox});
  }

  Future<Map<String, dynamic>> boreholes({String bbox = ''}) {
    return _client.get('/hydro/boreholes', query: {'bbox': bbox});
  }

  Future<Map<String, dynamic>> settlements({String bbox = ''}) {
    return _client.get('/urban/settlements', query: {'bbox': bbox});
  }

  Future<Map<String, dynamic>> roads({String bbox = ''}) {
    return _client.get('/infra/roads', query: {'bbox': bbox});
  }

  Future<Map<String, dynamic>> satelliteScenes({
    String bbox = '37.45,-1.20,37.55,-1.10',
  }) {
    return _client.get(
      '/satellite/scenes',
      query: {'bbox': bbox, 'start': '2026-01-01', 'end': '2026-06-30'},
    );
  }

  Future<Map<String, dynamic>> satelliteLatest({
    String bbox = '37.45,-1.20,37.55,-1.10',
    String index = 'ndvi',
  }) {
    return _client.get('/satellite/latest', query: {
      'bbox': bbox,
      'index': index,
    });
  }

  Future<Map<String, dynamic>> satelliteInsar({
    String bbox = '37.45,-1.20,37.55,-1.10',
    List<String>? dateRange,
  }) {
    return _client.post('/satellite/insar', {
      'bbox': bbox,
      'date_range': dateRange ?? ['2026-01-01', '2026-06-30'],
    });
  }

  Future<Map<String, dynamic>> fuseSeismic() {
    return _client.post('/fuse-seismic', {'filepath': 'demo_segy.sgy'});
  }

  Future<Map<String, dynamic>> classifyThinSection() {
    return _client.post('/classify-thin-section', {
      'image_path': 'demo_thin_section.jpg',
    });
  }
}