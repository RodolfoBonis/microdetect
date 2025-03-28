import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import '../controllers/backend_monitor_controller.dart';

class StalledScreenWidget extends StatelessWidget {
  const StalledScreenWidget({Key? key}) : super(key: key);

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
              const Icon(
                Icons.hourglass_top,
                color: AppColors.warning,
                size: 80,
              ),
              const SizedBox(height: AppSpacing.medium),
              Obx(
                () => Text(
                  controller.noActivity.value
                      ? 'Sem Atividade Detectada'
                      : 'Inicialização Demorada',
                  textAlign: TextAlign.center,
                  style: AppTypography.headlineLarge(context).copyWith(
                    color: AppColors.warning,
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.medium),
              Obx(() => Text(
                    controller.noActivity.value
                        ? 'O backend não está respondendo. Não foi detectada atividade nos últimos minutos.'
                        : 'A inicialização do backend está demorando mais do que o esperado.',
                    textAlign: TextAlign.center,
                    style: AppTypography.bodyLarge(context),
                  )),
              const SizedBox(height: AppSpacing.large),

              // Card com informações de tempo
              Card(
                elevation: 3,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(color: ThemeColors.border(context)),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.medium),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Informações de Tempo',
                        style: AppTypography.titleMedium(context),
                      ),
                      const SizedBox(height: AppSpacing.small),
                      Obx(() => Column(
                            children: [
                              _buildInfoRow(
                                context,
                                'Tempo de inicialização:',
                                _formatDuration(
                                    controller.initializationTime.value),
                                Icons.timer,
                                color: AppColors.warning,
                              ),
                              const SizedBox(height: AppSpacing.xSmall),
                              _buildInfoRow(
                                context,
                                'Último log recebido:',
                                '${_getTimeAgo(controller.lastLogTime.value)}',
                                Icons.history,
                                color: controller.noActivity.value
                                    ? AppColors.error
                                    : AppColors.warning,
                              ),
                              const SizedBox(height: AppSpacing.xSmall),
                              _buildInfoRow(
                                context,
                                'Etapa atual:',
                                controller.initSteps[
                                    controller.currentStepIndex.value],
                                Icons.list_alt,
                              ),
                            ],
                          )),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: AppSpacing.large),

              // Logs (resumido)
              Card(
                elevation: 3,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(color: ThemeColors.border(context)),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.medium),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Últimos Logs',
                        style: AppTypography.titleMedium(context),
                      ),
                      const SizedBox(height: AppSpacing.small),
                      Container(
                        constraints: const BoxConstraints(maxHeight: 200),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1E1E1E),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        padding: const EdgeInsets.all(AppSpacing.small),
                        child: Obx(() => ListView.builder(
                              itemCount: controller.logs.isEmpty
                                  ? 1
                                  : controller.logs.length > 10
                                      ? 10
                                      : controller.logs.length,
                              itemBuilder: (context, index) {
                                if (controller.logs.isEmpty) {
                                  return const Center(
                                    child: Text(
                                      'Nenhum log disponível',
                                      style: TextStyle(color: Colors.white70),
                                    ),
                                  );
                                }

                                final logIndex = controller.logs.length > 10
                                    ? controller.logs.length - 10 + index
                                    : index;
                                final log = controller.logs[logIndex];

                                return Text(
                                  log,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontFamily: 'monospace',
                                    fontSize: 12,
                                  ),
                                );
                              },
                            )),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: AppSpacing.large),

              // Botões de ação
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  OutlinedButton.icon(
                    onPressed: controller.continueWaiting,
                    icon: const Icon(Icons.timelapse),
                    label: const Text('Continuar Aguardando'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.medium,
                        vertical: AppSpacing.small,
                      ),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.medium),
                  ElevatedButton.icon(
                    onPressed: controller.forceRestartBackend,
                    icon: const Icon(Icons.restart_alt),
                    label: const Text('Reiniciar Processo'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.medium,
                        vertical: AppSpacing.small,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoRow(
      BuildContext context, String label, String value, IconData icon,
      {Color? color}) {
    return Row(
      children: [
        Icon(
          icon,
          size: 16,
          color: color ?? ThemeColors.text(context),
        ),
        const SizedBox(width: 8),
        Text(
          label,
          style: AppTypography.bodyMedium(context).copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(width: 4),
        Expanded(
          child: Text(
            value,
            style: AppTypography.bodyMedium(context).copyWith(
              color: color,
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

  String _getTimeAgo(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inSeconds < 60) {
      return '${difference.inSeconds} segundos atrás';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes} minutos atrás';
    } else if (difference.inHours < 24) {
      return '${difference.inHours} horas atrás';
    } else {
      return '${difference.inDays} dias atrás';
    }
  }
}
