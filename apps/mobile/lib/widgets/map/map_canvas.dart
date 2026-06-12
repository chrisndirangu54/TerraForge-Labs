import 'dart:math' as math;

import 'package:flutter/material.dart';

class MapCanvas extends StatelessWidget {
  final List<Map<String, dynamic>> points;
  final List<String> activeLayers;

  const MapCanvas({
    super.key,
    required this.points,
    required this.activeLayers,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Mission map', style: Theme.of(context).textTheme.titleSmall),
            if (activeLayers.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Wrap(
                  spacing: 6,
                  children: activeLayers
                      .take(4)
                      .map((layer) => Chip(
                            label: Text(layer, style: const TextStyle(fontSize: 10)),
                            visualDensity: VisualDensity.compact,
                          ))
                      .toList(),
                ),
              ),
            SizedBox(
              height: 220,
              width: double.infinity,
              child: CustomPaint(
                painter: _MapCanvasPainter(points: points),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MapCanvasPainter extends CustomPainter {
  final List<Map<String, dynamic>> points;

  _MapCanvasPainter({required this.points});

  @override
  void paint(Canvas canvas, Size size) {
    final grid = Paint()
      ..color = Colors.teal.withValues(alpha: 0.06)
      ..strokeWidth = 1;
    for (var x = 0.0; x < size.width; x += 20) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), grid);
    }
    for (var y = 0.0; y < size.height; y += 20) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), grid);
    }

    if (points.isEmpty) {
      final text = TextPainter(
        text: const TextSpan(
          text: 'Matuu project AOI',
          style: TextStyle(color: Colors.grey, fontSize: 12),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      text.paint(canvas, Offset(size.width / 2 - text.width / 2, size.height / 2));
      return;
    }

    final lons = points.map((p) => (p['lon'] as num).toDouble()).toList();
    final lats = points.map((p) => (p['lat'] as num).toDouble()).toList();
    final west = lons.reduce(math.min) - 0.01;
    final east = lons.reduce(math.max) + 0.01;
    final south = lats.reduce(math.min) - 0.01;
    final north = lats.reduce(math.max) + 0.01;

    for (final point in points) {
      final lon = (point['lon'] as num).toDouble();
      final lat = (point['lat'] as num).toDouble();
      final x = ((lon - west) / (east - west)) * (size.width - 40) + 20;
      final y = size.height - (((lat - south) / (north - south)) * (size.height - 40) + 20);
      canvas.drawCircle(Offset(x, y), 5, Paint()..color = Colors.teal);
    }
  }

  @override
  bool shouldRepaint(covariant _MapCanvasPainter oldDelegate) => true;
}