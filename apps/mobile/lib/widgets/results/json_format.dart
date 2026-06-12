import 'dart:convert';

String formatJsonLabel(String key) {
  return key.replaceAll('_', ' ').replaceAll('-', ' ');
}

String formatJsonValue(dynamic value, {int maxLength = 240}) {
  if (value == null) return '—';
  if (value is bool) return value ? 'yes' : 'no';
  if (value is num || value is String) {
    final text = value.toString();
    if (text.length <= maxLength) return text;
    return '${text.substring(0, maxLength)}…';
  }
  if (value is List) {
    if (value.isEmpty) return '[]';
    if (value.every((item) => item is num || item is String || item is bool)) {
      return value.map((item) => formatJsonValue(item, maxLength: 80)).join(', ');
    }
    return '[${value.length} items]';
  }
  if (value is Map) {
    return '{${value.length} fields}';
  }
  return value.toString();
}

String formatJsonValueDetailed(dynamic value) {
  if (value is Map || value is List) {
    return const JsonEncoder.withIndent('  ').convert(value);
  }
  return formatJsonValue(value);
}

List<String> unionTableColumns(Iterable<Map> rows) {
  final columns = <String>[];
  for (final row in rows) {
    for (final key in row.keys) {
      final name = '$key';
      if (!columns.contains(name)) columns.add(name);
    }
  }
  return columns;
}

bool isScalar(dynamic value) {
  return value == null ||
      value is String ||
      value is num ||
      value is bool;
}

bool isMapList(dynamic value) {
  return value is List &&
      value.isNotEmpty &&
      value.every((item) => item is Map);
}