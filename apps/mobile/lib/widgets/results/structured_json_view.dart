import 'package:flutter/material.dart';

import '../capture/data_table.dart';
import '../capture/summary_cards.dart';
import 'json_format.dart';

class StructuredJsonView extends StatelessWidget {
  final dynamic data;
  final String? title;
  final int depth;

  const StructuredJsonView({
    super.key,
    required this.data,
    this.title,
    this.depth = 0,
  });

  @override
  Widget build(BuildContext context) {
    if (data == null) {
      return const Text('No data returned.');
    }
    return _buildNode(context, data, title: title);
  }

  Widget _buildNode(BuildContext context, dynamic node, {String? title}) {
    if (isScalar(node)) {
      return _scalarTile(context, title ?? 'value', node);
    }

    if (node is List) {
      return _buildList(context, node, title: title);
    }

    if (node is Map) {
      return _buildMap(context, Map<String, dynamic>.from(node), title: title);
    }

    return Text(formatJsonValue(node));
  }

  Widget _buildMap(
    BuildContext context,
    Map<String, dynamic> map, {
    String? title,
  }) {
    if (map.isEmpty) {
      return const Text('Empty object.');
    }

    final children = <Widget>[];
    final scalars = <String, dynamic>{};

    for (final entry in map.entries) {
      if (entry.key == 'display') continue;
      if (isScalar(entry.value)) {
        scalars[entry.key] = entry.value;
      }
    }

    if (title != null && depth == 0) {
      children.add(
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Text(
            title,
            style: Theme.of(context).textTheme.titleSmall,
          ),
        ),
      );
    }

    if (scalars.isNotEmpty) {
      children.add(_scalarCardGrid(scalars));
      children.add(const SizedBox(height: 12));
    }

    for (final entry in map.entries) {
      if (entry.key == 'display' || isScalar(entry.value)) continue;
      children.add(_buildComplexField(context, entry.key, entry.value));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
  }

  Widget _buildList(BuildContext context, List<dynamic> list, {String? title}) {
    if (list.isEmpty) {
      return Text(title != null ? '$title: empty list' : 'Empty list');
    }

    if (isMapList(list)) {
      final rows = list
          .whereType<Map>()
          .map((row) => Map<String, dynamic>.from(row))
          .toList();
      final columns = unionTableColumns(rows);
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title != null ? formatJsonLabel(title) : 'Items',
                style: Theme.of(context).textTheme.titleSmall,
              ),
              Text(
                '${rows.length} row${rows.length == 1 ? '' : 's'}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 8),
              CaptureDataTable(columns: columns, rows: rows),
            ],
          ),
        ),
      );
    }

    if (list.every((item) => isScalar(item))) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (title != null)
                Text(formatJsonLabel(title),
                    style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: list
                    .map(
                      (item) => Chip(
                        label: Text(
                          formatJsonValue(item),
                          style: const TextStyle(fontSize: 11),
                        ),
                      ),
                    )
                    .toList(),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (title != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(4, 4, 4, 8),
                child: Text(formatJsonLabel(title),
                    style: Theme.of(context).textTheme.titleSmall),
              ),
            ...list.asMap().entries.map(
                  (entry) => Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: _buildComplexField(
                      context,
                      '${entry.key + 1}',
                      entry.value,
                    ),
                  ),
                ),
          ],
        ),
      ),
    );
  }

  Widget _buildComplexField(BuildContext context, String key, dynamic value) {
    final label = formatJsonLabel(key);

    if (isScalar(value)) {
      return _scalarTile(context, label, value);
    }

    if (value is List && value.length <= 4 && !isMapList(value)) {
      return Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: StructuredJsonView(
          data: value,
          title: label,
          depth: depth + 1,
        ),
      );
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 12),
          childrenPadding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
          title: Text(label, style: Theme.of(context).textTheme.titleSmall),
          subtitle: Text(
            _complexSubtitle(value),
            style: Theme.of(context).textTheme.bodySmall,
          ),
          initiallyExpanded: depth < 1,
          children: [
            StructuredJsonView(
              data: value,
              depth: depth + 1,
            ),
          ],
        ),
      ),
    );
  }

  Widget _scalarCardGrid(Map<String, dynamic> scalars) {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: scalars.entries
          .map(
            (entry) => SizedBox(
              width: 160,
              child: SummaryCard(
                label: formatJsonLabel(entry.key),
                value: formatJsonValue(entry.value),
              ),
            ),
          )
          .toList(),
    );
  }

  Widget _scalarTile(BuildContext context, String label, dynamic value) {
    return ListTile(
      dense: true,
      contentPadding: EdgeInsets.zero,
      title: Text(label, style: Theme.of(context).textTheme.bodySmall),
      trailing: Text(
        formatJsonValue(value),
        style: Theme.of(context).textTheme.bodyMedium,
      ),
    );
  }

  String _complexSubtitle(dynamic value) {
    if (value is List) return '${value.length} items';
    if (value is Map) return '${value.length} fields';
    return formatJsonValue(value);
  }
}