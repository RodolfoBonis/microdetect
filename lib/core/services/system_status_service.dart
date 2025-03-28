import 'package:microdetect/core/services/api_service.dart';

import '../models/system_status_model.dart';

class SystemStatusService extends ApiService {
  Future<SystemStatusModel> getSystemStatus() async {
    try {
      final response = await get('/api/v1/system/status');

      // Verificar formato da resposta
      if (response.data is Map) {
        if (response.data.containsKey('data')) {
          return SystemStatusModel.fromMap(response.data['data']);
        } else {
          return SystemStatusModel.fromMap(response.data);
        }
      } else {
        throw Exception(
            'Formato de resposta inesperado: ${response.data.runtimeType}');
      }
    } catch (e) {
      // Retornar modelo com erro
      return SystemStatusModel(
        memory: Memory(total: "0", available: "0", percentage: 0),
        cpu: Cpu(model: 'Desconhecida', cores: 0, threads: 0, usage: "0%"),
        os: '',
        gpu: Gpu(
          model: "Desconhecida",
          memory: "0",
          available: false,
        ),
        storage: Storage(
          used: "0",
          total: "0",
          percentage: 0,
        ),
        server: Server(
          version: "0.0.0",
          active: false,
        ),
      );
    }
  }
}
