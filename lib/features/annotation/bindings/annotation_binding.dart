import 'package:get/get.dart';
import 'package:microdetect/features/annotation/controllers/annotation_controller.dart';
import 'package:microdetect/features/annotation/services/annotation_service.dart';
import 'package:microdetect/features/camera/services/camera_service.dart';
import 'package:microdetect/features/datasets/services/dataset_service.dart';

/// Binding para o módulo de anotações
class AnnotationBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<DatasetService>(() => DatasetService());
    // Registrar o serviço como singleton
    Get.lazyPut<AnnotationService>(
      () => AnnotationService(),
      fenix: true,
    );
    
    // Registrar o controlador
    Get.lazyPut<AnnotationController>(
      () => AnnotationController(),
    );
  }
} 