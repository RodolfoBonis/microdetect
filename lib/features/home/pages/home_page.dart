import 'dart:async';

import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/services/system_status_service.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';

import '../controllers/home_controller.dart';
import '../widgets/activities_section_widget.dart';
import '../widgets/metrics_section_widget.dart';
import '../widgets/recent_datasets_section_widget.dart';
import '../widgets/system_status_section_widget.dart';

class HomePage extends GetView<HomeController> {
  const HomePage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Garantir que o controller existe de forma permanente
    final homeController = Get.find<HomeController>();
    
    return Stack(
      children: [
        // Conteúdo principal
        Container(
          color: Get.isDarkMode ? AppColors.surfaceDark : AppColors.white,
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.xLarge),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [

                // Cards de métricas
                const MetricsSectionWidget(),
                const SizedBox(height: AppSpacing.large),

                // Datasets recentes e atividades
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Coluna de datasets recentes
                    Expanded(
                      flex: 3,
                      child: RecentDatasetsSectionWidget(
                        onViewAllPressed: () {
                          // Navegar para a página de datasets
                        },
                      ),
                    ),
                    const SizedBox(width: AppSpacing.medium),

                    // Coluna de atividades recentes
                    Expanded(
                      flex: 2,
                      child: ActivitiesSectionWidget(
                        onViewMorePressed: () {
                          // Navegar para histórico de atividades
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.large),

                // Status do sistema
                Obx(() => SystemStatusSectionWidget(
                  systemStatus: controller.systemStatus.value,
                )),
              ],
            ),
          ),
        ),

        // Indicador de carregamento
        Obx(() => controller.isLoading.value
          ? Container(
              color: Theme.of(context).brightness == Brightness.dark
                  ? AppColors.black.withValues(alpha: 0.5)
                  : AppColors.white.withValues(alpha: 0.7),
              child: const Center(
                child: CircularProgressIndicator(),
              ),
            )
          : const SizedBox.shrink()
        ),
      ],
    );
  }
} 