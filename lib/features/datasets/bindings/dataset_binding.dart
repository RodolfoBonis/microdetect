import 'package:get/get.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';
import 'package:microdetect/features/datasets/services/dataset_service.dart';

class DatasetBinding extends Bindings {
  @override
  void dependencies() {
    // Registra o dataset service como permanente
    if (!Get.isRegistered<DatasetService>(tag: 'datasetService')) {
      Get.put<DatasetService>(
        DatasetService(),
        tag: 'datasetService',
        permanent: true,
      );
    }

    // Registra o DatasetController como permanente para manter estado entre navegações
    if (!Get.isRegistered<DatasetController>(tag: 'datasetController')) {
      Get.put<DatasetController>(
        DatasetController(),
        tag: 'datasetController',
        permanent: true,
      );
    }
  }
}
