import 'dart:convert';

import 'package:flutter/material.dart';

class CopilotAnswerView extends StatefulWidget {
  final Map<String, dynamic> answer;

  const CopilotAnswerView({super.key, required this.answer});

  @override
  State<CopilotAnswerView> createState() => _CopilotAnswerViewState();
}

class _CopilotAnswerViewState extends State<CopilotAnswerView> {
  bool _showRaw = false;

  @override
  Widget build(BuildContext context) {
    final text = widget.answer['answer'] ??
        widget.answer['response'] ??
        widget.answer['text'];
    final citations = widget.answer['citations'];
    final provider = widget.answer['provider'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (provider != null)
          Chip(
            label: Text('Provider: $provider', style: const TextStyle(fontSize: 11)),
          ),
        if (text != null) ...[
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: SelectableText('$text'),
            ),
          ),
        ],
        if (citations is List && citations.isNotEmpty) ...[
          const SizedBox(height: 12),
          Text('Sources', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          ...citations.whereType<Map>().map((cite) {
            return ListTile(
              dense: true,
              leading: const Icon(Icons.article_outlined, size: 18),
              title: Text('${cite['title'] ?? cite['source'] ?? 'Source'}'),
              subtitle: cite['snippet'] != null ? Text('${cite['snippet']}') : null,
            );
          }),
        ],
        const SizedBox(height: 8),
        TextButton(
          onPressed: () => setState(() => _showRaw = !_showRaw),
          child: Text(_showRaw ? 'Hide raw JSON' : 'Show raw JSON'),
        ),
        if (_showRaw)
          SelectableText(
            const JsonEncoder.withIndent('  ').convert(widget.answer),
            style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
          ),
      ],
    );
  }
}