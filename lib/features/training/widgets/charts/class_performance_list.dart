import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:microdetect/features/training/models/training_report.dart';

/// Widget para exibir desempenho por classe
class ClassPerformanceList extends StatelessWidget {
  /// Lista de dados de desempenho por classe
  final List<ClassPerformance> performances;

  /// Título do widget
  final String title;

  /// Construtor
  const ClassPerformanceList({
    Key? key,
    required this.performances,
    this.title = 'Desempenho por Classe',
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (performances.isEmpty) {
      return Container(
        padding: AppSpacing.paddingMedium,
        decoration: BoxDecoration(
          color: ThemeColors.surfaceVariant(context),
          borderRadius: AppBorders.medium,
        ),
        child: Center(
          child: Text(
            'Sem dados de desempenho por classe',
            style: AppTypography.bodyMedium(context),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: AppSpacing.paddingMedium,
          child: Text(
            title,
            style: AppTypography.titleMedium(context),
          ),
        ),
        const SizedBox(height: 8),
        ...performances.map((perf) => _buildClassCard(context, perf)),
      ],
    );
  }

  /// Constrói o card para uma classe
  Widget _buildClassCard(BuildContext context, ClassPerformance perf) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Card(
      margin: AppSpacing.paddingSmall,
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: AppBorders.medium,
      ),
      child: Padding(
        padding: AppSpacing.paddingMedium,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Cabeçalho com nome da classe
            Row(
              children: [
                Expanded(
                  child: Text(
                    perf.className,
                    style: AppTypography.titleSmall(context),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Text(
                  'ID: ${perf.classId}',
                  style: AppTypography.bodySmall(context).copyWith(
                    color: ThemeColors.textSecondary(context),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Métricas principais em cards
            Row(
              children: [
                Expanded(
                  child: _buildMetricCard(
                    context,
                    'Precisão',
                    perf.precision,
                    AppColors.primary,
                    icon: Icons.precision_manufacturing_outlined,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildMetricCard(
                    context,
                    'Recall',
                    perf.recall,
                    AppColors.secondary,
                    icon: Icons.replay_outlined,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildMetricCard(
                    context,
                    'F1-Score',
                    perf.f1Score,
                    AppColors.tertiary,
                    icon: Icons.equalizer_outlined,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Informações de suporte
            Row(
              children: [
                Expanded(
                  child: _buildInfoItem(
                    context,
                    'Exemplos',
                    '${perf.examplesCount}',
                    Icons.image_outlined,
                  ),
                ),
                Expanded(
                  child: _buildInfoItem(
                    context,
                    'Suporte',
                    '${perf.support}',
                    Icons.check_circle_outline,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Gráfico de barras com as métricas
            SizedBox(
              height: 120,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 8.0),
                child: BarChart(
                  BarChartData(
                    barGroups: [
                      _buildBarGroup(0, perf.precision, AppColors.primary),
                      _buildBarGroup(1, perf.recall, AppColors.secondary),
                      _buildBarGroup(2, perf.f1Score, AppColors.tertiary),
                    ],
                    gridData: FlGridData(show: false),
                    titlesData: FlTitlesData(
                      show: true,
                      rightTitles: AxisTitles(
                        sideTitles: SideTitles(showTitles: false),
                      ),
                      topTitles: AxisTitles(
                        sideTitles: SideTitles(showTitles: false),
                      ),
                      bottomTitles: AxisTitles(
                        sideTitles: SideTitles(
                          showTitles: true,
                          getTitlesWidget: (double value, TitleMeta meta) {
                            final titles = ['Precisão', 'Recall', 'F1-Score'];
                            return Padding(
                              padding: const EdgeInsets.only(top: 8.0),
                              child: Text(
                                titles[value.toInt()],
                                style: AppTypography.bodySmall(context).copyWith(
                                  fontSize: 10,
                                ),
                              ),
                            );
                          },
                          reservedSize: 28,
                        ),
                      ),
                      leftTitles: AxisTitles(
                        sideTitles: SideTitles(
                          showTitles: true,
                          getTitlesWidget: (double value, TitleMeta meta) {
                            return Text(
                              '${(value * 100).toInt()}%',
                              style: AppTypography.bodySmall(context).copyWith(
                                fontSize: 10,
                              ),
                            );
                          },
                          reservedSize: 40,
                        ),
                      ),
                    ),
                    borderData: FlBorderData(show: false),
                    barTouchData: BarTouchData(
                      touchTooltipData: BarTouchTooltipData(
                        tooltipRoundedRadius: 8,
                        getTooltipItem: (group, groupIndex, rod, rodIndex) {
                          final titles = ['Precisão', 'Recall', 'F1-Score'];
                          return BarTooltipItem(
                            '${titles[group.x.toInt()]}: ${(rod.toY * 100).toStringAsFixed(2)}%',
                            AppTypography.bodySmall(context),
                          );
                        },
                      ),
                    ),
                    minY: 0,
                    maxY: 1,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Constrói um card de métrica
  Widget _buildMetricCard(
      BuildContext context,
      String title,
      double value,
      Color color,
      {IconData? icon}
      ) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bgColor = isDark
        ? color.withOpacity(0.15)
        : color.withOpacity(0.1);

    return Container(
      padding: AppSpacing.paddingSmall,
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: AppBorders.small,
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (icon != null) ...[
                Icon(icon, size: 16, color: color),
                const SizedBox(width: 4),
              ],
              Text(
                title,
                style: AppTypography.labelSmall(context).copyWith(
                  color: color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '${(value * 100).toStringAsFixed(1)}%',
            style: AppTypography.titleSmall(context).copyWith(
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  /// Constrói um item de informação
  Widget _buildInfoItem(
      BuildContext context,
      String title,
      String value,
      IconData icon
      ) {
    return Row(
      children: [
        Icon(
          icon,
          size: 16,
          color: ThemeColors.icon(context),
        ),
        const SizedBox(width: 8),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: AppTypography.bodySmall(context).copyWith(
                color: ThemeColors.textSecondary(context),
              ),
            ),
            Text(
              value,
              style: AppTypography.labelMedium(context),
            ),
          ],
        ),
      ],
    );
  }

  /// Constrói um grupo de barras para o gráfico
  BarChartGroupData _buildBarGroup(int x, double y, Color color) {
    return BarChartGroupData(
      x: x,
      barRods: [
        BarChartRodData(
          toY: y,
          color: color,
          width: 15,
          borderRadius: BorderRadius.circular(4),
          backDrawRodData: BackgroundBarChartRodData(
            show: true,
            toY: 1,
            color: color.withOpacity(0.1),
          ),
        ),
      ],
    );
  }
}