import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/backend_monitor_controller.dart';
import '../widgets/loading_screen_widget.dart';
import '../widgets/error_screen_widget.dart';
import '../widgets/stalled_screen_widget.dart';
import '../widgets/status_info_widget.dart';
import '../widgets/progress_steps_widget.dart';
import '../widgets/log_console_widget.dart';
import '../../../core/enums/backend_status_enum.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';

class BackendMonitorPage extends GetView<BackendMonitorController> {
  // Rota para a qual navegaremos quando o backend estiver rodando
  final String rootRoute;

  const BackendMonitorPage({this.rootRoute = '/root', Key? key})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Definir a rota de destino no controller
    controller.setRootRoute(rootRoute);
    
    return Scaffold(
      backgroundColor: Get.isDarkMode ? AppColors.surfaceDark : AppColors.surfaceLight,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.large),
          child: Obx(() => _buildContent()),
        ),
      ),
    );
  }

  Widget _buildContent() {
    // Verificar se há algum erro ou se a inicialização está demorando muito
    if (controller.status.value == BackendStatus.error) {
      return ErrorScreenWidget();
    } else if (controller.isLongRunning.value || controller.noActivity.value) {
      return const StalledScreenWidget();
    } else if (controller.isInitializing.value && !controller.isRunning.value) {
      return const LoadingScreenWidget();
    }

    // Layout normal
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: AppSpacing.medium),

        // Informações de status e versão
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // Status e informações gerais do backend
            Expanded(
              flex: 3,
              child: StatusInfoWidget(
                status: controller.status.value,
                statusMessage: controller.statusMessage.value,
                isRunning: controller.isRunning.value,
                isInitializing: controller.isInitializing.value,
                initTime: controller.initializationTime.value,
              ),
            ),

            // Informações de versão e botões de atualização
            Expanded(
              flex: 2,
              child: _buildVersionInfo(),
            ),
          ],
        ),

        const SizedBox(height: AppSpacing.medium),

        // Steps de progresso
        Obx(() => ProgressStepsWidget(
              checkItems: controller.getCheckItems(),
              active: controller.isInitializing.value,
            )),

        const SizedBox(height: AppSpacing.medium),

        // Console de logs
        Expanded(
            child: LogConsoleWidget(
          logs: controller.logs,
          scrollToBottom: true,
        )),

        const SizedBox(height: AppSpacing.medium),

        // Botões de ação
        _buildActionButtons(),
      ],
    );
  }

  Widget _buildVersionInfo() {
    return Card(
      elevation: 2,
      color: ThemeColors.surface(Get.context!),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: ThemeColors.border(Get.context!)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.medium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Informações de Versão',
              style: AppTypography.titleMedium(Get.context!),
            ),
            const SizedBox(height: AppSpacing.small),

            // Versão atual
            Row(
              children: [
                Text(
                  'Versão atual:',
                  style: AppTypography.bodyMedium(Get.context!).copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(width: 8),
                Obx(() => Text(
                    controller.currentVersion.value.isEmpty
                        ? 'Carregando...'
                        : controller.currentVersion.value,
                    style: AppTypography.bodyMedium(Get.context!))),
              ],
            ),
            const SizedBox(height: AppSpacing.xSmall),

            // Versão disponível
            Row(
              children: [
                Text(
                  'Versão disponível:',
                  style: AppTypography.bodyMedium(Get.context!).copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(width: 8),
                Obx(() => Text(
                    controller.assetVersion.value.isEmpty
                        ? 'Carregando...'
                        : controller.assetVersion.value,
                    style: AppTypography.bodyMedium(Get.context!))),
              ],
            ),
            const SizedBox(height: AppSpacing.small),

            // Status de atualização
            Obx(() => controller.updateAvailable
                ? Row(
                    children: [
                      Icon(
                        Icons.new_releases,
                        color: AppColors.primary,
                        size: 16,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        'Atualização disponível!',
                        style: AppTypography.bodySmall(Get.context!).copyWith(
                          color: AppColors.primary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  )
                : Row(
                    children: [
                      Icon(
                        Icons.check_circle,
                        size: 16,
                        color: AppColors.success,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        'Versão atualizada',
                        style: AppTypography.bodySmall(Get.context!).copyWith(
                          color: AppColors.success,
                        ),
                      ),
                    ],
                  )),

            const SizedBox(height: AppSpacing.medium),

            // Botões
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                // Botão verificar atualizações
                OutlinedButton.icon(
                  onPressed: controller.isInitializing.value ||
                          controller.isUpdating.value
                      ? null
                      : controller.checkForUpdates,
                  icon: const Icon(Icons.refresh, size: 16),
                  label: const Text('Verificar'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.small,
                      vertical: 4,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(6),
                    ),
                  ),
                ),
                const SizedBox(width: AppSpacing.small),

                // Botão atualizar
                Obx(() => ElevatedButton.icon(
                      onPressed: controller.isInitializing.value ||
                              controller.isUpdating.value ||
                              !controller.updateAvailable
                          ? null
                          : controller.updateBackend,
                      icon: controller.isUpdating.value
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor:
                                    AlwaysStoppedAnimation<Color>(Colors.white),
                              ),
                            )
                          : const Icon(Icons.system_update, size: 16),
                      label: Text(controller.isUpdating.value
                          ? 'Atualizando...'
                          : 'Atualizar'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.small,
                          vertical: 4,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(6),
                        ),
                      ),
                    )),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // Restart Button
        OutlinedButton.icon(
          icon: const Icon(Icons.refresh),
          label: const Text('Reiniciar Backend'),
          onPressed:
              controller.isInitializing.value || controller.isUpdating.value
                  ? null
                  : controller.restartBackend,
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.medium,
              vertical: AppSpacing.small,
            ),
          ),
        ),
        const SizedBox(width: AppSpacing.medium),

        // Force Restart Button (more aggressive restart)
        ElevatedButton.icon(
          icon: const Icon(Icons.restart_alt),
          label: const Text('Forçar Reinício'),
          onPressed:
              controller.isInitializing.value || controller.isUpdating.value
                  ? null
                  : controller.forceRestartBackend,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.error,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.medium,
              vertical: AppSpacing.small,
            ),
          ),
        ),

        // Diagnostics Button
        const SizedBox(width: AppSpacing.medium),
        OutlinedButton.icon(
          icon: const Icon(Icons.bug_report),
          label: const Text('Diagnóstico'),
          onPressed:
              controller.isInitializing.value || controller.isUpdating.value
                  ? null
                  : controller.runDiagnostics,
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.medium,
              vertical: AppSpacing.small,
            ),
          ),
        ),
      ],
    );
  }
}
