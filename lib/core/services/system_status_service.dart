import 'package:microdetect/core/services/api_service.dart';

import '../models/system_status_model.dart';

class SystemStatusService extends ApiService {
  Future<SystemStatusModel> getSystemStatus() async {
    final response = await get('/api/v1/system/status');
    return SystemStatusModel.fromMap(response.data);
  }
}