import 'package:get/get.dart';
import '../controllers/backend_monitor_controller.dart';

class BackendMonitorBinding extends Bindings {
  @override
  void dependencies() {
    Get.put<BackendMonitorController>(BackendMonitorController(), permanent: true);
  }
}