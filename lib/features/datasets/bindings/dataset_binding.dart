import 'package:get/get.dart';
import '../controllers/dataset_controller.dart';
import '../services/dataset_service.dart';

class DatasetBinding extends Bindings {
  @override
  void dependencies() {
    // Registrar o serviço de datasets
    Get.lazyPut<DatasetService>(() => DatasetService());
    
    // Registrar o controller de datasets
    Get.lazyPut<DatasetController>(() => DatasetController());
  }
} 