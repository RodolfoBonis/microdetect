import 'package:get/get.dart';
import 'package:microdetect/core/services/backend_fix_service.dart';
import 'package:microdetect/core/services/backend_service.dart';
import 'package:microdetect/core/services/health_service.dart';
import 'package:microdetect/core/services/port_checker_service.dart';
import 'package:microdetect/core/services/python_service.dart';
import 'package:microdetect/core/services/system_status_service.dart';
import 'package:microdetect/features/settings/services/settings_service.dart';
import 'package:microdetect/features/shared/events/event_manager.dart';
import 'package:microdetect/features/shared/events/screen_event_service.dart';

/// Binding principal da aplicação que registra todos os serviços e controllers necessários
class AppBinding implements Bindings {
  @override
  void dependencies() {
    // Registrar o serviço de configurações (se ainda não estiver registrado)
    if (!Get.isRegistered<SettingsService>()) {
      Get.put<SettingsService>(SettingsService(), permanent: true);
    }

    Get.put<EventManager>(EventManager(), permanent: true);

    // Serviço de eventos de tela
    Get.put<ScreenEventService>(ScreenEventService(), permanent: true);

    // Registrar serviços principais como singletons permanentes
    Get.put<HealthService>(HealthService(), permanent: true);
    Get.put<PortCheckerService>(PortCheckerService(), permanent: true);
    Get.put<PythonService>(PythonService(), permanent: true);
    Get.put<BackendFixService>(BackendFixService(), permanent: true);

    // Registrar serviço de backend que depende dos anteriores
    Get.put<BackendService>(BackendService(), permanent: true);
    Get.put<SystemStatusService>(SystemStatusService(), permanent: true);
  }
}
