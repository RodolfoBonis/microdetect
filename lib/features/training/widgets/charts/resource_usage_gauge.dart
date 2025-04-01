import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:fl_chart/fl_chart.dart';

/// Widget para exibir medidores de uso de recursos
class ResourceUsageGauge extends StatelessWidget {
  /// Uso de CPU em percentual (0-100)
  final double cpuUsage;

  /// Uso de memória em percentual (0-100)
  final double memoryUsage;

  /// Uso de GPU em percentual (0-100), opcional
  final double? gpuUsage;

  /// Uso de memória GPU em percentual (0-100), opcional
  final double? gpuMemoryUsage;

  /// Título do widget
  final String title;

  /// Tamanho do medidor
  final double size;

  /// Construtor
  const ResourceUsageGauge({
    Key? key,
    required this.cpuUsage,
    required this.memoryUsage,
    this.gpuUsage,
    this.gpuMemoryUsage,
    this.title = 'Uso de Recursos',
    this.size = 150,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
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
        Wrap(
          spacing: AppSpacing.medium,
          runSpacing: AppSpacing.medium,
          alignment: WrapAlignment.center,
          children: [
            _buildGauge(
              context,
              'CPU',
              cpuUsage,
              AppColors.primary,
              icon: Icons.memory,
            ),
            _buildGauge(
              context,
              'Memória',
              memoryUsage,
              AppColors.secondary,
              icon: Icons.storage,
            ),
            if (gpuUsage != null)
              _buildGauge(
                context,
                'GPU',
                gpuUsage!,
                AppColors.tertiary,
                icon: Icons.widgets,
              ),
            if (gpuMemoryUsage != null)
              _buildGauge(
                context,
                'Mem. GPU',
                gpuMemoryUsage!,
                AppColors.info,
                icon: Icons.sd_storage,
              ),
          ],
        ),
      ],
    );
  }

  /// Constrói um medidor individual
  Widget _buildGauge(
      BuildContext context,
      String label,
      double value,
      Color color,
      {IconData? icon}
      ) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      width: size,
      height: size + 40,
      padding: AppSpacing.paddingSmall,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Rótulo
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (icon != null) ...[
                Icon(icon, size: 16, color: color),
                const SizedBox(width: 4),
              ],
              Text(
                label,
                style: AppTypography.labelMedium(context).copyWith(
                  color: color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          // Gauge chart
          SizedBox(
            height: size,
            width: size,
            child: Stack(
              children: [
                // Gráfico circular
                PieChart(
                  PieChartData(
                    sectionsSpace: 0,
                    centerSpaceRadius: size / 3,
                    startDegreeOffset: 270,
                    sections: [
                      // Seção preenchida
                      PieChartSectionData(
                        value: value,
                        color: _getColorForValue(color, value),
                        radius: size / 4,
                        showTitle: false,
                      ),
                      // Seção vazia
                      PieChartSectionData(
                        value: 100 - value,
                        color: isDark ? AppColors.neutralDark : AppColors.neutralLight,
                        radius: size / 4,
                        showTitle: false,
                      ),
                    ],
                  ),
                ),
                // Valor central
                Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        '${value.toStringAsFixed(1)}%',
                        style: AppTypography.titleSmall(context).copyWith(
                          color: _getColorForValue(color, value),
                        ),
                      ),
                      Text(
                        _getLabelForValue(value),
                        style: AppTypography.bodySmall(context).copyWith(
                          color: ThemeColors.textSecondary(context),
                          fontSize: 10,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Obtém a cor baseada no valor
  Color _getColorForValue(Color baseColor, double value) {
    if (value >= 90) {
      return AppColors.error;
    } else if (value >= 75) {
      return AppColors.warning;
    } else {
      return baseColor;
    }
  }

  /// Obtém o rótulo baseado no valor
  String _getLabelForValue(double value) {
    if (value >= 90) {
      return 'Crítico';
    } else if (value >= 75) {
      return 'Alto';
    } else if (value >= 50) {
      return 'Moderado';
    } else {
      return 'Normal';
    }
  }
}