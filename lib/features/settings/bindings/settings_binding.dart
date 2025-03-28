import 'package:get/get.dart';
import 'package:microdetect/core/services/backend_installer_service.dart';
import 'package:microdetect/core/services/backend_service.dart';
import 'package:microdetect/features/shared/events/screen_events.dart';
import '../controllers/settings_controller.dart';
import '../services/settings_service.dart';

/// Binding para o módulo de configurações
class SettingsBinding implements Bindings {
  @override
  void dependencies() {
    // Services
    Get.lazyPut<SettingsService>(() => SettingsService());

    // Controllers
    Get.lazyPut<SettingsController>(() => SettingsController(
          settingsService: Get.find<SettingsService>(),
          backendService: Get.find<BackendService>(),
          installerService: Get.find<BackendInstallerService>(),
        ));
  }
}
