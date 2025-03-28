import 'package:get/get.dart';
import 'package:microdetect/core/services/system_status_service.dart';
import '../controllers/home_controller.dart';

class HomeBinding implements Bindings {
  @override
  void dependencies() {
    // Serviços
    Get.lazyPut<SystemStatusService>(() => SystemStatusService());
    
    // Controllers
    Get.lazyPut<HomeController>(() => HomeController(
      systemStatusService: Get.find<SystemStatusService>(),
    ));
  }
}
