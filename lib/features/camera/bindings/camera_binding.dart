import 'package:get/get.dart';
import 'package:microdetect/features/camera/controllers/camera_controller.dart';
import 'package:microdetect/features/camera/services/camera_service.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';
import 'package:microdetect/features/datasets/services/dataset_service.dart';


class CameraBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<DatasetService>(() => DatasetService());
    
    // Verify if DatasetListController is already registered
    if (!Get.isRegistered<DatasetController>()) {
      Get.lazyPut<DatasetController>(() => DatasetController());
    }

    Get.lazyPut<CameraService>(() => CameraService());
    // Obtain dataset ID if provided
    final arguments = Get.arguments;
    final int? datasetId = arguments != null ? arguments['datasetId'] : null;

    // Register CameraController with the dataset ID
    Get.lazyPut<CameraController>(() => CameraController(
          datasetId: datasetId,
        ));
  }
} 