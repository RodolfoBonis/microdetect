import 'package:get/get.dart';
import '../controllers/backend_monitor_controller.dart';
import '../../../core/services/backend_service.dart';
import '../../../core/services/python_service.dart';
import '../../../core/services/backend_installer_service.dart';
import '../../../core/services/backend_fix_service.dart';

class BackendMonitorBinding extends Bindings {
  @override
  void dependencies() {
    Get.put<BackendMonitorController>(BackendMonitorController(), permanent: true);
  }
}