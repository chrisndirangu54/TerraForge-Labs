import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/job_poller.dart';
import '../services/terraforge_api.dart';

class JorcReportScreen extends StatefulWidget {
  const JorcReportScreen({super.key});

  @override
  State<JorcReportScreen> createState() => _JorcReportScreenState();
}

class _JorcReportScreenState extends State<JorcReportScreen> {
  final TerraforgeApi _api = TerraforgeApi();
  final JobPollerService _poller = JobPollerService();
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;

  Map<String, dynamic> _statusFromJob(Map<String, dynamic> job) {
    final workflowStatus = job['status']?.toString() ?? 'unknown';
    final result = job['result'] as Map<String, dynamic>? ?? {};
    final acknowledged = result['disclaimer_acknowledged'] == true;
    final reportStatus = result['report_status']?.toString() ??
        (acknowledged ? 'approved' : 'draft');
    final approvalStatus = result['approval_status']?.toString() ??
        (acknowledged
            ? 'competent_person_signed'
            : 'pending_competent_person_review');

    return {
      'workflow_status': workflowStatus,
      'report_status': reportStatus,
      'approval_status': approvalStatus,
      'disclaimer_acknowledged': acknowledged,
      if (result['json_url'] != null) 'json_url': result['json_url'],
      if (result['html_url'] != null) 'html_url': result['html_url'],
      if (result['pdf_url'] != null) 'pdf_url': result['pdf_url'],
    };
  }

  Future<void> _generateReport() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final started = await _api.generateJorcReport();
      final jobId = started['job_id']?.toString();
      Map<String, dynamic> job = started;
      if (jobId != null && started['status'] != 'complete') {
        job = await _poller.pollUntilComplete(jobId);
      }
      setState(() {
        _result = {
          'job_id': jobId ?? job['job_id'],
          ..._statusFromJob(job),
          if (job['result'] != null) 'artifacts': job['result'],
        };
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
    return Scaffold(
      appBar: AppBar(title: const Text('JORC Report')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Generate a JORC report via POST /reports/jorc and display draft/approval status from the job API.',
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loading ? null : _generateReport,
            child: Text(_loading ? 'Generating...' : 'Generate Report'),
          ),
          if (_result != null) ...[
            const SizedBox(height: 16),
            _StatusChip(
              label: 'Workflow',
              value: _result!['workflow_status']?.toString() ?? 'unknown',
            ),
            _StatusChip(
              label: 'Report',
              value: _result!['report_status']?.toString() ?? 'draft',
            ),
            _StatusChip(
              label: 'Approval',
              value: _result!['approval_status']?.toString() ?? 'pending',
            ),
            const SizedBox(height: 16),
            SelectableText(
              JsonEncoder.withIndent('  ').convert(_result),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String label;
  final String value;

  const _StatusChip({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Text('$label: ', style: const TextStyle(fontWeight: FontWeight.bold)),
          Chip(label: Text(value)),
        ],
      ),
    );
  }
}