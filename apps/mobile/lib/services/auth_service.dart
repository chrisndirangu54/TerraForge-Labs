class AuthService {
  AuthService._();

  static final AuthService instance = AuthService._();

  String? _token;
  Map<String, dynamic>? _user;

  String? get token => _token;
  Map<String, dynamic>? get user => _user;
  bool get isAuthenticated => _token != null;

  void setSession({
    required String token,
    required Map<String, dynamic> user,
  }) {
    _token = token;
    _user = user;
  }

  void clear() {
    _token = null;
    _user = null;
  }
}