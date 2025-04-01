import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_badge.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/training/models/hyperparameter_search.dart';
import 'package:percent_indicator/percent_indicator.dart';


/// Widget para exibir um card de busca de hiperparâmetros
class HyperparameterSearchCard extends StatelessWidget {
  /// Dados da busca de hiperparâmetros
  final HyperparamSearch search;

  /// Função chamada ao selecionar a busca
  final VoidCallback? onTap;

  /// Função chamada ao clicar para usar os melhores parâmetros
  final VoidCallback? onUseBestParams;

  /// Função chamada ao visualizar o modelo final
  final VoidCallback? onViewFinalModel;

  /// Construtor
  const HyperparameterSearchCard({
    Key? key,
    required this.search,
    this.onTap,
    this.onUseBestParams,
    this.onViewFinalModel,
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
                          search.name,
                          style: AppTypography.titleMedium(context),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          search.description,
                          style: AppTypography.bodySmall(context).copyWith(
                            color: ThemeColors.textSecondary(context),
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  _buildStatusBadge(context),
                ],
              ),

              const SizedBox(height: 16),

              // Indicador de progresso (se em execução)
              if (search.status == 'running')
                Column(
                  children: [
                    LinearPercentIndicator(
                      lineHeight: 12,
                      percent: search.progress.clamp(0.0, 1.0),
                      backgroundColor: isDark ? AppColors.neutralDark : AppColors.neutralLight,
                      progressColor: AppColors.primary,
                      barRadius: Radius.circular(AppBorders.radiusSmall),
                      padding: EdgeInsets.zero,
                      animation: true,
                      animationDuration: 500,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Tentativa ${search.trialsData?.length ?? 0} de ${search.iterations}',
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
                    label: 'Dataset',
                    value: 'ID: ${search.datasetId}',
                    icon: Icons.folder,
                  ),
                  _buildInfoItem(
                    context: context,
                    label: 'Iterações',
                    value: '${search.iterations}',
                    icon: Icons.repeat,
                  ),
                  _buildInfoItem(
                    context: context,
                    label: 'Criado em',
                    value: search.createdAtFormatted,
                    icon: Icons.calendar_today,
                  ),
                  _buildInfoItem(
                    context: context,
                    label: 'Duração',
                    value: search.durationFormatted,
                    icon: Icons.timer,
                  ),
                ],
              ),

              // Melhores métricas (se concluído)
              if (search.status == 'completed' && search.bestMetrics != null)
                _buildBestMetrics(context),

              // Botões de ação
              if (_shouldShowActionButtons() && search.status == 'completed')
                Padding(
                  padding: const EdgeInsets.only(top: 16.0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      if (search.trainingSessionId != null && onViewFinalModel != null)
                        OutlinedButton.icon(
                          onPressed: onViewFinalModel,
                          icon: const Icon(Icons.visibility),
                          label: const Text('Ver Modelo'),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: AppColors.secondary,
                          ),
                        ),
                      if (search.bestParams != null && onUseBestParams != null) ...[
                        const SizedBox(width: 16),
                        ElevatedButton.icon(
                          onPressed: onUseBestParams,
                          icon: const Icon(Icons.play_arrow),
                          label: const Text('Usar Parâmetros'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: Colors.white,
                          ),
                        ),
                      ],
                    ],
                  ),
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

    switch (search.status) {
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
      default:
        color = AppColors.grey;
        icon = null;
    }

    return AppBadge(
      text: search.statusDisplay,
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

  /// Constrói o widget de métricas
  Widget _buildBestMetrics(BuildContext context) {
    final metrics = search.bestMetrics!;

    // Extrair métricas mais relevantes
    final map50 = metrics['map50'] ?? 0.0;
    final precision = metrics['precision'] ?? 0.0;
    final recall = metrics['recall'] ?? 0.0;

    // Calcular F1-Score se possível
    double f1Score = 0.0;
    if (precision > 0 && recall > 0) {
      f1Score = 2 * precision * recall / (precision + recall);
    } else if (metrics.containsKey('f1_score')) {
      f1Score = metrics['f1_score'];
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        const Divider(),
        const SizedBox(height: 8),
        Text(
          'Melhores Métricas',
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

  /// Verifica se deve mostrar botões de ação
  bool _shouldShowActionButtons() {
    return (search.bestParams != null && onUseBestParams != null) ||
        (search.trainingSessionId != null && onViewFinalModel != null);
  }
}