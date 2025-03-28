// lib/features/backend_monitor/widgets/loading_screen_widget.dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/backend_monitor_controller.dart';
import '../../../core/utils/logger_util.dart';
import '../../../design_system/app_colors.dart';
import '../../../design_system/app_typography.dart';
import '../../../design_system/app_borders.dart';
import 'package:microdetect/core/models/check_item_model.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'progress_steps_widget.dart';
import 'log_console_widget.dart';

class LoadingScreenWidget extends StatelessWidget {
  const LoadingScreenWidget({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<BackendMonitorController>();

    return Center(
      child: SingleChildScrollView(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 600),
          padding: const EdgeInsets.all(AppSpacing.large),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Logo ou ícone de carregamento
              const SizedBox(
                width: 100,
                height: 100,
                child: CircularProgressIndicator(
                  color: AppColors.primary,
                  strokeWidth: 4,
                ),
              ),
              const SizedBox(height: AppSpacing.medium),

              // Título e descrição
              Text(
                'Inicializando Backend',
                textAlign: TextAlign.center,
                style: AppTypography.headlineLarge(context),
              ),
              const SizedBox(height: AppSpacing.small),
              Obx(() => Text(
                    controller.statusMessage.value,
                    textAlign: TextAlign.center,
                    style: AppTypography.bodyLarge(context),
                  )),
              const SizedBox(height: AppSpacing.large),

              // Widget de progresso
              Obx(() => ProgressStepsWidget(
                    checkItems: controller.getCheckItems(),
                    active: true,
                  )),

              const SizedBox(height: AppSpacing.large),

              // Console de logs (compacto)
              SizedBox(
                  height: 250,
                  child: LogConsoleWidget(
                    logs: controller.logs,
                    scrollToBottom: true,
                  )),

              const SizedBox(height: AppSpacing.large),

              // Informações de tempo
              Obx(() => Text(
                    'Tempo decorrido: ${_formatDuration(controller.initializationTime.value)}',
                    style: AppTypography.bodyMedium(context).copyWith(
                      color: ThemeColors.textSecondary(context),
                    ),
                  )),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    String twoDigitMinutes = twoDigits(duration.inMinutes.remainder(60));
    String twoDigitSeconds = twoDigits(duration.inSeconds.remainder(60));

    if (duration.inHours > 0) {
      return '${duration.inHours}:$twoDigitMinutes:$twoDigitSeconds';
    } else {
      return '$twoDigitMinutes:$twoDigitSeconds';
    }
  }
}
