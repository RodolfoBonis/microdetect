import 'package:get/get.dart';

import '../controllers/app_root_controller.dart';

class AppRootBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<AppRootController>(
        () => AppRootController(backendService: Get.find()));
  }
}
