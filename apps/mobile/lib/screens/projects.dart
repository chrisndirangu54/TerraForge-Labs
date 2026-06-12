import 'package:flutter/material.dart';

import '../services/project_store.dart';
import '../services/terraforge_api.dart';

class ProjectsScreen extends StatefulWidget {
  const ProjectsScreen({super.key});

  @override
  State<ProjectsScreen> createState() => _ProjectsScreenState();
}

class _ProjectsScreenState extends State<ProjectsScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  bool _loading = true;
  String? _error;
  List<dynamic> _projects = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final projects = await _api.listProjects();
      setState(() {
        _projects = projects;
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _select(String projectId) async {
    await ProjectStore.instance.select(projectId);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Selected project: $projectId')),
    );
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final selected = ProjectStore.instance.selectedProjectId;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Projects'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : ListView.builder(
                  itemCount: _projects.length,
                  itemBuilder: (context, index) {
                    final project = _projects[index] as Map;
                    final id = project['id']?.toString() ?? '';
                    final name = project['name']?.toString() ?? id;
                    final isSelected = id == selected;
                    return ListTile(
                      title: Text(name),
                      subtitle: Text(id),
                      trailing: isSelected ? const Icon(Icons.check_circle) : null,
                      selected: isSelected,
                      onTap: () => _select(id),
                    );
                  },
                ),
    );
  }
}