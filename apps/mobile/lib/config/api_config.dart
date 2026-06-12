class ApiConfig {
  /// Override at build/run time:
  /// `flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000`
  /// (Android emulator) or `http://localhost:8000` (desktop/web).
  static const String _envUrl = String.fromEnvironment('API_BASE_URL');

  static String get baseUrl {
    if (_envUrl.isNotEmpty) {
      return _envUrl;
    }
    return 'http://localhost:8000';
  }
}