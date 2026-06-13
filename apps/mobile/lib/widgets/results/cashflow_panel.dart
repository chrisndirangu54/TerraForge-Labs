import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class CashflowPanel extends StatelessWidget {
  final List<Map<String, dynamic>> cashFlows;
  final double? paybackYears;
  final double? npvUsd;

  const CashflowPanel({
    super.key,
    required this.cashFlows,
    this.paybackYears,
    this.npvUsd,
  });

  @override
  Widget build(BuildContext context) {
    if (cashFlows.isEmpty) {
      return const Text('No cash flow data — run an analysis first.');
    }

    final rows = _buildRows();
    final currencyFull = NumberFormat.simpleCurrency();
    final totalUndiscounted = rows.fold<double>(0, (sum, row) => sum + row.amount);
    final peakInflow = rows.map((r) => r.amount).reduce(math.max);
    final initialCapex = rows.first.amount;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _summaryChip(
              context,
              'Undiscounted total',
              currencyFull.format(totalUndiscounted),
              Colors.amber.shade700,
            ),
            _summaryChip(
              context,
              'Peak annual inflow',
              currencyFull.format(peakInflow),
              Colors.green.shade600,
            ),
            _summaryChip(
              context,
              'Initial CAPEX (Y0)',
              currencyFull.format(initialCapex),
              Colors.deepOrange.shade400,
            ),
          ],
        ),
        const SizedBox(height: 16),
        Card(
          clipBehavior: Clip.antiAlias,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Annual cash flow & cumulative position',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 8),
                SizedBox(
                  height: 200,
                  child: CustomPaint(
                    painter: _CashflowChartPainter(
                      rows: rows,
                      paybackYears: paybackYears,
                      inflowColor: Colors.green.shade600,
                      outflowColor: Colors.deepOrange.shade400,
                      cumulativeColor: Colors.amber.shade600,
                      gridColor: Colors.teal.withValues(alpha: 0.15),
                      axisColor: Colors.grey.shade600,
                    ),
                    child: const SizedBox.expand(),
                  ),
                ),
                Row(
                  children: [
                    _legendDot(Colors.deepOrange.shade400, 'Outflow / CAPEX'),
                    const SizedBox(width: 12),
                    _legendDot(Colors.green.shade600, 'Inflow'),
                    const SizedBox(width: 12),
                    _legendDot(Colors.amber.shade600, 'Cumulative'),
                  ],
                ),
              ],
            ),
          ),
        ),
        if (npvUsd != null) ...[
          const SizedBox(height: 8),
          Text(
            'NPV (discounted): ${currencyFull.format(npvUsd)} · '
            'Cumulative line shows undiscounted project cash position by year.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
        const SizedBox(height: 12),
        Card(
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              headingRowHeight: 36,
              dataRowMinHeight: 36,
              dataRowMaxHeight: 44,
              columns: const [
                DataColumn(label: Text('Year')),
                DataColumn(label: Text('Annual')),
                DataColumn(label: Text('Cumulative')),
                DataColumn(label: Text('Phase')),
              ],
              rows: rows.map((row) {
                final phase = row.year == 0
                    ? 'Investment'
                    : row.cumulative < 0
                        ? 'Payback period'
                        : 'Free cash';
                return DataRow(
                  cells: [
                    DataCell(Text(row.year == 0 ? 'Y0 (CAPEX)' : 'Year ${row.year}')),
                    DataCell(
                      Text(
                        currencyFull.format(row.amount),
                        style: TextStyle(
                          color: row.amount < 0
                              ? Colors.deepOrange.shade400
                              : Colors.green.shade600,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ),
                    DataCell(
                      Text(
                        currencyFull.format(row.cumulative),
                        style: TextStyle(
                          color: row.cumulative < 0
                              ? Colors.blueGrey.shade400
                              : Colors.teal.shade300,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ),
                    DataCell(Text(phase, style: Theme.of(context).textTheme.bodySmall)),
                  ],
                );
              }).toList(),
            ),
          ),
        ),
      ],
    );
  }

  List<_CashflowRow> _buildRows() {
    var cumulative = 0.0;
    final rows = <_CashflowRow>[];
    for (final item in cashFlows) {
      final year = (item['year'] as num?)?.toInt() ?? rows.length;
      final amount = (item['amount_usd'] as num?)?.toDouble() ?? 0;
      cumulative += amount;
      rows.add(_CashflowRow(year: year, amount: amount, cumulative: cumulative));
    }
    return rows;
  }

  Widget _summaryChip(
    BuildContext context,
    String label,
    String value,
    Color accent,
  ) {
    return Container(
      width: 160,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: accent.withValues(alpha: 0.35)),
        borderRadius: BorderRadius.circular(10),
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.labelSmall),
          const SizedBox(height: 4),
          Text(
            value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: accent,
                ),
          ),
        ],
      ),
    );
  }

  Widget _legendDot(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 10)),
      ],
    );
  }
}

class _CashflowRow {
  final int year;
  final double amount;
  final double cumulative;

  const _CashflowRow({
    required this.year,
    required this.amount,
    required this.cumulative,
  });
}

