import 'package:flutter/material.dart';

class GpuCapabilitiesView extends StatelessWidget {
  final Map<String, dynamic> capabilities;

  const GpuCapabilitiesView({super.key, required this.capabilities});

  @override
  Widget build(BuildContext context) {
    final cuda = capabilities['cuda_available'] == true;
    final device = capabilities['device_name'] ?? capabilities['device'] ?? 'unknown';
    final tasks = capabilities['supported_tasks'] ?? capabilities['queues'];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  cuda ? Icons.memory : Icons.computer,
                  color: cuda ? Colors.green : Colors.grey,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(device, style: Theme.of(context).textTheme.titleMedium),
                      Text(cuda ? 'CUDA available' : 'CPU fallback mode'),
                    ],
                  ),
                ),
              ],
            ),
            if (tasks is List && tasks.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text('Supported tasks', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 6),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: tasks
                    .map((task) => Chip(label: Text('$task', style: const TextStyle(fontSize: 11))))
                    .toList(),
              ),
            ],
            if (capabilities['mixed_precision'] != null) ...[
              const SizedBox(height: 8),
              Text('Mixed precision: ${capabilities['mixed_precision']}'),
            ],
          ],
        ),
      ),
    );
  }
}