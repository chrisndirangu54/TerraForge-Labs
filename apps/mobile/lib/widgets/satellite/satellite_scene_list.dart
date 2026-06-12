import 'package:flutter/material.dart';

import '../capture/data_table.dart';

class SatelliteSceneList extends StatelessWidget {
  final List<dynamic> scenes;
  final List<dynamic>? indices;

  const SatelliteSceneList({
    super.key,
    required this.scenes,
    this.indices,
  });

  @override
  Widget build(BuildContext context) {
    if (scenes.isEmpty) {
      return const Text('No satellite scenes in catalogue.');
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (indices != null && indices!.isNotEmpty) ...[
          Wrap(
            spacing: 6,
            children: indices!
                .map((idx) => Chip(label: Text('$idx', style: const TextStyle(fontSize: 11))))
                .toList(),
          ),
          const SizedBox(height: 12),
        ],
        ...scenes.whereType<Map>().map((scene) {
          final source = '${scene['source'] ?? 'unknown'}';
          return Card(
            child: ListTile(
              leading: Icon(_iconFor(source), color: _colorFor(source)),
              title: Text('${scene['scene_id'] ?? scene['date'] ?? source}'),
              subtitle: Text(_subtitle(scene)),
              trailing: scene['cloud_cover_pct'] != null
                  ? Chip(
                      label: Text('${scene['cloud_cover_pct']}% cloud',
                          style: const TextStyle(fontSize: 10)),
                    )
                  : null,
            ),
          );
        }),
      ],
    );
  }

  String _subtitle(Map scene) {
    final parts = <String>[scene['source']?.toString() ?? '', scene['date']?.toString() ?? ''];
    if (scene['ndvi_mean'] != null) parts.add('NDVI ${scene['ndvi_mean']}');
    if (scene['lst_mean_c'] != null) parts.add('LST ${scene['lst_mean_c']}°C');
    if (scene['coherence'] != null) parts.add('coh ${scene['coherence']}');
    return parts.where((p) => p.isNotEmpty).join(' · ');
  }

  IconData _iconFor(String source) {
    switch (source) {
      case 'sentinel2':
        return Icons.satellite_alt;
      case 'sar':
        return Icons.radar;
      case 'landsat_thermal':
      case 'modis_thermal':
        return Icons.thermostat;
      default:
        return Icons.public;
    }
  }

  Color _colorFor(String source) {
    switch (source) {
      case 'sentinel2':
        return Colors.green;
      case 'sar':
        return Colors.indigo;
      default:
        return Colors.orange;
    }
  }
}

class SatelliteInsarPanel extends StatelessWidget {
  final Map<String, dynamic> insar;

  const SatelliteInsarPanel({super.key, required this.insar});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('InSAR displacement', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            ListTile(
              dense: true,
              leading: const Icon(Icons.waves),
              title: Text('Job ${insar['job_id'] ?? 'n/a'}'),
              subtitle: Text(
                'Alert threshold: ${insar['alert_threshold_mm'] ?? 'n/a'} mm',
              ),
            ),
            if (insar['displacement_raster_url'] != null)
              Text('${insar['displacement_raster_url']}',
                  style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }
}

class DrillLogPreviewTable extends StatelessWidget {
  final List<dynamic> holes;

  const DrillLogPreviewTable({super.key, required this.holes});

  @override
  Widget build(BuildContext context) {
    final rows = holes.whereType<Map>().map((hole) => Map<String, dynamic>.from(hole)).toList();
    if (rows.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Drill hole preview', style: Theme.of(context).textTheme.titleSmall),
        const SizedBox(height: 8),
        CaptureDataTable(
          columns: const [
            'hole_id', 'depth_m', 'mean_ta_ppm', 'lithology', 'dip', 'azimuth',
          ],
          rows: rows,
        ),
      ],
    );
  }
}