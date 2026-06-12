import 'package:flutter/material.dart';

import '../services/terraforge_api.dart';
import '../widgets/results/copilot_answer_view.dart';

class CopilotScreen extends StatefulWidget {
  const CopilotScreen({super.key});

  @override
  State<CopilotScreen> createState() => _CopilotScreenState();
}

class _CopilotScreenState extends State<CopilotScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  final _queryController = TextEditingController(
    text: 'Summarize the Matuu Ta exploration status and next drill targets.',
  );
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _status;
  Map<String, dynamic>? _answer;

  @override
  void initState() {
    super.initState();
    _loadStatus();
  }

  Future<void> _loadStatus() async {
    try {
      final status = await _api.copilotStatus();
      setState(() => _status = status);
    } catch (_) {}
  }

  Future<void> _query() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final answer = await _api.copilotQuery(query: _queryController.text.trim());
      setState(() {
        _answer = answer;
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
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Copilot')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_status != null)
            Card(
              child: ListTile(
                leading: Icon(
                  _status!['active'] == true ? Icons.check_circle : Icons.pause_circle,
                  color: _status!['active'] == true ? Colors.green : Colors.grey,
                ),
                title: Text('${_status!['provider'] ?? 'LLM provider'}'),
                subtitle: Text(
                  _status!['active'] == true ? 'Copilot is active' : 'Copilot is offline',
                ),
              ),
            ),
          const SizedBox(height: 16),
          TextField(
            controller: _queryController,
            decoration: const InputDecoration(
              labelText: 'Ask TerraForge Copilot',
              border: OutlineInputBorder(),
            ),
            maxLines: 3,
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _query,
            child: Text(_loading ? 'Thinking...' : 'Send Query'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_answer != null) ...[
            const SizedBox(height: 16),
            CopilotAnswerView(answer: _answer!),
          ],
        ],
      ),
    );
  }
}