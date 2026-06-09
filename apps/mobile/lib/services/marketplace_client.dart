class MarketplaceClient {
  Future<List<Map<String, dynamic>>> listCatalogue() async {
    return [
      {'name': 'ASEG-GDF2 parser plugin', 'price_usd': 0},
      {'name': 'NI 43-101 template', 'price_usd': 49},
    ];
  }
}
