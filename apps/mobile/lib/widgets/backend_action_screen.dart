import 'dart:convert';

import 'package:flutter/material.dart';

typedef BackendAction = Future<Map<String, dynamic>> Function();

class BackendActionScreen extends StatefulWidget {
  final String title;
  final String description;
  final String actionLabel;
  final BackendAction onAction;

  const BackendActionScreen({
    super.key,
    required this.title,
    required this.description,
    required this.actionLabel,
    required this.onAction,
  });

  @override
  State<BackendActionScreen> createState() => _BackendActionScreenState();
}

class _BackendActionScreenState extends State<BackendActionScreen> {
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;

  Future<void> _run() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await widget.onAction();
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
      appBar: AppBar(title: Text(widget.title)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(widget.description),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _run,
            child: Text(_loading ? 'Loading...' : widget.actionLabel),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_result != null) ...[
            const SizedBox(height: 16),
            SelectableText(
              const JsonEncoder.withIndent('  ').convert(_result),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }
}