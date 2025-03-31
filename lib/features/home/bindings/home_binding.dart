import 'package:get/get.dart';
import 'package:microdetect/core/services/system_status_service.dart';
import '../controllers/home_controller.dart';

class HomeBinding extends Bindings {
  @override
  void dependencies() {
    // Registra o HomeController como permanente para manter estado entre navegações
    Get.lazyPut<HomeController>(
      () =>
          HomeController(systemStatusService: Get.find<SystemStatusService>()),
    );
  }
}
