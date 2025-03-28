import 'package:get/get.dart';
import 'package:microdetect/core/models/app_paths_model.dart';
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

part 'app_routes.dart';

abstract class AppPages {
  static final pageRoutes = [
    GetPage(
      name: _Paths.root.path,
      page: () => AppRootPage(),
      preventDuplicates: true,
      binding: AppRootBinding(),
      children: [
        GetPage(
          name: _Paths.home.path,
          page: () => const HomePage(),
          binding: HomeBinding(),
        ),
        GetPage(
          name: _Paths.settings.path,
          page: () => const SettingsPage(),
          binding: SettingsBinding(),
        ),
        GetPage(
          name: _Paths.camera.path,
          page: () => const CameraPage(),
          binding: CameraBinding(),
        ),
        GetPage(
          name: _Paths.datasets.path,
          page: () => const DatasetsPage(),
          binding: DatasetBinding(),
          children: [
            GetPage(
              name: _Paths.datasetDetail.path,
              page: () => const DatasetDetailPage(),
              binding: DatasetDetailBinding(),
            ),
          ]
        ),

        // GetPage(
        //   name: _Paths.annotations.path,
        //   page: () => AnnotationsView(),
        // ),
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
