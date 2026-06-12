import 'package:shared_preferences/shared_preferences.dart';

class ProjectStore {
  ProjectStore._();

  static final ProjectStore instance = ProjectStore._();

  static const _projectKey = 'terraforge_selected_project';

  String _selectedProjectId = 'matuu';

  String get selectedProjectId => _selectedProjectId;

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    _selectedProjectId = prefs.getString(_projectKey) ?? 'matuu';
  }

  Future<void> select(String projectId) async {
    _selectedProjectId = projectId;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_projectKey, projectId);
  }
}