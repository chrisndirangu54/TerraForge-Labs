import 'package:flutter/material.dart';

import '../capture/capture_result_view.dart';
import 'infer_display.dart';
import 'job_status_panel.dart';

class ApiResultView extends StatelessWidget {
  final Map<String, dynamic>? result;
  final String? jobTitle;

  const ApiResultView({
    super.key,
    this.result,
    this.jobTitle,
  });

  @override
  Widget build(BuildContext context) {
    if (result == null) return const SizedBox.shrink();

    final hasJob = result!['status'] != null || result!['job_id'] != null;
    if (hasJob) {
      return JobStatusPanel(job: result, title: jobTitle ?? 'Job status');
    }

    var display = inferDisplay(result);
    final nested = result!['result'];
    if (display == null && nested is Map) {
      display = inferDisplay(Map<String, dynamic>.from(nested));
    }

    return CaptureResultView(
      display: display,
      fallback: result,
    );
  }
}