import 'package:flutter/material.dart';

class CaptureDataTable extends StatelessWidget {
  final List<String> columns;
  final List<Map<String, dynamic>> rows;

  const CaptureDataTable({
    super.key,
    required this.columns,
    required this.rows,
  });

  @override
  Widget build(BuildContext context) {
    if (rows.isEmpty) {
      return const Text('No tabular rows to display.');
    }

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        headingRowColor: WidgetStateProperty.all(
          Theme.of(context).colorScheme.surfaceContainerHighest,
        ),
        columns: columns
            .map((column) => DataColumn(label: Text(column)))
            .toList(),
        rows: rows
            .map(
              (row) => DataRow(
                cells: columns
                    .map(
                      (column) => DataCell(
                        Text(_formatCell(row[column])),
                      ),
                    )
                    .toList(),
              ),
            )
            .toList(),
      ),
    );
  }

  static String _formatCell(dynamic value) {
    if (value == null) return '—';
    if (value is bool) return value ? 'yes' : 'no';
    if (value is List) return value.join(', ');
    if (value is Map) return value.toString();
    return value.toString();
  }
}