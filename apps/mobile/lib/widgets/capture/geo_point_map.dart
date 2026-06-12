import 'dart:math' as math;

import 'package:flutter/material.dart';

class GeoPointMap extends StatelessWidget {
  final List<dynamic> features;
  final List<dynamic>? bounds;

  const GeoPointMap({
    super.key,
    required this.features,
    this.bounds,
  });

  @override
  Widget build(BuildContext context) {
    final points = <_MapPoint>[];
    for (final feature in features) {
      if (feature is! Map) continue;
      final geometry = feature['geometry'];
      if (geometry is! Map || geometry['type'] != 'Point') continue;
      final coords = geometry['coordinates'];
      if (coords is! List || coords.length < 2) continue;
      final props = feature['properties'];
      points.add(
        _MapPoint(
          lon: (coords[0] as num).toDouble(),
          lat: (coords[1] as num).toDouble(),
          label: props is Map
              ? '${props['sample_id'] ?? props['point_id'] ?? ''}'
              : '',
          flagged: props is Map && props['flagged'] == true,
        ),
      );
    }

    if (points.isEmpty) {
      return const Text('No georeferenced points in this capture.');
    }

    final west = bounds != null && bounds!.length >= 4
        ? (bounds![0] as num).toDouble()
        : points.map((p) => p.lon).reduce(math.min) - 0.01;
    final south = bounds != null && bounds!.length >= 4
        ? (bounds![1] as num).toDouble()
        : points.map((p) => p.lat).reduce(math.min) - 0.01;
    final east = bounds != null && bounds!.length >= 4
        ? (bounds![2] as num).toDouble()
        : points.map((p) => p.lon).reduce(math.max) + 0.01;
    final north = bounds != null && bounds!.length >= 4
        ? (bounds![3] as num).toDouble()
        : points.map((p) => p.lat).reduce(math.max) + 0.01;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              height: 220,
              width: double.infinity,
              child: CustomPaint(
                painter: _PointMapPainter(
                  points: points,
                  west: west,
                  south: south,
                  east: east,
                  north: north,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '${points.length} points · bounds '
              '[${west.toStringAsFixed(3)}, ${south.toStringAsFixed(3)}, '
              '${east.toStringAsFixed(3)}, ${north.toStringAsFixed(3)}]',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class _MapPoint {
  final double lon;
  final double lat;
  final String label;
  final bool flagged;

  const _MapPoint({
    required this.lon,
    required this.lat,
    required this.label,
    required this.flagged,
  });
}

class _PointMapPainter extends CustomPainter {
  final List<_MapPoint> points;
  final double west;
  final double south;
  final double east;
  final double north;

  _PointMapPainter({
    required this.points,
    required this.west,
    required this.south,
    required this.east,
    required this.north,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final gridPaint = Paint()
      ..color = Colors.teal.withValues(alpha: 0.08)
      ..strokeWidth = 1;
    for (var x = 0.0; x < size.width; x += 24) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), gridPaint);
    }
    for (var y = 0.0; y < size.height; y += 24) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    const pad = 24.0;
    final lonSpan = math.max(east - west, 0.0001);
    final latSpan = math.max(north - south, 0.0001);

    for (final point in points) {
      final x = pad + ((point.lon - west) / lonSpan) * (size.width - pad * 2);
      final y = size.height -
          pad -
          ((point.lat - south) / latSpan) * (size.height - pad * 2);
      final fill = point.flagged ? Colors.orange : Colors.teal;
      canvas.drawCircle(Offset(x, y), 5, Paint()..color = fill);
      canvas.drawCircle(
        Offset(x, y),
        5,
        Paint()
          ..color = Colors.white
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _PointMapPainter oldDelegate) => true;
}