import 'package:get/get.dart';
import 'package:microdetect/features/camera/services/camera_service.dart';
import '../controllers/dataset_detail_controller.dart';
import '../services/dataset_service.dart';

class DatasetDetailBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<CameraService>(() => CameraService());

    // Registrar o serviço de datasets se ainda não estiver registrado
    if (!Get.isRegistered<DatasetService>()) {
      Get.lazyPut<DatasetService>(() => DatasetService());
    }

    
    // Registrar o controller de detalhes do dataset
    Get.lazyPut<DatasetDetailController>(() => DatasetDetailController(
      datasetId: int.parse(Get.parameters['id']!),
    ));
  }
} 