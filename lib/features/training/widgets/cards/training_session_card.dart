import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import 'package:microdetect/design_system/app_badge.dart';
import 'package:microdetect/features/training/models/training_session.dart';
import 'package:percent_indicator/percent_indicator.dart';


/// Widget para exibir um card de sessão de treinamento
class TrainingSessionCard extends StatelessWidget {
  /// Dados da sessão de treinamento
  final TrainingSession session;

  /// Função chamada ao selecionar a sessão
  final VoidCallback? onTap;

  /// Função chamada ao pausar o treinamento
  final VoidCallback? onPause;

  /// Função chamada ao retomar o treinamento
  final VoidCallback? onResume;

  /// Função chamada ao cancelar o treinamento
  final VoidCallback? onCancel;

  /// Construtor
  const TrainingSessionCard({
    Key? key,
    required this.session,
    this.onTap,
    this.onPause,
    this.onResume,
    this.onCancel,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: AppBorders.medium,
      ),
      margin: AppSpacing.paddingMedium,
      child: InkWell(
        onTap: onTap,
        borderRadius: AppBorders.medium,
        child: Padding(
          padding: AppSpacing.paddingMedium,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Cabeçalho com nome e badge de status
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
                          session.fullModelName,
                          style: AppTypography.bodyMedium(context).copyWith(
                            color: ThemeColors.textSecondary(context),
                          ),
                        ),
                      ],
                    ),
                  ),
                  _buildStatusBadge(context),
                ],
              ),

              const SizedBox(height: 16),

              // Indicador de progresso (se em execução)
              if (session.status == 'running' || session.status == 'paused')
                Column(
                  children: [
                    LinearPercentIndicator(
                      lineHeight: 12,
                      percent: session.progress,
                      backgroundColor: isDark ? AppColors.neutralDark : AppColors.neutralLight,
                      progressColor: _getProgressColor(context, session.status),
                      barRadius: Radius.circular(AppBorders.radiusSmall),
                      padding: EdgeInsets.zero,
                      animation: true,
                      animationDuration: 500,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _getProgressText(),
                      style: AppTypography.bodySmall(context).copyWith(
                        color: ThemeColors.textSecondary(context),
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                  ],
                ),

              // Informações adicionais
              Row(
                children: [
                  _buildInfoItem(
                    context: context,
                    label: 'Criado em',
                    value: session.createdAtFormatted,
                    icon: Icons.calendar_today,
                  ),
                  const SizedBox(width: 16),
                  _buildInfoItem(
                    context: context,
                    label: 'Duração',
                    value: session.durationFormatted,
                    icon: Icons.timer,
                  ),
                ],
              ),

              // Métricas finais (se concluído)
              if (session.status == 'completed' && session.metrics != null)
                _buildMetrics(context),

              const SizedBox(height: 16),

              // Botões de ação
              if (_shouldShowActionButtons())
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    if (session.canBePaused && onPause != null)
                      AppIconButton(
                        icon: Icons.pause,
                        type: AppButtonType.secondary,
                        size: AppButtonSize.small,
                        onPressed: onPause,
                        tooltip: 'Pausar treinamento',
                      ),
                    if (session.canBeResumed && onResume != null) ...[
                      const SizedBox(width: 8),
                      AppIconButton(
                        icon: Icons.play_arrow,
                        type: AppButtonType.primary,
                        size: AppButtonSize.small,
                        onPressed: onResume,
                        tooltip: 'Retomar treinamento',
                      ),
                    ],
                    if (session.canBeCancelled && onCancel != null) ...[
                      const SizedBox(width: 8),
                      AppIconButton(
                        icon: Icons.stop,
                        type: AppButtonType.secondary,
                        size: AppButtonSize.small,
                        onPressed: onCancel,
                        tooltip: 'Cancelar treinamento',
                      ),
                    ],
                  ],
                ),
            ],
          ),
        ),
      ),
    );
  }

  /// Constrói o badge de status
  Widget _buildStatusBadge(BuildContext context) {
    Color color;
    IconData? icon;

    switch (session.status) {
      case 'pending':
        color = AppColors.info;
        icon = Icons.hourglass_empty;
        break;
      case 'running':
        color = AppColors.primary;
        icon = Icons.play_circle_outline;
        break;
      case 'completed':
        color = AppColors.success;
        icon = Icons.check_circle_outline;
        break;
      case 'failed':
        color = AppColors.error;
        icon = Icons.error_outline;
        break;
      case 'paused':
        color = AppColors.warning;
        icon = Icons.pause_circle_outline;
        break;
      case 'cancelled':
        color = AppColors.grey;
        icon = Icons.cancel_outlined;
        break;
      default:
        color = AppColors.grey;
        icon = null;
    }

    return AppBadge(
      text: session.statusDisplay,
      color: color,
      prefixIcon: icon,
    );
  }

  /// Constrói um item de informação
  Widget _buildInfoItem({
    required BuildContext context,
    required String label,
    required String value,
    required IconData icon,
  }) {
    return Expanded(
      child: Row(
        children: [
          Icon(
            icon,
            size: 16,
            color: ThemeColors.icon(context),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: AppTypography.bodySmall(context).copyWith(
                    color: ThemeColors.textSecondary(context),
                  ),
                ),
                Text(
                  value,
                  style: AppTypography.bodyMedium(context),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Constrói o widget de métricas finais
  Widget _buildMetrics(BuildContext context) {
    final metrics = session.metrics;
    if (metrics == null) return const SizedBox.shrink();

    final hasFinalMetrics = metrics.containsKey('final_metrics') ||
        metrics.containsKey('map50') ||
        metrics.containsKey('precision') ||
        metrics.containsKey('recall');

    if (!hasFinalMetrics) return const SizedBox.shrink();

    // Obter métricas finais, seja do campo final_metrics ou diretamente
    final finalMetrics = metrics.containsKey('final_metrics')
        ? metrics['final_metrics'] as Map<String, dynamic>
        : metrics;

    final map50 = finalMetrics['map50'] ?? 0.0;
    final precision = finalMetrics['precision'] ?? 0.0;
    final recall = finalMetrics['recall'] ?? 0.0;

    // Calcular F1-Score se possível
    double f1Score = 0.0;
    if (precision > 0 && recall > 0) {
      f1Score = 2 * precision * recall / (precision + recall);
    } else if (finalMetrics.containsKey('f1_score')) {
      f1Score = finalMetrics['f1_score'];
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        const Divider(),
        const SizedBox(height: 8),
        Text(
          'Métricas Finais',
          style: AppTypography.labelMedium(context),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            _buildMetricItem(
              context: context,
              label: 'mAP50',
              value: map50,
              color: AppColors.primary,
            ),
            _buildMetricItem(
              context: context,
              label: 'Precisão',
              value: precision,
              color: AppColors.secondary,
            ),
            _buildMetricItem(
              context: context,
              label: 'Recall',
              value: recall,
              color: AppColors.tertiary,
            ),
            _buildMetricItem(
              context: context,
              label: 'F1-Score',
              value: f1Score,
              color: AppColors.info,
            ),
          ],
        ),
      ],
    );
  }

  /// Constrói um item de métrica
  Widget _buildMetricItem({
    required BuildContext context,
    required String label,
    required double value,
    required Color color,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Expanded(
      child: Column(
        children: [
          Text(
            label,
            style: AppTypography.bodySmall(context).copyWith(
              color: ThemeColors.textSecondary(context),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '${(value * 100).toStringAsFixed(1)}%',
            style: AppTypography.labelMedium(context).copyWith(
              color: isDark ? color : color.withValues(
                red: color.r * 0.8,
                green: color.g * 0.8,
                blue: color.b * 0.8,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Determina a cor do indicador de progresso
  Color _getProgressColor(BuildContext context, String status) {
    if (status == 'paused') {
      return AppColors.warning;
    }
    return AppColors.primary;
  }

  /// Obtém o texto de progresso
  String _getProgressText() {
    if (session.metrics == null) {
      return 'Progresso: ${(session.progress * 100).toStringAsFixed(1)}%';
    }

    final currentEpoch = session.metrics!['current_epoch'] ?? 0;
    final totalEpochs = session.metrics!['total_epochs'] ?? 0;

    if (session.status == 'paused') {
      return 'Pausado em época $currentEpoch de $totalEpochs';
    }

    return 'Época $currentEpoch de $totalEpochs';
  }

  /// Verifica se deve mostrar botões de ação
  bool _shouldShowActionButtons() {
    return (session.canBePaused && onPause != null) ||
        (session.canBeResumed && onResume != null) ||
        (session.canBeCancelled && onCancel != null);
  }
}