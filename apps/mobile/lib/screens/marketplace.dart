import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/marketplace_client.dart';

class MarketplaceScreen extends StatefulWidget {
  const MarketplaceScreen({super.key});

  @override
  State<MarketplaceScreen> createState() => _MarketplaceScreenState();
}

class _MarketplaceScreenState extends State<MarketplaceScreen> {
  final MarketplaceClient _client = MarketplaceClient();
  bool _loading = false;
  String? _error;
  List<Map<String, dynamic>> _items = [];

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final items = await _client.listCatalogue();
      setState(() {
        _items = items;
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
  void initState() {
    super.initState();
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Marketplace')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (_error != null)
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                ..._items.map(
                  (item) => Card(
                    child: ListTile(
                      title: Text(item['name']?.toString() ?? 'Item'),
                      subtitle: Text(
                        '\$${item['price_usd']} · ${item['category'] ?? 'catalogue'}',
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                SelectableText(
                  JsonEncoder.withIndent('  ').convert(_items),
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                ),
              ],
            ),
    );
  }
}