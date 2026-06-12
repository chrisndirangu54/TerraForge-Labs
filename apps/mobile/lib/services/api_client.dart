import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import 'auth_service.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;

  const ApiException(this.statusCode, this.message);

  @override
  String toString() => 'ApiException($statusCode): $message';
}

class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Map<String, String> get _headers {
    final headers = <String, String>{'Content-Type': 'application/json'};
    final token = AuthService.instance.token;
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Uri _uri(String path, [Map<String, String>? query]) {
    return Uri.parse('${ApiConfig.baseUrl}$path')
        .replace(queryParameters: query);
  }

  Future<Map<String, dynamic>> get(
    String path, {
    Map<String, String>? query,
  }) async {
    final response = await _client.get(_uri(path, query), headers: _headers);
    return _asMap(_decode(response));
  }

  Future<Map<String, dynamic>> post(
    String path,
    Map<String, dynamic> body,
  ) async {
    final response = await _client.post(
      _uri(path),
      headers: _headers,
      body: jsonEncode(body),
    );
    return _asMap(_decode(response));
  }

  Future<Map<String, dynamic>> uploadCapture({
    required List<int> fileBytes,
    required String filename,
    String? instrumentType,
    String transport = 'file',
    String? projectId,
    List<int>? gpsBytes,
    String? gpsFilename,
    List<int>? calibrationBytes,
    String? calibrationFilename,
  }) async {
    final request = http.MultipartRequest('POST', _uri('/capture/upload'));
    final token = AuthService.instance.token;
    if (token != null && token.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $token';
    }
    request.fields['transport'] = transport;
    if (instrumentType != null &&
        instrumentType.isNotEmpty &&
        instrumentType != 'auto') {
      request.fields['instrument_type'] = instrumentType;
    }
    if (projectId != null && projectId.isNotEmpty) {
      request.fields['project_id'] = projectId;
    }
    request.files.add(
      http.MultipartFile.fromBytes('file', fileBytes, filename: filename),
    );
    if (gpsBytes != null && gpsBytes.isNotEmpty) {
      request.files.add(
        http.MultipartFile.fromBytes(
          'gps_file',
          gpsBytes,
          filename: gpsFilename ?? 'gps.csv',
        ),
      );
    }
    if (calibrationBytes != null && calibrationBytes.isNotEmpty) {
      request.files.add(
        http.MultipartFile.fromBytes(
          'calibration_file',
          calibrationBytes,
          filename: calibrationFilename ?? 'calibration.json',
        ),
      );
    }
    final streamed = await _client.send(request);
    final response = await http.Response.fromStream(streamed);
    return _asMap(_decode(response));
  }

  Future<Map<String, dynamic>> uploadTrainingData({
    required String task,
    required String className,
    String? projectId,
    List<int>? pairBytes,
    String? pairFilename,
    List<int>? pplBytes,
    String? pplFilename,
    List<int>? xplBytes,
    String? xplFilename,
    List<int>? spectralBytes,
    String? spectralFilename,
  }) async {
    final path = task == 'spectral'
        ? '/training/spectral/upload'
        : '/training/thin_section/upload';
    final request = http.MultipartRequest('POST', _uri(path));
    final token = AuthService.instance.token;
    if (token != null && token.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $token';
    }
    request.fields['class_name'] = className;
    if (projectId != null && projectId.isNotEmpty) {
      request.fields['project_id'] = projectId;
    }

    if (task == 'spectral') {
      if (spectralBytes == null || spectralBytes.isEmpty) {
        throw const ApiException(400, 'Spectral file is required');
      }
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          spectralBytes,
          filename: spectralFilename ?? 'spectrum.npy',
        ),
      );
    } else {
      if (pairBytes != null && pairBytes.isNotEmpty) {
        request.files.add(
          http.MultipartFile.fromBytes(
            'pair_file',
            pairBytes,
            filename: pairFilename ?? 'pair.npy',
          ),
        );
      } else {
        if (pplBytes == null || xplBytes == null) {
          throw const ApiException(400, 'Provide pair_file or both ppl_file and xpl_file');
        }
        request.files.add(
          http.MultipartFile.fromBytes(
            'ppl_file',
            pplBytes,
            filename: pplFilename ?? 'ppl.png',
          ),
        );
        request.files.add(
          http.MultipartFile.fromBytes(
            'xpl_file',
            xplBytes,
            filename: xplFilename ?? 'xpl.png',
          ),
        );
      }
    }

    final streamed = await _client.send(request);
    final response = await http.Response.fromStream(streamed);
    return _asMap(_decode(response));
  }

  Future<Map<String, dynamic>> uploadInstrument({
    required String instrumentType,
    required List<int> fileBytes,
    required String filename,
  }) async {
    final request = http.MultipartRequest('POST', _uri('/instruments/upload'));
    final token = AuthService.instance.token;
    if (token != null && token.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $token';
    }
    request.fields['instrument_type'] = instrumentType;
    request.files.add(
      http.MultipartFile.fromBytes('file', fileBytes, filename: filename),
    );
    final streamed = await _client.send(request);
    final response = await http.Response.fromStream(streamed);
    return _asMap(_decode(response));
  }

  dynamic _decode(http.Response response) {
    final raw = response.body.isEmpty ? '{}' : response.body;
    final decoded = jsonDecode(raw);
    if (response.statusCode >= 400) {
      throw ApiException(
        response.statusCode,
        decoded is Map ? decoded.toString() : raw,
      );
    }
    return decoded;
  }

  Map<String, dynamic> _asMap(dynamic decoded) {
    if (decoded is Map<String, dynamic>) {
      return decoded;
    }
    return {'data': decoded};
  }

  void close() {
    _client.close();
  }
}