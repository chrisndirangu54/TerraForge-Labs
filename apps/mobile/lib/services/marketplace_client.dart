import 'api_client.dart';

class MarketplaceClient {
  MarketplaceClient({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<List<Map<String, dynamic>>> listCatalogue() async {
    final response = await _client.get('/marketplace/catalogue');
    final items = response['items'];
    if (items is List) {
      return items
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
    }
    return [];
  }
}
