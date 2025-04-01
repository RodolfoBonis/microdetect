import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/widgets/base_page_scaffold.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/design_system/app_badge.dart';

import '../controllers/training_controller.dart';
import '../models/training_session.dart';
import '../models/training_report.dart';
import '../widgets/charts/metrics_line_chart.dart';
import '../widgets/charts/confusion_matrix_widget.dart';
import '../widgets/charts/class_performance_list.dart';
import '../widgets/progress/training_progress_tracker.dart';

/// Página de detalhes do treinamento
class TrainingDetailsPage extends StatefulWidget {
  /// Construtor
  const TrainingDetailsPage({Key? key}) : super(key: key);

  @override
  State<TrainingDetailsPage> createState() => _TrainingDetailsPageState();
}

class _TrainingDetailsPageState extends State<TrainingDetailsPage> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TrainingController _controller = Get.find<TrainingController>();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);

    // Obter ID da sessão a partir dos parâmetros de rota
    final sessionId = int.tryParse(Get.parameters['id'] ?? '');
    if (sessionId != null) {
      // Carregar detalhes da sessão se necessário
      if (_controller.selectedSession.value?.id != sessionId) {
        _controller.selectTrainingSession(sessionId);
      }
    } else {
      // ID inválido, voltar para a lista
      Get.back();
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      if (_controller.isLoading.value) {
        return const BasePageScaffold(
          title: 'Detalhes do Treinamento',
          body: Center(
            child: CircularProgressIndicator(),
          ),
        );
      }

      final session = _controller.selectedSession.value;
      if (session == null) {
        return BasePageScaffold(
          title: 'Detalhes do Treinamento',
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.error_outline,
                  size: 64,
                  color: AppColors.error,
                ),
                const SizedBox(height: 16),
                Text(
                  'Sessão não encontrada',
                  style: AppTypography.titleMedium(context),
                ),
                const SizedBox(height: 16),
                AppButton(
                  label: 'Voltar',
                  onPressed: () => Get.back(),
                  type: AppButtonType.secondary,
                  prefixIcon: Icons.arrow_back,
                ),
              ],
            ),
          ),
        );
      }

      return BasePageScaffold(
        title: session.name,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Atualizar',
            onPressed: () {
              if (session.id > 0) {
                _controller.selectTrainingSession(session.id);
              }
            },
          ),
        ],
        body: Column(
          children: [
            _buildHeader(context, session),
            Expanded(
              child: _buildTabView(context, session),
            ),
          ],
        ),
      );
    });
  }

  /// Constrói o cabeçalho da página
  Widget _buildHeader(BuildContext context, TrainingSession session) {
    return Container(
      padding: AppSpacing.paddingMedium,
      decoration: BoxDecoration(
        color: ThemeColors.surfaceVariant(context),
        border: Border(
          bottom: BorderSide(
            color: ThemeColors.border(context),
            width: 1,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Linha superior com título e status
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      session.name,
                      style: AppTypography.titleMedium(context),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      session.description,
                      style: AppTypography.bodySmall(context).copyWith(
                        color: ThemeColors.textSecondary(context),
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              AppBadge(
                text: session.statusDisplay,
                color: _getStatusColor(session.status),
                prefixIcon: _getStatusIcon(session.status),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Informações do modelo e duração
          Row(
            children: [
              _buildInfoBox(
                context: context,
                label: 'Modelo',
                value: session.fullModelName,
                icon: Icons.model_training,
              ),
              _buildInfoBox(
                context: context,
                label: 'Dataset',
                value: 'ID: ${session.datasetId}',
                icon: Icons.folder,
              ),
              _buildInfoBox(
                context: context,
                label: 'Criado em',
                value: session.createdAtFormatted,
                icon: Icons.calendar_today,
              ),
              _buildInfoBox(
                context: context,
                label: 'Duração',
                value: session.durationFormatted,
                icon: Icons.timer,
              ),
            ],
          ),

          // Botões de ação (se aplicável)
          if (_shouldShowActionButtons(session))
            Padding(
              padding: const EdgeInsets.only(top: 16.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  if (session.canBePaused)
                    AppButton(
                      label: 'Pausar',
                      onPressed: () => _controller.pauseTraining(session.id),
                      type: AppButtonType.secondary,
                      prefixIcon: Icons.pause,
                    ),
                  if (session.canBeResumed) ...[
                    const SizedBox(width: 16),
                    AppButton(
                      label: 'Retomar',
                      onPressed: () => _controller.resumeTraining(session.id),
                      prefixIcon: Icons.play_arrow,
                    ),
                  ],
                  if (session.canBeCancelled) ...[
                    const SizedBox(width: 16),
                    AppButton(
                      label: 'Cancelar',
                      onPressed: () => _showCancelConfirmDialog(context, session.id),
                      type: AppButtonType.secondary,
                      prefixIcon: Icons.stop,
                    ),
                  ],
                ],
              ),
            ),
        ],
      ),
    );
  }

  /// Constrói a visualização em abas
  Widget _buildTabView(BuildContext context, TrainingSession session) {
    return Column(
      children: [
        // Barra de abas
        TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Progresso & Métricas'),
            Tab(text: 'Hiperparâmetros'),
            Tab(text: 'Relatório Final'),
          ],
          labelColor: AppColors.primary,
          unselectedLabelColor: ThemeColors.textSecondary(context),
          indicatorColor: AppColors.primary,
        ),

        // Conteúdo das abas
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              // Aba 1: Progresso e Métricas
              _buildProgressTab(context, session),

              // Aba 2: Hiperparâmetros
              _buildHyperparametersTab(context, session),

              // Aba 3: Relatório Final
              _buildReportTab(context, session),
            ],
          ),
        ),
      ],
    );
  }

  /// Constrói a aba de progresso e métricas
  Widget _buildProgressTab(BuildContext context, TrainingSession session) {
    if (session.status == 'running' || session.status == 'paused') {
      return TrainingProgressTracker(
        session: session,
      );
    }

    // Para sessões concluídas ou com erro
    if (session.status == 'completed') {
      return Obx(() {
        final report = _controller.trainingReport.value;
        if (report == null) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.analytics,
                  size: 64,
                  color: ThemeColors.textSecondary(context),
                ),
                const SizedBox(height: 16),
                Text(
                  'Relatório de métricas não disponível',
                  style: AppTypography.titleSmall(context),
                ),
                const SizedBox(height: 8),
                Text(
                  'O treinamento foi concluído, mas o relatório de métricas não está disponível.',
                  style: AppTypography.bodyMedium(context),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                AppButton(
                  label: 'Carregar Relatório',
                  onPressed: () => _controller.fetchTrainingReport(session.id),
                  type: AppButtonType.secondary,
                  prefixIcon: Icons.refresh,
                ),
              ],
            ),
          );
        }

        // Obter dados históricos
        final epochs = List<double>.generate(
            report.metricsHistory.length,
                (i) => report.metricsHistory[i].epoch.toDouble()
        );

        // Listas para métricas
        final List<double> lossValues = [];
        final List<double> map50Values = [];
        final List<double> precisionValues = [];
        final List<double> recallValues = [];

        // Extrair valores históricos
        for (final metrics in report.metricsHistory) {
          lossValues.add(metrics.loss);

          if (metrics.map50 != null) map50Values.add(metrics.map50!);
          if (metrics.precision != null) precisionValues.add(metrics.precision!);
          if (metrics.recall != null) recallValues.add(metrics.recall!);
        }

        return SingleChildScrollView(
          padding: AppSpacing.paddingMedium,
          child: Column(
            children: [
              // Gráfico de Loss
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
                      values: lossValues,
                      color: AppColors.error,
                      showAreaGradient: true,
                    ),
                  ],
                  title: 'Loss ao longo do treinamento',
                  yAxisTitle: 'Loss',
                ),
              ),

              // Gráfico de Precisão & Recall
              if (precisionValues.isNotEmpty && recallValues.isNotEmpty)
                Container(
                  margin: AppSpacing.paddingMedium,
                  decoration: BoxDecoration(
                    color: ThemeColors.surface(context),
                    borderRadius: AppBorders.medium,
                    boxShadow: ThemeColors.boxShadow(context, level: ShadowLevel.small),
                  ),
                  child: MetricsLineChart(
                    xValues: epochs.sublist(0, precisionValues.length),
                    series: [
                      MetricSeries(
                        name: 'Precisão',
                        values: precisionValues,
                        color: AppColors.primary,
                      ),
                      MetricSeries(
                        name: 'Recall',
                        values: recallValues,
                        color: AppColors.secondary,
                      ),
                    ],
                    title: 'Precisão e Recall',
                    yAxisTitle: 'Valor',
                  ),
                ),

              // Gráfico de mAP50
              if (map50Values.isNotEmpty)
                Container(
                  margin: AppSpacing.paddingMedium,
                  decoration: BoxDecoration(
                    color: ThemeColors.surface(context),
                    borderRadius: AppBorders.medium,
                    boxShadow: ThemeColors.boxShadow(context, level: ShadowLevel.small),
                  ),
                  child: MetricsLineChart(
                    xValues: epochs.sublist(0, map50Values.length),
                    series: [
                      MetricSeries(
                        name: 'mAP50',
                        values: map50Values,
                        color: AppColors.tertiary,
                        showAreaGradient: true,
                      ),
                    ],
                    title: 'mAP50 ao longo do treinamento',
                    yAxisTitle: 'mAP50',
                  ),
                ),
            ],
          ),
        );
      });
    }

    // Para sessões com erro ou pendentes
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            _getStatusIcon(session.status),
            size: 64,
            color: _getStatusColor(session.status),
          ),
          const SizedBox(height: 16),
          Text(
            'Status: ${session.statusDisplay}',
            style: AppTypography.titleSmall(context),
          ),
          const SizedBox(height: 8),
          Text(
            _getStatusMessage(session.status),
            style: AppTypography.bodyMedium(context),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Constrói a aba de hiperparâmetros
  Widget _buildHyperparametersTab(BuildContext context, TrainingSession session) {
    final hyperparams = session.hyperparameters;

    return SingleChildScrollView(
      padding: AppSpacing.paddingLarge,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Hiperparâmetros do Treinamento',
            style: AppTypography.titleMedium(context),
          ),
          const SizedBox(height: 24),

          // Parâmetros principais
          _buildParamGroup(
            context: context,
            title: 'Parâmetros Básicos',
            params: [
              ParamItem(
                name: 'Épocas',
                value: '${hyperparams['epochs'] ?? 'N/A'}',
                icon: Icons.repeat,
              ),
              ParamItem(
                name: 'Batch Size',
                value: '${hyperparams['batch_size'] ?? 'N/A'}',
                icon: Icons.dashboard,
              ),
              ParamItem(
                name: 'Imagem (px)',
                value: '${hyperparams['imgsz'] ?? 'N/A'} × ${hyperparams['imgsz'] ?? 'N/A'}',
                icon: Icons.crop_free,
              ),
              ParamItem(
                name: 'Dispositivo',
                value: _formatDevice(hyperparams['device']),
                icon: Icons.memory,
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Parâmetros de otimização
          _buildParamGroup(
            context: context,
            title: 'Parâmetros de Otimização',
            params: [
              ParamItem(
                name: 'Otimizador',
                value: '${hyperparams['optimizer'] ?? 'Auto'}',
                icon: Icons.tune,
              ),
              ParamItem(
                name: 'Taxa de Aprendizado',
                value: '${hyperparams['lr0'] ?? 'N/A'}',
                icon: Icons.speed,
              ),
              ParamItem(
                name: 'Paciência',
                value: '${hyperparams['patience'] ?? 'N/A'} épocas',
                icon: Icons.timer_off,
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Parâmetros avançados (se existirem)
          if (_hasAdvancedParams(hyperparams))
            _buildParamGroup(
              context: context,
              title: 'Parâmetros Avançados',
              params: _getAdvancedParams(hyperparams),
            ),
        ],
      ),
    );
  }

  /// Constrói a aba de relatório final
  Widget _buildReportTab(BuildContext context, TrainingSession session) {
    if (session.status != 'completed') {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.analytics_outlined,
              size: 64,
              color: ThemeColors.textSecondary(context),
            ),
            const SizedBox(height: 16),
            Text(
              'Relatório não disponível',
              style: AppTypography.titleSmall(context),
            ),
            const SizedBox(height: 8),
            Padding(
              padding: AppSpacing.paddingHorizontalLarge,
              child: Text(
                'O relatório final estará disponível quando o treinamento for concluído com sucesso.',
                style: AppTypography.bodyMedium(context),
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      );
    }

    return Obx(() {
      final report = _controller.trainingReport.value;

      if (report == null) {
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              Text(
                'Carregando relatório...',
                style: AppTypography.titleSmall(context),
              ),
            ],
          ),
        );
      }

      return SingleChildScrollView(
        padding: AppSpacing.paddingMedium,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Resumo do relatório
            _buildReportSummary(context, report),

            // Matriz de confusão
            if (report.confusionMatrix.isNotEmpty && report.classPerformance.isNotEmpty)
              Container(
                margin: AppSpacing.paddingMedium,
                decoration: BoxDecoration(
                  color: ThemeColors.surface(context),
                  borderRadius: AppBorders.medium,
                  boxShadow: ThemeColors.boxShadow(context, level: ShadowLevel.small),
                ),
                child: ConfusionMatrixWidget(
                  matrix: report.confusionMatrix,
                  classNames: report.classPerformance.map((c) => c.className).toList(),
                  showPercentages: true,
                ),
              ),

            // Desempenho por classe
            if (report.classPerformance.isNotEmpty)
              Container(
                margin: AppSpacing.paddingMedium,
                decoration: BoxDecoration(
                  color: ThemeColors.surface(context),
                  borderRadius: AppBorders.medium,
                  boxShadow: ThemeColors.boxShadow(context, level: ShadowLevel.small),
                ),
                child: ClassPerformanceList(
                  performances: report.classPerformance,
                ),
              ),
          ],
        ),
      );
    });
  }

  /// Constrói uma caixa de informação
  Widget _buildInfoBox({
    required BuildContext context,
    required String label,
    required String value,
    required IconData icon,
  }) {
    return Expanded(
      child: Container(
        padding: AppSpacing.paddingSmall,
        margin: const EdgeInsets.only(right: 8),
        decoration: BoxDecoration(
          color: ThemeColors.surface(context),
          borderRadius: AppBorders.small,
          border: Border.all(
            color: ThemeColors.border(context),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  icon,
                  size: 14,
                  color: ThemeColors.textSecondary(context),
                ),
                const SizedBox(width: 4),
                Text(
                  label,
                  style: AppTypography.bodySmall(context).copyWith(
                    color: ThemeColors.textSecondary(context),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: AppTypography.labelMedium(context),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  /// Constrói um grupo de parâmetros
  Widget _buildParamGroup({
    required BuildContext context,
    required String title,
    required List<ParamItem> params,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: AppTypography.titleSmall(context),
        ),
        const SizedBox(height: 16),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            childAspectRatio: 2.5,
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
          ),
          itemCount: params.length,
          itemBuilder: (context, index) {
            final param = params[index];
            return Container(
              padding: AppSpacing.paddingMedium,
              decoration: BoxDecoration(
                color: ThemeColors.surface(context),
                borderRadius: AppBorders.medium,
                border: Border.all(
                  color: ThemeColors.border(context),
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    param.icon,
                    size: 24,
                    color: AppColors.primary,
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          param.name,
                          style: AppTypography.labelSmall(context),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          param.value,
                          style: AppTypography.titleSmall(context),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ],
    );
  }

  /// Constrói o resumo do relatório
  Widget _buildReportSummary(BuildContext context, TrainingReport report) {
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
          Text(
            'Resumo do Modelo',
            style: AppTypography.titleMedium(context),
          ),
          const SizedBox(height: 16),

          // Métricas principais em cartões
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 4,
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            childAspectRatio: 1.5,
            children: [
              _buildMetricCard(
                context: context,
                label: 'mAP50',
                value: '${(report.map50 * 100).toStringAsFixed(1)}%',
                icon: Icons.precision_manufacturing_outlined,
                color: AppColors.primary,
              ),
              _buildMetricCard(
                context: context,
                label: 'Precisão',
                value: '${(report.precision * 100).toStringAsFixed(1)}%',
                icon: Icons.speed,
                color: AppColors.secondary,
              ),
              _buildMetricCard(
                context: context,
                label: 'Recall',
                value: '${(report.recall * 100).toStringAsFixed(1)}%',
                icon: Icons.replay_outlined,
                color: AppColors.tertiary,
              ),
              _buildMetricCard(
                context: context,
                label: 'F1-Score',
                value: '${(report.f1Score * 100).toStringAsFixed(1)}%',
                icon: Icons.equalizer_outlined,
                color: AppColors.info,
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Informações adicionais
          Row(
            children: [
              _buildInfoBox(
                context: context,
                label: 'Imagens de Treino',
                value: '${report.trainImagesCount}',
                icon: Icons.image_outlined,
              ),
              _buildInfoBox(
                context: context,
                label: 'Imagens de Validação',
                value: '${report.valImagesCount}',
                icon: Icons.image_search_outlined,
              ),
              _buildInfoBox(
                context: context,
                label: 'Tamanho do Modelo',
                value: report.modelSizeFormatted,
                icon: Icons.sd_storage_outlined,
              ),
              _buildInfoBox(
                context: context,
                label: 'Tempo de Treinamento',
                value: report.trainingTimeFormatted,
                icon: Icons.timer_outlined,
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Constrói um cartão de métrica
  Widget _buildMetricCard({
    required BuildContext context,
    required String label,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: AppSpacing.paddingMedium,
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: AppBorders.medium,
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 16, color: color),
              const SizedBox(width: 4),
              Text(
                label,
                style: AppTypography.labelMedium(context).copyWith(
                  color: color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: AppTypography.titleMedium(context).copyWith(
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  /// Verifica se deve mostrar botões de ação
  bool _shouldShowActionButtons(TrainingSession session) {
    return session.canBePaused || session.canBeResumed || session.canBeCancelled;
  }

  /// Obtém a cor para o status
  Color _getStatusColor(String status) {
    switch (status) {
      case 'pending':
        return AppColors.info;
      case 'running':
        return AppColors.primary;
      case 'completed':
        return AppColors.success;
      case 'failed':
        return AppColors.error;
      case 'paused':
        return AppColors.warning;
      case 'cancelled':
        return AppColors.grey;
      default:
        return AppColors.grey;
    }
  }

  /// Obtém o ícone para o status
  IconData _getStatusIcon(String status) {
    switch (status) {
      case 'pending':
        return Icons.hourglass_empty;
      case 'running':
        return Icons.play_circle_outline;
      case 'completed':
        return Icons.check_circle_outline;
      case 'failed':
        return Icons.error_outline;
      case 'paused':
        return Icons.pause_circle_outline;
      case 'cancelled':
        return Icons.cancel_outlined;
      default:
        return Icons.help_outline;
    }
  }

  /// Obtém uma mensagem para o status
  String _getStatusMessage(String status) {
    switch (status) {
      case 'pending':
        return 'O treinamento está aguardando para iniciar.';
      case 'failed':
        return 'O treinamento falhou. Verifique os logs para mais detalhes.';
      case 'cancelled':
        return 'O treinamento foi cancelado pelo usuário.';
      default:
        return '';
    }
  }

  /// Formata o dispositivo
  String _formatDevice(dynamic device) {
    if (device == null) return 'Auto';
    if (device == 'auto') return 'Auto';
    if (device == 'cpu') return 'CPU';
    if (device is String && device.startsWith('cuda')) return 'GPU';
    if (device is int || (device is String && int.tryParse(device) != null)) {
      return 'GPU ${device is int ? device : int.parse(device)}';
    }
    return device.toString();
  }

  /// Verifica se existem parâmetros avançados
  bool _hasAdvancedParams(Map<String, dynamic> hyperparams) {
    final basicParams = ['epochs', 'batch_size', 'imgsz', 'device', 'optimizer', 'lr0', 'patience'];
    return hyperparams.keys.any((key) => !basicParams.contains(key));
  }

  /// Obtém a lista de parâmetros avançados
  List<ParamItem> _getAdvancedParams(Map<String, dynamic> hyperparams) {
    final basicParams = ['epochs', 'batch_size', 'imgsz', 'device', 'optimizer', 'lr0', 'patience'];

    final List<ParamItem> result = [];

    hyperparams.forEach((key, value) {
      if (!basicParams.contains(key)) {
        // Formato mais amigável para booleanos
        if (value is bool) {
          value = value ? 'Sim' : 'Não';
        }

        result.add(ParamItem(
          name: _formatParamName(key),
          value: value.toString(),
          icon: Icons.settings,
        ));
      }
    });

    return result;
  }

  /// Formata o nome do parâmetro
  String _formatParamName(String key) {
    // Substituir underscores por espaços e capitalizar a primeira letra
    final words = key.split('_');
    final formattedWords = words.map((word) {
      if (word.length > 0) {
        return word[0].toUpperCase() + word.substring(1);
      }
      return word;
    });
    return formattedWords.join(' ');
  }

  /// Exibe diálogo de confirmação para cancelar treinamento
  void _showCancelConfirmDialog(BuildContext context, int sessionId) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancelar treinamento'),
        content: const Text(
            'Tem certeza que deseja cancelar este treinamento? Esta ação não pode ser desfeita.'
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              _controller.cancelTraining(sessionId);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              foregroundColor: Colors.white,
            ),
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );
  }
}

/// Modelo para item de parâmetro
class ParamItem {
  final String name;
  final String value;
  final IconData icon;

  const ParamItem({
    required this.name,
    required this.value,
    required this.icon,
  });
}