import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../services/project_store.dart';
import '../services/terraforge_api.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  final _currency = NumberFormat.simpleCurrency();
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _summary;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final summary = await _api.dashboardSummary();
      setState(() {
        _summary = summary;
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final projectId = ProjectStore.instance.selectedProjectId;
    final economics = _summary?['economics_preview'] as Map?;
    final deposit = _summary?['deposit'] as Map?;
    final copilot = _summary?['copilot'] as Map?;
    final gpu = _summary?['gpu'] as Map?;
    final jobs = _summary?['recent_jobs'] as List? ?? [];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mission Control'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loading ? null : _load,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, textAlign: TextAlign.center))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Text('Project: $projectId',
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 16),
                    Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        _MetricCard(
                          label: 'NPV',
                          value: economics?['npv_usd'] != null
                              ? _currency.format(economics!['npv_usd'])
                              : 'n/a',
                          icon: Icons.payments_outlined,
                        ),
                        _MetricCard(
                          label: 'IRR',
                          value: economics?['irr']?.toString() ?? 'n/a',
                          icon: Icons.trending_up,
                        ),
                        _MetricCard(
                          label: 'Ore tonnes',
                          value: deposit?['ore_tonnes_estimate']?.toString() ?? 'n/a',
                          icon: Icons.landscape_outlined,
                        ),
                        _MetricCard(
                          label: 'Grade (Ta ppm)',
                          value: deposit?['mean_grade_ta_ppm']?.toString() ?? 'n/a',
                          icon: Icons.science_outlined,
                        ),
                        _MetricCard(
                          label: 'Copilot',
                          value: copilot?['active'] == true ? 'Active' : 'Off',
                          icon: Icons.smart_toy_outlined,
                        ),
                        _MetricCard(
                          label: 'GPU',
                          value: gpu?['device_name']?.toString() ?? 'n/a',
                          icon: Icons.memory_outlined,
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    Text('Recent jobs (${jobs.length})',
                        style: Theme.of(context).textTheme.titleSmall),
                    const SizedBox(height: 8),
                    if (jobs.isEmpty)
                      const Text('No recent jobs')
                    else
                      ...jobs.whereType<Map>().map((job) {
                        final status = '${job['status'] ?? 'unknown'}';
                        return Card(
                          child: ListTile(
                            leading: Icon(_jobIcon(status)),
                            title: Text('${job['job_type'] ?? job['type'] ?? 'job'}'),
                            subtitle: Text(
                              '${job['job_id'] ?? job['id'] ?? ''} · '
                              '${job['created_at'] ?? ''}',
                            ),
                            trailing: Chip(
                              label: Text(status, style: const TextStyle(fontSize: 11)),
                            ),
                          ),
                        );
                      }),
                  ],
                ),
    );
  }

  IconData _jobIcon(String status) {
    if (status == 'complete') return Icons.check_circle_outline;
    if (status == 'failed') return Icons.error_outline;
    return Icons.hourglass_top;
  }
}

class _MetricCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;

  const _MetricCard({
    required this.label,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 160,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, size: 18, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: 8),
              Text(label, style: Theme.of(context).textTheme.labelSmall),
              Text(
                value,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}