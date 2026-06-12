import 'dart:convert';

import 'package:flutter/material.dart';

import '../results/structured_json_view.dart';
import 'capture_chart.dart';
import 'data_table.dart';
import 'document_preview.dart';
import 'geo_point_map.dart';
import 'summary_cards.dart';

class CaptureResultView extends StatefulWidget {
  final Map<String, dynamic>? display;
  final Map<String, dynamic>? fallback;

  const CaptureResultView({
    super.key,
    this.display,
    this.fallback,
  });

  @override
  State<CaptureResultView> createState() => _CaptureResultViewState();
}

class _CaptureResultViewState extends State<CaptureResultView> {
  bool _showRaw = false;

  @override
  Widget build(BuildContext context) {
    final display = widget.display;
    final fallback = widget.fallback;

    if (display == null && fallback == null) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (display != null) ..._buildDisplay(context, display),
        if (fallback != null) ...[
          const SizedBox(height: 12),
          const Divider(),
          const SizedBox(height: 8),
          StructuredJsonView(
            data: fallback,
            title: 'Complete response',
          ),
          const SizedBox(height: 8),
          TextButton(
            onPressed: () => setState(() => _showRaw = !_showRaw),
            child: Text(_showRaw ? 'Hide raw JSON' : 'View raw JSON'),
          ),
          if (_showRaw)
            SelectableText(
              const JsonEncoder.withIndent('  ').convert(fallback),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
            ),
        ],
      ],
    );
  }

  List<Widget> _buildDisplay(BuildContext context, Map<String, dynamic> display) {
    final summary = display['summary'];
    final summaryMap = summary is Map<String, dynamic>
        ? summary
        : summary is Map
            ? Map<String, dynamic>.from(summary)
            : <String, dynamic>{};
    final displayType = display['display_type']?.toString() ?? 'table';
    final table = display['table'];
    final tables = display['tables'];
    final map = display['map'];
    final chart = display['chart'];
    final document = display['document'];

    return [
      if (summaryMap.isNotEmpty) SummaryCardGrid(summary: summaryMap),
      if (displayType == 'document' && document is Map) ...[
        const SizedBox(height: 12),
        DocumentPreview(
          title: '${summaryMap['title'] ?? 'Document'}',
          excerpt: '${document['excerpt'] ?? ''}',
          keywords: document['keywords'] is List ? document['keywords'] as List : null,
          pages: summaryMap['pages'] is int ? summaryMap['pages'] as int : null,
          sizeBytes: summaryMap['size_bytes'] is int
              ? summaryMap['size_bytes'] as int
              : null,
        ),
      ],
      if (map is Map && (map['features'] is List)) ...[
        const SizedBox(height: 12),
        Text('Spatial preview', style: Theme.of(context).textTheme.titleSmall),
        const SizedBox(height: 8),
        GeoPointMap(
          features: map['features'] as List,
          bounds: map['bounds'] is List ? map['bounds'] as List : null,
        ),
      ],
      if (chart is Map && chart['series'] is List) ...[
        const SizedBox(height: 12),
        CaptureChart(series: chart['series'] as List),
      ],
      if (table is Map && table['columns'] is List && table['rows'] is List)
        ..._tableSection(
          context,
          '${summaryMap['source'] ?? 'Data'}',
          table,
        ),
      if (tables is List)
        ...tables.whereType<Map>().map(
              (entry) => _tableSection(
                context,
                '${entry['source'] ?? 'Data'}',
                entry,
              ),
            ).expand((widgets) => widgets),
    ];
  }

  List<Widget> _tableSection(
    BuildContext context,
    String title,
    Map<dynamic, dynamic> table,
  ) {
    final columns = table['columns'];
    final rows = table['rows'];
    if (columns is! List || rows is! List || rows.isEmpty) {
      return [];
    }

    return [
      const SizedBox(height: 12),
      Text(title, style: Theme.of(context).textTheme.titleSmall),
      const SizedBox(height: 8),
      CaptureDataTable(
        columns: columns.map((c) => '$c').toList(),
        rows: rows
            .whereType<Map>()
            .map((row) => Map<String, dynamic>.from(row))
            .toList(),
      ),
    ];
  }
}