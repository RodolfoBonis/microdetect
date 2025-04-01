import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/features/training/controllers/training_controller.dart';
import 'package:microdetect/features/training/models/training_session.dart';
import 'package:microdetect/features/training/widgets/charts/resource_usage_gauge.dart';
import 'package:percent_indicator/percent_indicator.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_borders.dart';

import '../charts/metrics_line_chart.dart';

/// Widget para exibir e acompanhar o progresso de treinamento em tempo real
class TrainingProgressTracker extends StatelessWidget {
  /// Sessão de treinamento
  final TrainingSession session;

  /// Construtor
  const TrainingProgressTracker({
    Key? key,
    required this.session,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<TrainingController>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Obx(() {
      // Se o treinamento estiver pausado
      if (session.status == 'paused') {
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.pause_circle_outline,
                size: 64,
                color: AppColors.warning,
              ),
              const SizedBox(height: 16),
              Text(
                'Treinamento Pausado',
                style: AppTypography.titleMedium(context),
              ),
              const SizedBox(height: 8),
              Text(
                'O treinamento está pausado temporariamente.',
                style: AppTypography.bodyMedium(context),
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: () => controller.resumeTraining(session.id),
                icon: const Icon(Icons.play_arrow),
                label: const Text('Retomar Treinamento'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: AppSpacing.paddingMedium,
                ),
              ),
            ],
          ),
        );
      }

