import 'package:flutter/material.dart';

import '../capture/capture_chart.dart';
import '../capture/data_table.dart';
import 'infer_display.dart';

class ClassificationResultView extends StatelessWidget {
  final Map<String, dynamic> result;
  final String title;

  const ClassificationResultView({
    super.key,
    required this.result,
    this.title = 'Classification',
  });

  @override
  Widget build(BuildContext context) {
    final display = inferDisplay(result);
    final label = result['label'] ?? result['species'];
    final confidence = result['confidence'];
    final top3 = result['top3'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.titleMedium),
        if (label != null) ...[
          const SizedBox(height: 12),
          Card(
            child: ListTile(
              leading: CircleAvatar(
                child: Text('${(confidence is num ? (confidence * 100) : 0).toStringAsFixed(0)}%'),
              ),
              title: Text('$label', style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text(
                [
                  if (result['mineral_affinity'] != null)
                    'Affinity: ${result['mineral_affinity']}',
                  if (result['recommended_action'] != null)
                    'Action: ${result['recommended_action']}',
                  if (result['accelerator'] != null) 'Via ${result['accelerator']}',
                  if (result['model'] != null) 'Model: ${result['model']}',
                ].join(' · '),
              ),
            ),
          ),
        ],
        if (top3 is List && top3.isNotEmpty) ...[
          const SizedBox(height: 12),
          Text('Top predictions', style: Theme.of(context).textTheme.titleSmall),
          ...top3.take(3).map((entry) {
            if (entry is! Map && entry is! List) return const SizedBox.shrink();
            final name = entry is Map ? entry['label'] ?? entry['species'] : entry[0];
            final score = entry is Map ? entry['confidence'] ?? entry['score'] : entry[1];
            return ListTile(
              dense: true,
              title: Text('$name'),
              trailing: Text(
                score is num ? '${(score * 100).toStringAsFixed(1)}%' : '$score',
              ),
            );
          }),
        ],
        if (display != null) ...[
          const SizedBox(height: 8),
          if (display['chart']?['series'] is List)
            CaptureChart(series: display['chart']['series'] as List),
          if (display['table']?['rows'] is List &&
              display['table']?['columns'] is List)
            CaptureDataTable(
              columns: (display['table']['columns'] as List).map((c) => '$c').toList(),
              rows: (display['table']['rows'] as List)
                  .whereType<Map>()
                  .map((r) => Map<String, dynamic>.from(r))
                  .toList(),
            ),
        ],
      ],
    );
  }
}