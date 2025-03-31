import 'package:get/get.dart';
import 'package:microdetect/features/camera/controllers/camera_controller.dart';
import 'package:microdetect/features/camera/services/camera_service.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';
import 'package:microdetect/features/datasets/services/dataset_service.dart';


class CameraBinding extends Bindings {
  @override
  void dependencies() {
    // Registra o CameraService como permanente
    Get.put<CameraService>(
      CameraService(),
      permanent: true
    );

    // Registra o DatasetService como permanente
    if (!Get.isRegistered<DatasetService>(tag: 'datasetService')) {
      Get.put<DatasetService>(
        DatasetService(),
        tag: 'datasetService',
        permanent: true
      );
    }

    // Registra o DatasetController como permanente
    if (!Get.isRegistered<DatasetController>(tag: 'datasetController')) {
      Get.put<DatasetController>(
        DatasetController(),
        tag: 'datasetController',
        permanent: true
      );
    }

    // Obtain dataset ID if provided
    final arguments = Get.arguments;
    final int? datasetId = arguments != null ? arguments['datasetId'] : null;

    // Register CameraController with the dataset ID
    Get.put<CameraController>(
      CameraController(
        datasetId: datasetId,
      ),
      permanent: true
    );
  }
} 