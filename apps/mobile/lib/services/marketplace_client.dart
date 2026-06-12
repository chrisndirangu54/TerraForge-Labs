import 'api_client.dart';

class MarketplaceCatalogue {
  final List<Map<String, dynamic>> items;
  final List<String> categories;
  final List<Map<String, dynamic>> drillLogPreview;

  const MarketplaceCatalogue({
    required this.items,
    required this.categories,
    required this.drillLogPreview,
  });
}

class MarketplaceClient {
  MarketplaceClient({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<Map<String, dynamic>> fetchCatalogueRaw({String? category}) {
    return _client.get('/marketplace/catalogue', query: {
      if (category != null && category.isNotEmpty) 'category': category,
    });
  }

  Future<MarketplaceCatalogue> fetchCatalogue({String? category}) async {
    final response = await fetchCatalogueRaw(category: category);
    return MarketplaceCatalogue(
      items: parseItems(response['items']),
      categories: _parseCategories(response['categories']),
      drillLogPreview: parseItems(response['drill_log_preview']),
    );
  }

  List<Map<String, dynamic>> parseItems(dynamic raw) => _parseItems(raw);

  Future<List<Map<String, dynamic>>> listCatalogue({String? category}) async {
    final catalogue = await fetchCatalogue(category: category);
    return catalogue.items;
  }

  Future<Map<String, dynamic>> install(String pluginId) {
    return _client.post('/marketplace/install', {'plugin_id': pluginId});
  }

  Future<Map<String, dynamic>> checkout({
    required String itemId,
    double amountUsd = 0,
    String provider = 'stripe',
  }) {
    return _client.post('/marketplace/checkout', {
      'item_id': itemId,
      'amount_usd': amountUsd,
      'provider': provider,
    });
  }

  List<Map<String, dynamic>> _parseItems(dynamic raw) {
    if (raw is List) {
      return raw
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
    }
    return [];
  }

  List<String> _parseCategories(dynamic raw) {
    if (raw is List) {
      return raw.map((c) => '$c').toList();
    }
    return [];
  }
}