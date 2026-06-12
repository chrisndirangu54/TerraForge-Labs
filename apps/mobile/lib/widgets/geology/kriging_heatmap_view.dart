import 'dart:math' as math;

import 'package:flutter/material.dart';

class KrigingHeatmapView extends StatelessWidget {
  final Map<String, dynamic>? stats;
  final String? previewUrl;

  const KrigingHeatmapView({
    super.key,
    this.stats,
    this.previewUrl,
  });

  @override
  Widget build(BuildContext context) {
    final bounds = stats?['bounds'];
    final mean = (stats?['mean'] as num?)?.toDouble();
    final min = (stats?['min'] as num?)?.toDouble();
    final max = (stats?['max'] as num?)?.toDouble();
    final nPoints = stats?['n_points_used'];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Grade interpolation', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            if (previewUrl != null && previewUrl!.isNotEmpty)
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.network(
                  previewUrl!,
                  height: 180,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => _syntheticHeatmap(min, max, mean),
                ),
              )
            else
              _syntheticHeatmap(min, max, mean),
            const SizedBox(height: 8),
            Wrap(
              spacing: 12,
              children: [
                if (mean != null) _chip('Mean', mean.toStringAsFixed(1)),
                if (min != null && max != null)
                  _chip('Range', '${min.toStringAsFixed(0)}–${max.toStringAsFixed(0)}'),
                if (nPoints != null) _chip('Points', '$nPoints'),
              ],
            ),
            if (bounds is List && bounds.length >= 4)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  'Bounds: [${bounds.map((v) => (v as num).toStringAsFixed(3)).join(', ')}]',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _syntheticHeatmap(double? min, double? max, double? mean) {
    return SizedBox(
      height: 180,
      child: CustomPaint(
        painter: _SyntheticHeatmapPainter(
          min: min ?? 80,
          max: max ?? 180,
          mean: mean ?? 120,
        ),
        child: const SizedBox.expand(),
      ),
    );
  }

  Widget _chip(String label, String value) {
    return Chip(
      label: Text('$label: $value', style: const TextStyle(fontSize: 11)),
      visualDensity: VisualDensity.compact,
    );
  }
}

class _SyntheticHeatmapPainter extends CustomPainter {
  final double min;
  final double max;
  final double mean;

  _SyntheticHeatmapPainter({
    required this.min,
    required this.max,
    required this.mean,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final rng = math.Random(42);
    for (var y = 0; y < size.height.toInt(); y += 6) {
      for (var x = 0; x < size.width.toInt(); x += 6) {
        final noise = rng.nextDouble();
        final dist = ((x / size.width) - 0.55).abs() + ((y / size.height) - 0.45).abs();
        final value = math.max(min, math.min(max, mean + (0.35 - dist) * 80 + noise * 20));
        final t = (value - min) / math.max(max - min, 1);
        final paint = Paint()..color = Color.lerp(Colors.blue.shade100, Colors.red.shade400, t)!;
        canvas.drawRect(Rect.fromLTWH(x.toDouble(), y.toDouble(), 6, 6), paint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _SyntheticHeatmapPainter oldDelegate) => false;
}