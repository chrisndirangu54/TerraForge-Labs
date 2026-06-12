import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class FinancialSummaryView extends StatefulWidget {
  final Map<String, dynamic> result;
  final Map<String, dynamic>? presets;

  const FinancialSummaryView({
    super.key,
    required this.result,
    this.presets,
  });

  @override
  State<FinancialSummaryView> createState() => _FinancialSummaryViewState();
}

class _FinancialSummaryViewState extends State<FinancialSummaryView> {
  bool _showRaw = false;
  final _currency = NumberFormat.simpleCurrency();

  @override
  Widget build(BuildContext context) {
    final npv = widget.result['npv_usd'] ?? widget.result['npv'];
    final irr = widget.result['irr'];
    final payback = widget.result['payback_years'];
    final revenue = widget.result['revenue_usd'];
    final capex = widget.result['capex_usd'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            if (npv != null) _metricCard('NPV', _formatMoney(npv)),
            if (irr != null) _metricCard('IRR', '${(irr is num ? irr * 100 : irr).toString()}%'),
            if (payback != null) _metricCard('Payback', '$payback yrs'),
            if (revenue != null) _metricCard('Revenue', _formatMoney(revenue)),
            if (capex != null) _metricCard('CAPEX', _formatMoney(capex)),
          ],
        ),
        if (widget.presets != null && widget.presets!['commodities'] is Map) ...[
          const SizedBox(height: 16),
          Text('Commodity presets', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          ...(widget.presets!['commodities'] as Map).entries.map((entry) {
            final data = entry.value;
            return ListTile(
              title: Text('${entry.key}'),
              subtitle: data is Map
                  ? Text(
                      'Price: ${data['price_usd_per_kg'] ?? data['price']} · '
                      'Recovery: ${data['recovery_pct'] ?? 'n/a'}%',
                    )
                  : null,
            );
          }),
        ],
        TextButton(
          onPressed: () => setState(() => _showRaw = !_showRaw),
          child: Text(_showRaw ? 'Hide raw JSON' : 'Show raw JSON'),
        ),
        if (_showRaw)
          SelectableText(
            const JsonEncoder.withIndent('  ').convert(widget.result),
            style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
          ),
      ],
    );
  }

  Widget _metricCard(String label, String value) {
    return SizedBox(
      width: 140,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(fontSize: 12)),
              const SizedBox(height: 4),
              Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
            ],
          ),
        ),
      ),
    );
  }

  String _formatMoney(dynamic value) {
    if (value is num) return _currency.format(value);
    return '$value';
  }
}