import 'package:flutter/material.dart';

import '../services/marketplace_client.dart';
import '../widgets/results/marketplace_catalog_view.dart';
import '../widgets/results/structured_json_view.dart';
import '../widgets/satellite/satellite_scene_list.dart';

class MarketplaceScreen extends StatefulWidget {
  const MarketplaceScreen({super.key});

  @override
  State<MarketplaceScreen> createState() => _MarketplaceScreenState();
}

class _MarketplaceScreenState extends State<MarketplaceScreen>
    with SingleTickerProviderStateMixin {
  final MarketplaceClient _client = MarketplaceClient();
  late final TabController _tabs;

  bool _loading = false;
  String? _error;
  String? _actionMessage;
  Map<String, dynamic>? _catalogue;
  List<Map<String, dynamic>> _items = [];
  List<Map<String, dynamic>> _drillPreview = [];

  static const _categories = ['all', 'drill_log', 'report', 'plugin'];

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: _categories.length, vsync: this);
    _tabs.addListener(() {
      if (!_tabs.indexIsChanging) _load(_categories[_tabs.index]);
    });
    _load('all');
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _load(String category) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final query = category == 'all' ? null : category;
      final raw = await _client.fetchCatalogueRaw(category: query);
      setState(() {
        _catalogue = raw;
        _items = _client.parseItems(raw['items']);
        _drillPreview = _client.parseItems(raw['drill_log_preview']);
        _loading = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _install(Map<String, dynamic> item) async {
    final id = '${item['id'] ?? ''}';
    try {
      final result = await _client.install(id);
      setState(() {
        _actionMessage = 'Installed ${item['name']}: ${result['status'] ?? result['installed']}';
      });
    } catch (error) {
      setState(() => _error = error.toString());
    }
  }

  Future<void> _purchase(Map<String, dynamic> item) async {
    final id = '${item['id'] ?? ''}';
    final price = (item['price_usd'] as num?)?.toDouble() ?? 0;
    try {
      final result = await _client.checkout(itemId: id, amountUsd: price);
      setState(() {
        _actionMessage =
            'Checkout ${item['name']}: ${result['status']} (${result['receipt_id']})';
      });
    } catch (error) {
      setState(() => _error = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Marketplace'),
        bottom: TabBar(
          controller: _tabs,
          isScrollable: true,
          tabs: const [
            Tab(text: 'All'),
            Tab(text: 'Drill logs'),
            Tab(text: 'Reports'),
            Tab(text: 'Plugins'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => _load(_categories[_tabs.index]),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Text(
                  'Drill logs, JORC report templates, and capture pipeline plugins.',
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                ],
                if (_actionMessage != null) ...[
                  const SizedBox(height: 12),
                  Text(_actionMessage!, style: const TextStyle(color: Colors.teal)),
                ],
                const SizedBox(height: 12),
                if (_drillPreview.isNotEmpty &&
                    (_tabs.index == 0 || _tabs.index == 1)) ...[
                  DrillLogPreviewTable(holes: _drillPreview),
                  const SizedBox(height: 16),
                ],
                MarketplaceCatalogView(
                  items: _items,
                  onInstall: _install,
                  onPurchase: _purchase,
                ),
                if (_catalogue != null) ...[
                  const SizedBox(height: 16),
                  StructuredJsonView(data: _catalogue, title: 'Catalogue response'),
                ],
              ],
            ),
    );
  }
}