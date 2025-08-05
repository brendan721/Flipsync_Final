import 'dart:convert';
import 'package:http/http.dart' as http;

/// Test script to verify OAuth configuration
void main() async {
  print('🔍 Testing OAuth Configuration...');
  
  // Test different base URLs
  final testUrls = [
    'http://localhost:8000/api/v1',
    'https://flipsyncai.com/api/v1',
    'https://www.flipsyncai.com/api/v1',
  ];
  
  for (final baseUrl in testUrls) {
    print('\n📡 Testing: $baseUrl');
    await testOAuthEndpoint(baseUrl);
  }
}

Future<void> testOAuthEndpoint(String baseUrl) async {
  try {
    final url = '$baseUrl/marketplace/ebay/oauth/authorize';
    print('   🔗 URL: $url');
    
    final response = await http.post(
      Uri.parse(url),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Origin': 'https://flipsyncai.com', // Test with production origin
      },
      body: json.encode({
        'scopes': [
          'https://api.ebay.com/oauth/api_scope',
          'https://api.ebay.com/oauth/api_scope/sell.inventory',
        ],
      }),
    ).timeout(Duration(seconds: 10));
    
    print('   ✅ Status: ${response.statusCode}');
    print('   📄 Headers: ${response.headers}');
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      print('   🎯 Response: ${data.toString().substring(0, 100)}...');
    } else {
      print('   ❌ Error: ${response.body}');
    }
    
  } catch (e) {
    print('   💥 Exception: $e');
  }
}
