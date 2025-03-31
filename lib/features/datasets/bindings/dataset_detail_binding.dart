import 'package:get/get.dart';
import 'package:microdetect/features/camera/services/camera_service.dart';
import '../controllers/dataset_detail_controller.dart';
import '../services/dataset_service.dart';

class DatasetDetailBinding extends Bindings {
  @override
  void dependencies() {
    // Registrar o serviço de câmera se ainda não estiver registrado
    if (!Get.isRegistered<CameraService>()) {
      Get.put<CameraService>(
        CameraService(),
        permanent: true
      );
    }

    // Registrar o serviço de datasets se ainda não estiver registrado
    if (!Get.isRegistered<DatasetService>(tag: 'datasetService')) {
      Get.put<DatasetService>(
        DatasetService(),
        tag: 'datasetService',
        permanent: true
      );
    }

    // Registrar o controller de detalhes do dataset
    Get.put<DatasetDetailController>(
      DatasetDetailController(
        datasetId: int.parse(Get.parameters['id']!),
      )
    );
  }
} 