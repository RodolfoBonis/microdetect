import 'package:get/get.dart';
import 'package:microdetect/core/models/app_paths_model.dart';
import 'package:microdetect/features/annotation/pages/annotation_page.dart';
import 'package:microdetect/features/app_root/bindings/app_root_binding.dart';
import 'package:microdetect/features/app_root/pages/app_root_page.dart';
import 'package:microdetect/features/backend_monitor/bindings/backend_monitor_binding.dart';
import 'package:microdetect/features/backend_monitor/pages/backend_monitor_page.dart';
import 'package:microdetect/features/camera/pages/camera_page.dart';
import 'package:microdetect/features/home/bindings/home_binding.dart';
import 'package:microdetect/features/home/pages/home_page.dart';
import 'package:microdetect/features/not-found/pages/not_found_page.dart';
import 'package:microdetect/features/settings/pages/settings_page.dart';
import 'package:microdetect/features/settings/bindings/settings_binding.dart';
import 'package:microdetect/features/camera/bindings/camera_binding.dart';
import 'package:microdetect/features/datasets/bindings/dataset_binding.dart';
import 'package:microdetect/features/datasets/bindings/dataset_detail_binding.dart';
import 'package:microdetect/features/datasets/pages/dataset_detail_page.dart';
import 'package:microdetect/features/datasets/pages/datasets_page.dart';
import 'package:microdetect/features/annotation/bindings/annotation_binding.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';
import 'package:microdetect/features/datasets/services/dataset_service.dart';

part 'app_routes.dart';

/// Middleware para garantir que os controllers essenciais estejam disponíveis
class DependencyMiddleware extends GetMiddleware {

  @override
  GetPage? onPageCalled(GetPage? page) {
    if (page != null) {
      if (page.path.regex.hasMatch(AppRoutes.datasets)) {
        _ensureEssentialControllersExist();
      }
    }
    return super.onPageCalled(page);
  }

  /// Garante que os controllers essenciais estejam registrados
  void _ensureEssentialControllersExist() {
    // Verificar e registrar DatasetService
    if (!Get.isRegistered<DatasetService>(tag: 'datasetService')) {
      Get.put<DatasetService>(
        DatasetService(),
        tag: 'datasetService',
        permanent: true
      );
    }

    // Verificar e registrar DatasetController
    if (!Get.isRegistered<DatasetController>(tag: 'datasetController')) {
      Get.put<DatasetController>(
        DatasetController(),
        tag: 'datasetController',
        permanent: true
      );
    }
  }
}

abstract class AppPages {
  static final pageRoutes = [
    GetPage(
      name: _Paths.root.path,
      page: () => AppRootPage(),
      preventDuplicates: true,
      binding: AppRootBinding(),
      middlewares: [DependencyMiddleware()],
      participatesInRootNavigator: true,
      children: [
        GetPage(
          name: _Paths.home.path,
          page: () {
            return const HomePage();
          },
          preventDuplicates: true,
          transition: Transition.fade,
          binding: HomeBinding(),
        ),
        GetPage(
          name: _Paths.settings.path,
          page: () {
            return const SettingsPage();
          },
          preventDuplicates: true,
          transition: Transition.fade,
          binding: SettingsBinding(),
        ),
        GetPage(
          name: _Paths.camera.path,
          page: () {
            return const CameraPage();
          },
          preventDuplicates: true,
          transition: Transition.fade,
          bindings: [
            DatasetBinding(),
            CameraBinding(),
          ],
        ),
        GetPage(
            name: _Paths.datasets.path,
            page: () {
              return const DatasetsPage();
            },
            preventDuplicates: true,
            binding: DatasetBinding(),
            transition: Transition.fade,
            children: [
              GetPage(
                name: _Paths.datasetDetail.path,
                page: () {
                  return const DatasetDetailPage();
                },
                preventDuplicates: true,
                binding: DatasetDetailBinding(),
              ),
            ]),
        GetPage(
          name: _Paths.annotations.path,
          page: () {
            return const AnnotationPage();
          },
          preventDuplicates: true,
          transition: Transition.fade,
          bindings: [
            DatasetBinding(),
            AnnotationBinding(),
          ],
        ),
        // GetPage(
        //   name: _Paths.training.path,
        //   page: () => TrainingView(),
        // ),
        // GetPage(
        //   name: _Paths.inference.path,
        //   page: () => InferenceView(),
        // ),
        // GetPage(
        //   name: _Paths.analysis.path,
        //   page: () => AnalysisView(),
        // ),
        GetPage(
          name: _Paths.notFound.path,
          page: () => NotFoundPage(title: Get.arguments.title),
        ),
      ],
    ),
    GetPage(
      name: _Paths.backendMonitor.path,
      page: () => const BackendMonitorPage(),
      binding: BackendMonitorBinding(),
    ),
  ];
}
