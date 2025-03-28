import 'package:microdetect/core/services/api_service.dart';

class HealthService extends ApiService {
  Future<bool> checkHealth() {
    return get('/health').then((response) {
      return response.statusCode == 200;
    }).catchError((error) {
      return false;
    });
  }
}