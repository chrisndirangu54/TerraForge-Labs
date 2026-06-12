import 'package:flutter/material.dart';

typedef MarketplaceItemAction = Future<void> Function(Map<String, dynamic> item);

class MarketplaceCatalogView extends StatelessWidget {
  final List<Map<String, dynamic>> items;
  final MarketplaceItemAction? onInstall;
  final MarketplaceItemAction? onPurchase;

  const MarketplaceCatalogView({
    super.key,
    required this.items,
    this.onInstall,
    this.onPurchase,
  });

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const Text('No marketplace items available.');
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: items.map((item) => _itemCard(context, item)).toList(),
    );
  }

  Widget _itemCard(BuildContext context, Map<String, dynamic> item) {
    final category = '${item['category'] ?? 'other'}';
    final price = item['price_usd'];
    final isFree = price is num && price <= 0;
    final isPlugin = category == 'plugin';

    return Card(
      child: ListTile(
        leading: Icon(_iconFor(category)),
        title: Text('${item['name'] ?? 'Item'}'),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${item['description'] ?? category}'),
            if (item['holes'] != null)
              Text(
                '${item['holes']} holes · ${item['total_metres'] ?? '?'} m',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            if (item['formats'] is List)
              Text(
                (item['formats'] as List).join(', '),
                style: Theme.of(context).textTheme.bodySmall,
              ),
          ],
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _priceBadge(price),
            if (isPlugin && onInstall != null)
              TextButton(
                onPressed: () => onInstall!(item),
                child: const Text('Install', style: TextStyle(fontSize: 11)),
              )
            else if (!isFree && onPurchase != null)
              TextButton(
                onPressed: () => onPurchase!(item),
                child: const Text('Buy', style: TextStyle(fontSize: 11)),
              )
            else if (isFree && onInstall != null)
              TextButton(
                onPressed: () => onInstall!(item),
                child: const Text('Get', style: TextStyle(fontSize: 11)),
              ),
          ],
        ),
        isThreeLine: true,
      ),
    );
  }

  Widget _priceBadge(dynamic price) {
    final value = price is num ? price.toDouble() : 0;
    return Chip(
      label: Text(value <= 0 ? 'Free' : '\$${value.toStringAsFixed(0)}'),
      visualDensity: VisualDensity.compact,
    );
  }

  IconData _iconFor(String category) {
    switch (category) {
      case 'plugin':
        return Icons.extension;
      case 'report':
        return Icons.description_outlined;
      case 'drill_log':
        return Icons.construction;
      case 'template':
        return Icons.description_outlined;
      case 'dataset':
        return Icons.storage_outlined;
      default:
        return Icons.shopping_bag_outlined;
    }
  }
}