import 'package:flutter/material.dart';

import '../services/job_poller.dart';
import '../services/terraforge_api.dart';
import '../widgets/backend_action_screen.dart';

class JorcReportScreen extends StatelessWidget {
  const JorcReportScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = TerraforgeApi();
    final poller = JobPollerService();
    return BackendActionScreen(
      title: 'JORC Report',
      description:
          'Generate a JORC report via POST /reports/jorc, then poll GET /jobs/{id}.',
      actionLabel: 'Generate Report',
      onAction: () async {
        final started = await api.generateJorcReport();
        final jobId = started['job_id']?.toString();
        if (jobId == null) {
          return started;
        }
        return poller.poll(jobId);
      },
    );
  }
}
