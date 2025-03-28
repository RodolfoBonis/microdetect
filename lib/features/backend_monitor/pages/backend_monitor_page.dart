import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/enums/backend_status_enum.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/backend_monitor/controllers/backend_monitor_controller.dart';
import 'package:microdetect/features/backend_monitor/widgets/log_console_widget.dart';
import 'package:microdetect/features/backend_monitor/widgets/progress_steps_widget.dart';
import 'package:microdetect/features/backend_monitor/widgets/status_info_widget.dart';

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
          child: Obx(() => Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Cabeçalho com alerta se necessário (erro, travamento, etc)
              _buildHeaderAlert(context),

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
                    child: _buildVersionInfo(context),
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
              _buildActionButtons(context),
            ],
          )),
        ),
      ),
    );
  }

  // Construir alerta de cabeçalho para estados especiais (erro, travamento, etc)
  Widget _buildHeaderAlert(BuildContext context) {
    // Se estiver em erro
    if (controller.status.value == BackendStatus.error) {
      return _buildErrorAlert(context);
    }
    // Se estiver demorando muito ou sem atividade
    else if (controller.isLongRunning.value || controller.noActivity.value) {
      return _buildStalledAlert(context);
    }
    // Se estiver inicializando
    else if (controller.isInitializing.value && !controller.isRunning.value) {
      return _buildLoadingAlert(context);
    }
    // Estado normal - sem alerta
    return const SizedBox.shrink();
  }

  // Alerta para estado de erro
  Widget _buildErrorAlert(BuildContext context) {
    return Card(
      color: AppColors.error.withOpacity(0.1),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: AppColors.error),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.medium),
        child: Column(
          children: [
            Row(
              children: [
                const Icon(
                  Icons.error_outline,
                  color: AppColors.error,
                  size: 32,
                ),
                const SizedBox(width: AppSpacing.medium),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Erro no Backend',
                        style: AppTypography.titleLarge(context).copyWith(
                          color: AppColors.error,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.xSmall),
                      Text(
                        controller.getDetailedErrorMessage(),
                        style: AppTypography.bodyMedium(context),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.medium),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                OutlinedButton.icon(
                  onPressed: controller.runDiagnostics,
                  icon: const Icon(Icons.search),
                  label: const Text('Diagnóstico'),
                ),
                const SizedBox(width: AppSpacing.medium),
                ElevatedButton.icon(
                  onPressed: controller.forceRestartBackend,
                  icon: const Icon(Icons.restart_alt),
                  label: const Text('Reiniciar'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // Alerta para inicialização travada ou sem atividade
  Widget _buildStalledAlert(BuildContext context) {
    return Card(
      color: AppColors.warning.withOpacity(0.1),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: AppColors.warning),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.medium),
        child: Column(
          children: [
            Row(
              children: [
                const Icon(
                  Icons.hourglass_top,
                  color: AppColors.warning,
                  size: 32,
                ),
                const SizedBox(width: AppSpacing.medium),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        controller.noActivity.value
                            ? 'Sem Atividade Detectada'
                            : 'Inicialização Demorada',
                        style: AppTypography.titleLarge(context).copyWith(
                          color: AppColors.warning,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.xSmall),
                      Text(
                        controller.noActivity.value
                            ? 'O backend não está respondendo. Não foi detectada atividade nos últimos minutos.'
                            : 'A inicialização do backend está demorando mais do que o esperado.',
                        style: AppTypography.bodyMedium(context),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.medium),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                OutlinedButton.icon(
                  onPressed: controller.continueWaiting,
                  icon: const Icon(Icons.timelapse),
                  label: const Text('Continuar Aguardando'),
                ),
                const SizedBox(width: AppSpacing.medium),
                ElevatedButton.icon(
                  onPressed: controller.forceRestartBackend,
                  icon: const Icon(Icons.restart_alt),
                  label: const Text('Reiniciar'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // Alerta para estado de carregamento/inicialização
  Widget _buildLoadingAlert(BuildContext context) {
    return Card(
      color: AppColors.info.withOpacity(0.1),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: AppColors.info),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.medium),
        child: Row(
          children: [
            const SizedBox(
              width: 32,
              height: 32,
              child: CircularProgressIndicator(
                strokeWidth: 3,
                valueColor: AlwaysStoppedAnimation<Color>(AppColors.info),
              ),
            ),
            const SizedBox(width: AppSpacing.medium),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Inicializando Backend',
                    style: AppTypography.titleLarge(context).copyWith(
                      color: AppColors.info,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.xSmall),
                  Text(
                    'O processo de inicialização está em andamento. ' +
                        'Tempo decorrido: ${_formatDuration(controller.initializationTime.value)}',
                    style: AppTypography.bodyMedium(context),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVersionInfo(BuildContext context) {
    return Card(
      elevation: 2,
      color: ThemeColors.surface(context),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: ThemeColors.border(context)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.medium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Informações de Versão',
              style: AppTypography.titleMedium(context),
            ),
            const SizedBox(height: AppSpacing.small),

            // Versão atual
            Row(
              children: [
                Text(
                  'Versão atual:',
                  style: AppTypography.bodyMedium(context).copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(width: 8),
                Obx(() => Text(
                    controller.currentVersion.value.isEmpty
                        ? 'Carregando...'
                        : controller.currentVersion.value,
                    style: AppTypography.bodyMedium(context))),
              ],
            ),
            const SizedBox(height: AppSpacing.xSmall),

            // Versão disponível
            Row(
              children: [
                Text(
                  'Versão disponível:',
                  style: AppTypography.bodyMedium(context).copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(width: 8),
                Obx(() => Text(
                    controller.latestVersion.value.isEmpty
                        ? 'Carregando...'
                        : controller.latestVersion.value,
                    style: AppTypography.bodyMedium(context))),
              ],
            ),
            const SizedBox(height: AppSpacing.small),

            // Status de atualização
            Obx(() => controller.updateAvailable
                ? Row(
              children: [
                const Icon(
                  Icons.new_releases,
                  color: AppColors.primary,
                  size: 16,
                ),
                const SizedBox(width: 4),
                Text(
                  'Atualização disponível!',
                  style: AppTypography.bodySmall(context).copyWith(
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
                  style: AppTypography.bodySmall(context).copyWith(
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

  Widget _buildActionButtons(BuildContext context) {
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