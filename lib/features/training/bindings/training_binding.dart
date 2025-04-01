import 'package:get/get.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';

import '../controllers/hyperparameter_search_controller.dart';
import '../controllers/training_controller.dart';
import '../services/training_service.dart';

/// Binding para o módulo de treinamento
class TrainingBinding implements Bindings {
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

    // Registrar serviço de treinamento
    Get.lazyPut<TrainingService>(
          () => TrainingService(),
      fenix: true,
    );

    // Registrar controllers
    Get.lazyPut<TrainingController>(
          () => TrainingController(),
      fenix: true,
    );

    Get.lazyPut<HyperparameterSearchController>(
          () => HyperparameterSearchController(),
      fenix: true,
    );
  }
}