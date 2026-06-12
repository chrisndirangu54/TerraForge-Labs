import 'dart:math' as math;

import 'package:flutter/material.dart';

class DepositModelViewer extends StatelessWidget {
  final List<Map<String, dynamic>> blocks;
  final double? meanGrade;

  const DepositModelViewer({
    super.key,
    required this.blocks,
    this.meanGrade,
  });

  @override
  Widget build(BuildContext context) {
    if (blocks.isEmpty) {
      return const Card(
        child: SizedBox(
          height: 220,
          child: Center(child: Text('No block model data to display.')),
        ),
      );
    }

    final grades = blocks
        .map((b) => (b['ta_ppm_mean'] as num?)?.toDouble() ?? 0)
        .toList();
    final minGrade = grades.reduce(math.min);
    final maxGrade = grades.reduce(math.max);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('3D block model', style: Theme.of(context).textTheme.titleSmall),
            if (meanGrade != null)
              Text(
                'Mean grade: ${meanGrade!.toStringAsFixed(1)} ppm Ta',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            const SizedBox(height: 8),
            SizedBox(
              height: 240,
              width: double.infinity,
              child: CustomPaint(
                painter: _IsometricBlockPainter(
                  blocks: blocks,
                  minGrade: minGrade,
                  maxGrade: maxGrade,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                _legendSwatch(Colors.blue.shade200, 'Low'),
                const SizedBox(width: 12),
                _legendSwatch(Colors.orange, 'High'),
                const Spacer(),
                Text('${blocks.length} blocks', style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _legendSwatch(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 14, height: 14, color: color),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 11)),
      ],
    );
  }
}

class _IsometricBlockPainter extends CustomPainter {
  final List<Map<String, dynamic>> blocks;
  final double minGrade;
  final double maxGrade;

  _IsometricBlockPainter({
    required this.blocks,
    required this.minGrade,
    required this.maxGrade,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final xs = blocks.map((b) => (b['x'] as num?)?.toDouble() ?? 0).toList();
    final ys = blocks.map((b) => (b['y'] as num?)?.toDouble() ?? 0).toList();
    final minX = xs.reduce(math.min);
    final maxX = xs.reduce(math.max);
    final minY = ys.reduce(math.min);
    final maxY = ys.reduce(math.max);
    final spanX = math.max(maxX - minX, 1);
    final spanY = math.max(maxY - minY, 1);

    const tileW = 18.0;
    const tileH = 10.0;

    final sorted = [...blocks]..sort(
        (a, b) => ((a['z'] as num?) ?? 0).compareTo((b['z'] as num?) ?? 0),
      );

    for (final block in sorted) {
      final x = ((block['x'] as num?)?.toDouble() ?? 0) - minX;
      final y = ((block['y'] as num?)?.toDouble() ?? 0) - minY;
      final z = (block['z'] as num?)?.toDouble() ?? 0;
      final grade = (block['ta_ppm_mean'] as num?)?.toDouble() ?? minGrade;
      final t = maxGrade > minGrade ? (grade - minGrade) / (maxGrade - minGrade) : 0.5;

      final originX = size.width * 0.15 + (x / spanX) * (size.width * 0.55);
      final originY = size.height * 0.75 - (y / spanY) * (size.height * 0.45) - z * 8;

      final color = Color.lerp(Colors.blue.shade200, Colors.orange, t)!;
      _drawIsoCube(canvas, Offset(originX, originY), tileW, tileH, color);
    }
  }

  void _drawIsoCube(Canvas canvas, Offset origin, double w, double h, Color color) {
    final top = origin + Offset(0, -h);
    final right = origin + Offset(w * 0.6, -h * 0.35);
    final front = origin + Offset(0, h * 0.5);
    final paint = Paint()..color = color;
    final side = Paint()..color = Color.lerp(color, Colors.black, 0.15)!;
    final topPaint = Paint()..color = Color.lerp(color, Colors.white, 0.2)!;

    final path = Path()
      ..moveTo(origin.dx, origin.dy)
      ..lineTo(right.dx, right.dy)
      ..lineTo(right.dx, right.dy + h * 0.5)
      ..lineTo(origin.dx, origin.dy + h * 0.5)
      ..close();
    canvas.drawPath(path, side);

    final topPath = Path()
      ..moveTo(origin.dx, origin.dy)
      ..lineTo(top.dx, top.dy)
      ..lineTo(right.dx, right.dy)
      ..lineTo(origin.dx, origin.dy)
      ..close();
    canvas.drawPath(topPath, topPaint);

    final frontPath = Path()
      ..moveTo(origin.dx, origin.dy)
      ..lineTo(front.dx, front.dy)
      ..lineTo(front.dx + w * 0.6, front.dy - h * 0.35)
      ..lineTo(right.dx, right.dy)
      ..close();
    canvas.drawPath(frontPath, paint);
  }

  @override
  bool shouldRepaint(covariant _IsometricBlockPainter oldDelegate) => true;
}