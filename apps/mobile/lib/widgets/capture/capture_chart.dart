import 'dart:math' as math;

import 'package:flutter/material.dart';

class CaptureChart extends StatelessWidget {
  final List<dynamic> series;

  const CaptureChart({super.key, required this.series});

  @override
  Widget build(BuildContext context) {
    final points = <_ChartPoint>[];
    for (final item in series) {
      if (item is! Map) continue;
      final value = item['value'];
      if (value is! num) continue;
      points.add(
        _ChartPoint(
          label: '${item['label'] ?? points.length + 1}',
          value: value.toDouble(),
        ),
      );
    }
    if (points.isEmpty) return const SizedBox.shrink();

    final maxValue = points.map((p) => p.value).reduce(math.max);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Value distribution', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 12),
            SizedBox(
              height: 180,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: points.map((point) {
                  final heightFactor = maxValue > 0 ? point.value / maxValue : 0.0;
                  return Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 2),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          Text(
                            point.value.toStringAsFixed(1),
                            style: const TextStyle(fontSize: 9),
                          ),
                          const SizedBox(height: 2),
                          Expanded(
                            child: Align(
                              alignment: Alignment.bottomCenter,
                              child: FractionallySizedBox(
                                heightFactor: heightFactor.clamp(0.05, 1.0),
                                child: Container(
                                  decoration: BoxDecoration(
                                    color: Colors.teal,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            point.label,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 9),
                          ),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ChartPoint {
  final String label;
  final double value;

  const _ChartPoint({required this.label, required this.value});
}