      // Treinamento em execução
      return RefreshIndicator(
        onRefresh: () async {
          await controller.selectTrainingSession(session.id);
        },
        child: SingleChildScrollView(
          padding: AppSpacing.paddingMedium,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Progresso atual
              _buildProgressSection(context, controller),

              // Gráficos de métricas
              _buildMetricsSection(context, controller),

              // Uso de recursos
              _buildResourceSection(context, controller),
            ],
          ),
        ),
      );
    });
  }

  /// Constrói a seção de progresso atual
  Widget _buildProgressSection(BuildContext context, TrainingController controller) {
    return Container(
      margin: AppSpacing.paddingMedium,
      padding: AppSpacing.paddingMedium,
      decoration: BoxDecoration(
        color: ThemeColors.surface(context),
        borderRadius: AppBorders.medium,
        boxShadow: ThemeColors.boxShadow(context, level: ShadowLevel.small),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Título da seção
          Row(
            children: [
              Icon(
                Icons.timeline,
                size: 20,
                color: AppColors.primary,
              ),
              const SizedBox(width: 8),
              Text(
                'Progresso do Treinamento',
                style: AppTypography.titleSmall(context),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Indicador de progresso circular
          Center(
            child: CircularPercentIndicator(
              radius: 80.0,
              lineWidth: 15.0,
              percent: controller.currentEpoch.value /
                  (controller.totalEpochs.value > 0 ? controller.totalEpochs.value : 100),
              center: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    '${controller.currentEpoch.value}',
                    style: AppTypography.titleLarge(context),
                  ),
                  Text(
                    'de ${controller.totalEpochs.value}',
                    style: AppTypography.bodySmall(context).copyWith(
                      color: ThemeColors.textSecondary(context),
                    ),
                  ),
                ],
              ),
              progressColor: AppColors.primary,
              backgroundColor: ThemeColors.surfaceVariant(context),
              circularStrokeCap: CircularStrokeCap.round,
              animation: true,
              animationDuration: 500,
            ),
          ),
          const SizedBox(height: 16),

          // Progresso em texto
          Center(
            child: Text(
              'Época ${controller.currentEpoch.value} de ${controller.totalEpochs.value}',
              style: AppTypography.titleSmall(context),
            ),
          ),
          const SizedBox(height: 8),

          // Barra de progresso linear
          LinearPercentIndicator(
            lineHeight: 16.0,
            percent: controller.currentEpoch.value /
                (controller.totalEpochs.value > 0 ? controller.totalEpochs.value : 100),
            backgroundColor: ThemeColors.surfaceVariant(context),
            progressColor: AppColors.primary,
            animation: true,
            animationDuration: 500,
            center: Text(
              '${(controller.currentEpoch.value / controller.totalEpochs.value * 100).toStringAsFixed(0)}%',
              style: AppTypography.bodySmall(context).copyWith(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
            barRadius: Radius.circular(AppBorders.radiusSmall),
          ),
          const SizedBox(height: 16),

          // Status atual
          if (controller.trainingStatus.value.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 8.0),
              child: Row(
                children: [
                  Icon(
                    Icons.info_outline,
                    size: 16,
                    color: ThemeColors.textSecondary(context),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Status: ${controller.trainingStatus.value}',
                    style: AppTypography.bodyMedium(context),
                  ),
                ],
              ),
            ),

          // Métricas atuais
          const SizedBox(height: 16),
          Row(
            children: [
              _buildMetricBadge(
                context: context,
                label: 'Loss',
                value: controller.lossHistory.isNotEmpty
                    ? controller.lossHistory.last.toStringAsFixed(4)
                    : 'N/A',
                color: AppColors.error,
              ),
              const SizedBox(width: 8),
              _buildMetricBadge(
                context: context,
                label: 'mAP50',
                value: controller.map50History.isNotEmpty
                    ? '${(controller.map50History.last * 100).toStringAsFixed(1)}%'
                    : 'N/A',
                color: AppColors.primary,
              ),
              const SizedBox(width: 8),
              _buildMetricBadge(
                context: context,
                label: 'Precisão',
                value: controller.precisionHistory.isNotEmpty
                    ? '${(controller.precisionHistory.last * 100).toStringAsFixed(1)}%'
                    : 'N/A',
                color: AppColors.secondary,
              ),
              const SizedBox(width: 8),
              _buildMetricBadge(
                context: context,
                label: 'Recall',
                value: controller.recallHistory.isNotEmpty
                    ? '${(controller.recallHistory.last * 100).toStringAsFixed(1)}%'
                    : 'N/A',
                color: AppColors.tertiary,
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Constrói a seção de gráficos de métricas
  Widget _buildMetricsSection(BuildContext context, TrainingController controller) {
    // Verificar se já existem dados para exibir gráficos
    final hasLossData = controller.lossHistory.isNotEmpty;
    final hasMapData = controller.map50History.isNotEmpty;
    final hasPrecisionRecallData = controller.precisionHistory.isNotEmpty &&
        controller.recallHistory.isNotEmpty;

    if (!hasLossData && !hasMapData) {
      return Container(
        margin: AppSpacing.paddingMedium,
        padding: AppSpacing.paddingMedium,
        decoration: BoxDecoration(
          color: ThemeColors.surface(context),
          borderRadius: AppBorders.medium,
          boxShadow: ThemeColors.boxShadow(context, level: ShadowLevel.small),
        ),
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(32.0),
            child: Column(
              children: [
                Icon(
                  Icons.analytics_outlined,
                  size: 48,
                  color: ThemeColors.textSecondary(context),
                ),
                const SizedBox(height: 16),
                Text(
                  'Aguardando dados de métricas',
                  style: AppTypography.titleSmall(context),
                ),
                const SizedBox(height: 8),
                Text(
                  'Os gráficos serão exibidos quando os dados estiverem disponíveis.',
                  style: AppTypography.bodyMedium(context),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      );
    }

    // Preparar dados para os gráficos
    final epochs = List<double>.generate(
        controller.currentEpoch.value,
            (i) => i.toDouble()
    );

    return Column(
      children: [
        // Gráfico de Loss
        if (hasLossData)
          Container(
            margin: AppSpacing.paddingMedium,
            decoration: BoxDecoration(
              color: ThemeColors.surface(context),
              borderRadius: AppBorders.medium,
              boxShadow: ThemeColors.boxShadow(context, level: ShadowLevel.small),
            ),
            child: MetricsLineChart(
              xValues: epochs,
              series: [
                MetricSeries(
                  name: 'Loss',
                  values: controller.lossHistory,
                  color: AppColors.error,
                  showAreaGradient: true,
                ),
              ],
              title: 'Loss ao longo do treinamento',
              yAxisTitle: 'Loss',
            ),
          ),

        // Gráfico de mAP50
        if (hasMapData)
          Container(
            margin: AppSpacing.paddingMedium,
            decoration: BoxDecoration(
              color: ThemeColors.surface(context),
              borderRadius: AppBorders.medium,
              boxShadow: ThemeColors.boxShadow(context, level: ShadowLevel.small),
            ),
            child: MetricsLineChart(
              xValues: epochs.sublist(0, controller.map50History.length),
              series: [
                MetricSeries(
                  name: 'mAP50',
                  values: controller.map50History,
                  color: AppColors.primary,
                  showAreaGradient: true,
                ),
              ],
              title: 'mAP50 ao longo do treinamento',
              yAxisTitle: 'mAP50',
            ),
          ),

        // Gráfico de Precisão e Recall
        if (hasPrecisionRecallData)
          Container(
            margin: AppSpacing.paddingMedium,
            decoration: BoxDecoration(
              color: ThemeColors.surface(context),
              borderRadius: AppBorders.medium,
              boxShadow: ThemeColors.boxShadow(context, level: ShadowLevel.small),
            ),
            child: MetricsLineChart(
              xValues: epochs.sublist(0, controller.precisionHistory.length),
              series: [
                MetricSeries(
                  name: 'Precisão',
                  values: controller.precisionHistory,
                  color: AppColors.secondary,
                ),
                MetricSeries(
                  name: 'Recall',
                  values: controller.recallHistory,
                  color: AppColors.tertiary,
                ),
              ],
              title: 'Precisão e Recall',
              yAxisTitle: 'Valor',
            ),
          ),
      ],
    );
  }

  /// Constrói a seção de uso de recursos
  Widget _buildResourceSection(BuildContext context, TrainingController controller) {
    // Verificar se há dados de uso de recursos
    final hasResourceData = controller.cpuUsage.value > 0 ||
        controller.memoryUsage.value > 0 ||
        controller.gpuUsage.value > 0;

    if (!hasResourceData) {
      return const SizedBox.shrink();
    }

    return Container(
      margin: AppSpacing.paddingMedium,
      padding: AppSpacing.paddingMedium,
      decoration: BoxDecoration(
        color: ThemeColors.surface(context),
        borderRadius: AppBorders.medium,
        boxShadow: ThemeColors.boxShadow(context, level: ShadowLevel.small),
      ),
      child: ResourceUsageGauge(
        cpuUsage: controller.cpuUsage.value,
        memoryUsage: controller.memoryUsage.value,
        gpuUsage: controller.gpuUsage.value > 0 ? controller.gpuUsage.value : null,
        title: 'Uso de Recursos',
      ),
    );
  }

  /// Constrói um badge de métrica
  Widget _buildMetricBadge({
    required BuildContext context,
    required String label,
    required String value,
    required Color color,
  }) {
    return Expanded(
      child: Container(
        padding: AppSpacing.paddingSmall,
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: AppBorders.small,
        ),
        child: Column(
          children: [
            Text(
              label,
              style: AppTypography.bodySmall(context).copyWith(
                color: color,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: AppTypography.labelMedium(context).copyWith(
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}