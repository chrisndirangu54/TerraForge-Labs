import 'json_format.dart';

Map<String, dynamic>? inferDisplay(dynamic value) {
  if (value == null) return null;

  if (value is Map<String, dynamic>) {
    final display = value['display'];
    if (display is Map<String, dynamic>) return display;
    if (display is Map) return Map<String, dynamic>.from(display);

    for (final key in _classificationKeys) {
      if (value.containsKey(key)) return _classificationDisplay(value);
    }

    final sections = <Map<String, dynamic>>[];
    for (final key in _listKeys) {
      final items = value[key];
      if (isMapList(items)) {
        sections.add(_listTable(items.cast<Map>(), key));
      }
    }

    if (value['layer_groups'] is Map) {
      final groups = value['layer_groups'] as Map;
      final rows = groups.entries
          .map(
            (entry) => {
              'group': entry.key,
              'layers': (entry.value as List).join(', '),
            },
          )
          .toList();
      sections.add(_listTable(rows, 'layer_groups'));
    }

    final scalar = _scalarTable(value);
    if (scalar != null) sections.add(scalar);

    if (sections.isEmpty) return null;
    if (sections.length == 1) return sections.first;
    return _mergeSections(sections, value);
  }

  if (value is List && value.isNotEmpty && value.first is Map) {
    return _listTable(value.cast<Map>(), 'items');
  }

  return null;
}

const _listKeys = [
  'items',
  'records',
  'boreholes',
  'drill_log_preview',
  'blocks_preview',
  'scenes',
  'catalogs',
  'devices',
  'results',
  'layers',
  'settlements',
  'features',
  'packs',
  'categories',
  'timeline',
  'alerts',
  'recent_jobs',
  'jobs',
  'observations',
  'sessions',
  'uploads',
];

const _classificationKeys = [
  'label',
  'species',
  'confidence',
  'top3',
  'top_k',
  'classes',
];

Map<String, dynamic>? _scalarTable(Map<String, dynamic> record) {
  final rows = <Map<String, dynamic>>[];
  for (final entry in record.entries) {
    if (entry.key == 'display') continue;
    rows.add({
      'field': entry.key,
      'value': formatJsonValue(entry.value),
    });
  }
  if (rows.isEmpty) return null;
  return {
    'display_type': 'table',
    'summary': {'fields': rows.length},
    'table': {
      'columns': ['field', 'value'],
      'rows': rows,
    },
  };
}

Map<String, dynamic> _mergeSections(
  List<Map<String, dynamic>> sections,
  Map<String, dynamic> source,
) {
  final tables = sections
      .where((section) => section['table'] is Map)
      .map((section) => section['table'] as Map<String, dynamic>)
      .toList();

  final mapSection = sections.firstWhere(
    (section) => section['map'] is Map,
    orElse: () => <String, dynamic>{},
  );

  return {
    'display_type': 'mixed',
    'summary': {
      'sections': sections.length,
      if (source['count'] != null) 'count': source['count'],
    },
    'tables': tables,
    if (mapSection['map'] != null) 'map': mapSection['map'],
  };
}

Map<String, dynamic> _listTable(List<Map> rows, String source) {
  final columns = unionTableColumns(rows);
  final tableRows = rows
      .map((row) => {for (final col in columns) col: row[col]})
      .toList();

  final display = <String, dynamic>{
    'display_type': 'table',
    'summary': {'rows': rows.length, 'source': source},
    'table': {
      'columns': columns,
      'rows': tableRows,
      'source': source,
    },
  };

  final geoRows = rows.where(
    (row) => row['lon'] != null && row['lat'] != null,
  );
  if (geoRows.isNotEmpty) {
    display['display_type'] = 'mixed';
    display['map'] = {
      'features': geoRows
          .map(
            (row) => {
              'geometry': {
                'type': 'Point',
                'coordinates': [row['lon'], row['lat']],
              },
              'properties': row,
            },
          )
          .toList(),
    };
  }
  return display;
}

Map<String, dynamic> _classificationDisplay(Map<String, dynamic> record) {
  final label = record['label'] ?? record['species'];
  final confidence = record['confidence'] ?? record['model_confidence'];
  final top = record['top3'] ?? record['top_k'] ?? record['classes'];

  final rows = <Map<String, dynamic>>[];
  if (top is List) {
    for (final entry in top) {
      if (entry is Map) {
        rows.add(Map<String, dynamic>.from(entry));
      } else if (entry is List && entry.length >= 2) {
        rows.add({'label': entry[0], 'confidence': entry[1]});
      }
    }
  }
  if (rows.isEmpty) {
    rows.add({'label': label, 'confidence': confidence});
  }

  final series = rows
      .where((row) => row['confidence'] != null || row['score'] != null)
      .map(
        (row) => {
          'label': '${row['label'] ?? row['species'] ?? ''}',
          'value': (row['confidence'] ?? row['score'] ?? 0) as num,
        },
      )
      .toList();
  if (series.isEmpty && confidence != null) {
    series.add({'label': '$label', 'value': confidence});
  }

  final extraScalars = <String, dynamic>{};
  for (final entry in record.entries) {
    if (_classificationKeys.contains(entry.key)) continue;
    if (entry.key == 'display') continue;
    extraScalars[entry.key] = entry.value;
  }

  return {
    'display_type': 'chart',
    'summary': {
      if (label != null) 'label': label,
      if (confidence != null) 'confidence': confidence,
      if (record['accelerator'] != null) 'accelerator': record['accelerator'],
      if (record['model'] != null) 'model': record['model'],
      if (record['task'] != null) 'task': record['task'],
      ...extraScalars.map((key, value) => MapEntry(key, formatJsonValue(value))),
    },
    'chart': {'series': series},
    'table': {
      'columns': rows.isNotEmpty ? unionTableColumns(rows) : ['label', 'confidence'],
      'rows': rows,
    },
  };
}