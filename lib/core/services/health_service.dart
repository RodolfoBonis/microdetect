import 'dart:convert';

import 'package:microdetect/core/services/api_service.dart';

class HealthService extends ApiService {
  Future<Map<String, dynamic>> checkHealth() async {
    try {
      final response = await get('/health');
      
      // Verificar se a resposta está no formato esperado
      if (response.data is Map<String, dynamic>) {
        return response.data;
      } else if (response.data is String) {
        // Tentar converter string para mapa
        try {
          return jsonDecode(response.data);
        } catch (e) {
          // Se for apenas uma string simples, retornar como status
          return {'status': response.data};
        }
      } else {
        // Formato desconhecido, retornar um status genérico
        return {'status': 'unknown', 'raw_response': response.data.toString()};
      }
    } catch (e) {
      rethrow;
    }
  }
}