class _CashflowChartPainter extends CustomPainter {
  final List<_CashflowRow> rows;
  final double? paybackYears;
  final Color inflowColor;
  final Color outflowColor;
  final Color cumulativeColor;
  final Color gridColor;
  final Color axisColor;

  _CashflowChartPainter({
    required this.rows,
    required this.paybackYears,
    required this.inflowColor,
    required this.outflowColor,
    required this.cumulativeColor,
    required this.gridColor,
    required this.axisColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (rows.isEmpty) return;

    const leftPad = 52.0;
    const rightPad = 12.0;
    const topPad = 8.0;
    const bottomPad = 28.0;

    final chartWidth = size.width - leftPad - rightPad;
    final chartHeight = size.height - topPad - bottomPad;
    final originY = topPad + chartHeight / 2;

    final minVal = rows
        .map((r) => math.min(r.amount, r.cumulative))
        .fold<double>(0, math.min);
    final maxVal = rows
        .map((r) => math.max(r.amount, r.cumulative))
        .fold<double>(0, math.max);
    final bound = math.max(math.max(minVal.abs(), maxVal.abs()), 1.0) * 1.1;

    final barWidth = chartWidth / rows.length * 0.55;
    final gap = chartWidth / rows.length;

    final gridPaint = Paint()..color = gridColor;
    for (var i = -2; i <= 2; i++) {
      final y = originY - (i / 2) * (chartHeight / 2);
      canvas.drawLine(Offset(leftPad, y), Offset(size.width - rightPad, y), gridPaint);
    }

    final axisPaint = Paint()
      ..color = axisColor
      ..strokeWidth = 1;
    canvas.drawLine(
      Offset(leftPad, originY),
      Offset(size.width - rightPad, originY),
      axisPaint,
    );

    final labelStyle = TextStyle(color: axisColor, fontSize: 9);
    final compact = NumberFormat.compactCurrency(symbol: '\$');
    for (var i = -1; i <= 1; i++) {
      final value = bound * i;
      final y = originY - (value / bound) * (chartHeight / 2);
      final tp = TextPainter(
        text: TextSpan(text: compact.format(value), style: labelStyle),
        textDirection: ui.TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(2, y - tp.height / 2));
    }

    for (var i = 0; i < rows.length; i++) {
      final row = rows[i];
      final centerX = leftPad + gap * i + gap / 2;
      final barHeight = (row.amount / bound) * (chartHeight / 2);
      final barTop = barHeight < 0 ? originY : originY - barHeight;
      final rect = RRect.fromRectAndRadius(
        Rect.fromLTWH(
          centerX - barWidth / 2,
          barTop,
          barWidth,
          barHeight.abs().clamp(2, chartHeight),
        ),
        const Radius.circular(3),
      );
      canvas.drawRRect(
        rect,
        Paint()..color = row.amount >= 0 ? inflowColor : outflowColor,
      );

      final yearLabel = row.year == 0 ? 'Y0' : 'Y${row.year}';
      final yearTp = TextPainter(
        text: TextSpan(text: yearLabel, style: labelStyle),
        textDirection: ui.TextDirection.ltr,
      )..layout();
      yearTp.paint(
        canvas,
        Offset(centerX - yearTp.width / 2, size.height - bottomPad + 6),
      );
    }

    final cumulativePath = Path();
    for (var i = 0; i < rows.length; i++) {
      final x = leftPad + gap * i + gap / 2;
      final y = originY - (rows[i].cumulative / bound) * (chartHeight / 2);
      if (i == 0) {
        cumulativePath.moveTo(x, y);
      } else {
        cumulativePath.lineTo(x, y);
      }
    }
    canvas.drawPath(
      cumulativePath,
      Paint()
        ..color = cumulativeColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2,
    );

    for (final row in rows) {
      final i = rows.indexOf(row);
      final x = leftPad + gap * i + gap / 2;
      final y = originY - (row.cumulative / bound) * (chartHeight / 2);
      canvas.drawCircle(Offset(x, y), 3, Paint()..color = cumulativeColor);
    }

    if (paybackYears != null) {
      final paybackIndex = paybackYears!.ceil().clamp(0, rows.length - 1);
      final x = leftPad + gap * paybackIndex + gap / 2;
      final dashPaint = Paint()
        ..color = outflowColor
        ..strokeWidth = 1;
      const dashHeight = 6.0;
      for (var y = topPad; y < topPad + chartHeight; y += dashHeight * 2) {
        canvas.drawLine(Offset(x, y), Offset(x, y + dashHeight), dashPaint);
      }
      final paybackTp = TextPainter(
        text: TextSpan(
          text: 'Payback ~${paybackYears!.toStringAsFixed(1)}y',
          style: TextStyle(color: outflowColor, fontSize: 9),
        ),
        textDirection: ui.TextDirection.ltr,
      )..layout();
      paybackTp.paint(canvas, Offset(x + 4, topPad + 2));
    }
  }

  @override
  bool shouldRepaint(covariant _CashflowChartPainter oldDelegate) =>
      oldDelegate.rows != rows || oldDelegate.paybackYears != paybackYears;
}