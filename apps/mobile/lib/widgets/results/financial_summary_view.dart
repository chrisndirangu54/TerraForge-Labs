import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import 'cashflow_panel.dart';

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

  Map<String, dynamic>? get _metrics {
    final metrics = widget.result['metrics'];
    return metrics is Map ? Map<String, dynamic>.from(metrics) : null;
  }

  Map<String, dynamic>? get _annual {
    final annual = widget.result['annual'];
    return annual is Map ? Map<String, dynamic>.from(annual) : null;
  }

  List<Map<String, dynamic>> get _cashFlows {
    final flows = widget.result['cash_flows'];
    if (flows is! List) return [];
    return flows
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    final metrics = _metrics;
    final annual = _annual;
    final npv = metrics?['npv_usd'] ?? widget.result['npv_usd'] ?? widget.result['npv'];
    final irr = metrics?['irr'] ?? widget.result['irr'];
    final payback = metrics?['payback_years'] ?? widget.result['payback_years'];
    final revenue = annual?['annual_revenue_usd'] ?? widget.result['revenue_usd'];
    final capex = widget.result['inputs'] is Map
        ? (widget.result['inputs'] as Map)['capex_usd']
        : widget.result['capex_usd'];
    final monteCarlo = widget.result['monte_carlo'];
    final cashFlows = _cashFlows;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            if (npv != null) _metricCard('NPV', _formatMoney(npv), Colors.amber.shade700),
            if (irr != null)
              _metricCard(
                'IRR',
                irr is num ? '${(irr * 100).toStringAsFixed(1)}%' : '$irr',
                Colors.teal.shade400,
              ),
            if (payback != null)
              _metricCard(
                'Payback',
                payback is num ? '${payback.toStringAsFixed(1)} yrs' : '$payback',
                Colors.blueGrey.shade400,
              ),
            if (revenue != null) _metricCard('Revenue', _formatMoney(revenue), Colors.green.shade600),
            if (capex != null) _metricCard('CAPEX', _formatMoney(capex), Colors.deepOrange.shade400),
          ],
        ),
        if (monteCarlo is Map && monteCarlo['npv'] is Map) ...[
          const SizedBox(height: 16),
          Text('Price risk (Monte Carlo)', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          _monteCarloBand(Map<String, dynamic>.from(monteCarlo['npv'] as Map)),
        ],
        if (cashFlows.isNotEmpty) ...[
          const SizedBox(height: 20),
          Text('Cash flow schedule', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          CashflowPanel(
            cashFlows: cashFlows,
            paybackYears: payback is num ? payback.toDouble() : null,
            npvUsd: npv is num ? npv.toDouble() : null,
          ),
        ],
        if (widget.presets != null && widget.presets!['commodities'] is Map) ...[
          const SizedBox(height: 16),
          Text('Commodity presets', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          ...(widget.presets!['commodities'] as Map).entries.map((entry) {
            final data = entry.value;
            return ListTile(
              dense: true,
              title: Text('${entry.key}'),
              subtitle: data is Map
                  ? Text(
                      'Price: ${data['metal_price_usd'] ?? data['price_usd_per_kg'] ?? data['price']} · '
                      'Recovery: ${data['recovery'] ?? data['recovery_pct'] ?? 'n/a'}',
                    )
                  : null,
            );
          }),
        ],
        const SizedBox(height: 8),
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

  Widget _monteCarloBand(Map<String, dynamic> npvBand) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        if (npvBand['p10_usd'] != null)
          _metricCard('P10 NPV', _formatMoney(npvBand['p10_usd']), Colors.deepOrange.shade300),
        if (npvBand['p50_usd'] != null)
          _metricCard('P50 NPV', _formatMoney(npvBand['p50_usd']), Colors.teal.shade300),
        if (npvBand['p90_usd'] != null)
          _metricCard('P90 NPV', _formatMoney(npvBand['p90_usd']), Colors.green.shade500),
      ],
    );
  }

  Widget _metricCard(String label, String value, Color accent) {
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
              Text(
                value,
                style: TextStyle(fontWeight: FontWeight.bold, color: accent),
              ),
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