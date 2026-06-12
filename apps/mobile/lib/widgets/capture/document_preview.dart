import 'package:flutter/material.dart';

class DocumentPreview extends StatelessWidget {
  final String title;
  final String excerpt;
  final List<dynamic>? keywords;
  final int? pages;
  final int? sizeBytes;

  const DocumentPreview({
    super.key,
    required this.title,
    required this.excerpt,
    this.keywords,
    this.pages,
    this.sizeBytes,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.picture_as_pdf, color: Colors.redAccent),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            if (pages != null || sizeBytes != null) ...[
              const SizedBox(height: 8),
              Text(
                [
                  if (pages != null) '$pages pages',
                  if (sizeBytes != null) _formatBytes(sizeBytes!),
                ].join(' · '),
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
            if (keywords != null && keywords!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: keywords!
                    .map(
                      (keyword) => Chip(
                        label: Text('$keyword', style: const TextStyle(fontSize: 11)),
                        visualDensity: VisualDensity.compact,
                      ),
                    )
                    .toList(),
              ),
            ],
            if (excerpt.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text('Excerpt', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 4),
              Text(excerpt),
            ],
          ],
        ),
      ),
    );
  }

  static String _formatBytes(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}