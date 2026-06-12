import 'package:flutter/material.dart';

import '../results/json_format.dart';

class SummaryCard extends StatelessWidget {
  final String label;
  final String value;
  final Color? accent;

  const SummaryCard({
    super.key,
    required this.label,
    required this.value,
    this.accent,
  });

  @override
  Widget build(BuildContext context) {
    final color = accent ?? Theme.of(context).colorScheme.primary;
    return Card(
      child: Container(
        decoration: BoxDecoration(
          border: Border(left: BorderSide(color: color, width: 3)),
        ),
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: Theme.of(context).textTheme.labelSmall),
            const SizedBox(height: 4),
            Text(
              value,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

class SummaryCardGrid extends StatelessWidget {
  final Map<String, dynamic> summary;

  const SummaryCardGrid({super.key, required this.summary});

  @override
  Widget build(BuildContext context) {
    final cards = <Widget>[];

    for (final entry in summary.entries) {
      final value = entry.value;
      if (isScalar(value)) {
        cards.add(
          SummaryCard(
            label: formatJsonLabel(entry.key),
            value: formatJsonValue(value),
            accent: _accentFor(entry.key),
          ),
        );
      }
    }

    if (cards.isEmpty) return const SizedBox.shrink();

    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: cards.map((card) => SizedBox(width: 160, child: card)).toList(),
    );
  }

  Color? _accentFor(String key) {
    switch (key) {
      case 'flagged':
        return Colors.orange;
      case 'transport':
        return Colors.teal;
      case 'confidence':
        return Colors.green;
      default:
        return null;
    }
  }
}