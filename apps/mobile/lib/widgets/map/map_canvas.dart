import 'dart:math' as math;

import 'package:flutter/material.dart';

class MapCanvas extends StatelessWidget {
  final List<Map<String, dynamic>> points;
  final List<String> activeLayers;
  final Map<String, dynamic>? featureLayers;

  const MapCanvas({
    super.key,
    required this.points,
    required this.activeLayers,
    this.featureLayers,
  });

  List<Map<String, dynamic>> _collectPoints() {
    final merged = <Map<String, dynamic>>[...points];
    final layers = featureLayers;
    if (layers == null) return merged;

    for (final layerId in activeLayers) {
      final layer = layers[layerId];
      if (layer is! Map) continue;
      final features = layer['features'];
      if (features is! List) continue;
      for (final feature in features.whereType<Map>()) {
        final geometry = feature['geometry'];
        if (geometry is! Map) continue;
        final coordinates = geometry['coordinates'];
        if (coordinates is! List || coordinates.length < 2) continue;
        final properties = feature['properties'];
        merged.add({
          'lon': coordinates[0],
          'lat': coordinates[1],
          if (properties is Map) ...Map<String, dynamic>.from(properties),
          'layer_id': layerId,
        });
      }
    }
    return merged;
  }

  @override
  Widget build(BuildContext context) {
    final plotted = _collectPoints();
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
                      .map(
                        (layer) => Chip(
                          label: Text(layer, style: const TextStyle(fontSize: 10)),
                          visualDensity: VisualDensity.compact,
                        ),
                      )
                      .toList(),
                ),
              ),
            SizedBox(
              height: 220,
              width: double.infinity,
              child: CustomPaint(
                painter: _MapCanvasPainter(points: plotted),
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

  Color _colorForPoint(Map<String, dynamic> point) {
    final layerId = '${point['layer_id'] ?? ''}';
    if (layerId.contains('borehole')) return Colors.lightBlueAccent;
    if (layerId.contains('deposit')) return Colors.deepOrange;
    final grade = point['ta_ppm'] ?? point['ta_ppm_mean'];
    if (grade is num && grade > 150) return Colors.orange;
    return Colors.teal;
  }

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
      canvas.drawCircle(Offset(x, y), 5, Paint()..color = _colorForPoint(point));
    }
  }

  @override
  bool shouldRepaint(covariant _MapCanvasPainter oldDelegate) => true;
}