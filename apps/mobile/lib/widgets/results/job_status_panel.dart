import 'package:flutter/material.dart';

import '../capture/capture_result_view.dart';

class JobStatusPanel extends StatelessWidget {
  final Map<String, dynamic>? job;
  final String title;

  const JobStatusPanel({
    super.key,
    required this.job,
    this.title = 'Job status',
  });

  @override
  Widget build(BuildContext context) {
    if (job == null) return const SizedBox.shrink();

    final status = '${job!['status'] ?? 'unknown'}';
    final display = job!['display'];
    final displayMap = display is Map<String, dynamic>
        ? display
        : display is Map
            ? Map<String, dynamic>.from(display)
            : null;
    final timeline = displayMap?['timeline'];
    final statusColor = status == 'complete'
        ? Colors.green
        : status == 'failed'
            ? Colors.red
            : Colors.orange;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(title, style: Theme.of(context).textTheme.titleSmall),
            const Spacer(),
            Chip(
              label: Text(status),
              backgroundColor: statusColor.withValues(alpha: 0.15),
              labelStyle: TextStyle(color: statusColor, fontSize: 12),
            ),
          ],
        ),
        if (timeline is List && timeline.isNotEmpty) ...[
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: timeline.whereType<Map>().map((step) {
              final done = step['done'] == true;
              return Chip(
                label: Text('${step['step'] ?? ''}', style: const TextStyle(fontSize: 11)),
                backgroundColor: done
                    ? Colors.teal.withValues(alpha: 0.15)
                    : null,
              );
            }).toList(),
          ),
        ],
        const SizedBox(height: 12),
        CaptureResultView(display: displayMap, fallback: job),
      ],
    );
  }
}