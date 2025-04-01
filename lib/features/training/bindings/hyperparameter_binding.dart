import 'package:get/get.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';

import '../controllers/hyperparameter_search_controller.dart';
import '../controllers/training_controller.dart';
import '../services/training_service.dart';

/// Binding para o módulo de busca de hiperparâmetros
class HyperparameterBinding implements Bindings {
  @override
  void dependencies() {
    // Verificar se o controller de dataset já está disponível
    if (!Get.isRegistered<DatasetController>(tag: 'datasetController')) {
      Get.lazyPut<DatasetController>(
            () => DatasetController(),
        tag: 'datasetController',
        fenix: true,
      );
    }

    // Verificar se o serviço de treinamento já está disponível
    if (!Get.isRegistered<TrainingService>()) {
      Get.lazyPut<TrainingService>(
            () => TrainingService(),
        fenix: true,
      );
    }

    // Verificar se o controller de treinamento já está disponível
    if (!Get.isRegistered<TrainingController>()) {
      Get.lazyPut<TrainingController>(
            () => TrainingController(),
        fenix: true,
      );
    }

    // Registrar controller de busca de hiperparâmetros
    Get.lazyPut<HyperparameterSearchController>(
          () => HyperparameterSearchController(),
      fenix: true,
    );
  }
}