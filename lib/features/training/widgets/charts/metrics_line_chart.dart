import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';

/// Widget para exibir gráficos de métricas de treinamento
class MetricsLineChart extends StatelessWidget {
  /// Dados do eixo X (normalmente épocas)
  final List<double> xValues;

  /// Lista de séries de dados para o gráfico
  final List<MetricSeries> series;

  /// Título do gráfico
  final String title;

  /// Título do eixo X
  final String xAxisTitle;

  /// Título do eixo Y
  final String yAxisTitle;

  /// Altura do gráfico
  final double height;

  /// Construtor
  const MetricsLineChart({
    Key? key,
    required this.xValues,
    required this.series,
    required this.title,
    this.xAxisTitle = 'Época',
    this.yAxisTitle = 'Valor',
    this.height = 300,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Verificar tema claro ou escuro
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // Calcular intervalo do eixo Y (min e max)
    double minY = double.infinity;
    double maxY = -double.infinity;

    for (final serie in series) {
      for (final value in serie.values) {
        if (value < minY) minY = value;
        if (value > maxY) maxY = value;
      }
    }

    // Ajustar para ter um intervalo adequado
    if (minY == maxY) {
      minY = minY * 0.9;
      maxY = maxY * 1.1;
    } else {
      final interval = (maxY - minY) * 0.1;
      minY = minY - interval;
      maxY = maxY + interval;
    }

    // Evitar valores negativos para certas métricas
    if (title.contains('mAP') || title.contains('Precisão') || title.contains('Recall')) {
      minY = minY < 0 ? 0 : minY;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 16.0, top: 16.0, right: 16.0),
          child: Text(
            title,
            style: AppTypography.titleMedium(context),
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: height,
          child: Padding(
            padding: const EdgeInsets.only(right: 24.0, bottom: 24.0),
            child: LineChart(
              LineChartData(
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: true,
                  drawHorizontalLine: true,
                  horizontalInterval: (maxY - minY) / 5,
                  getDrawingHorizontalLine: (value) => FlLine(
                    color: isDark ? AppColors.neutralDark : AppColors.neutralLight,
                    strokeWidth: 1,
                  ),
                  getDrawingVerticalLine: (value) => FlLine(
                    color: isDark ? AppColors.neutralDark : AppColors.neutralLight,
                    strokeWidth: 1,
                  ),
                ),
                titlesData: FlTitlesData(
                  rightTitles: AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  topTitles: AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  bottomTitles: AxisTitles(
                    axisNameWidget: Text(
                      xAxisTitle,
                      style: AppTypography.bodySmall(context),
                    ),
                    axisNameSize: 24,
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, meta) {
                        // Mostrar apenas alguns valores para evitar sobreposição
                        if (xValues.length > 10) {
                          final int epoch = value.toInt();
                          if (epoch % (xValues.length ~/ 5) != 0 &&
                              epoch != 0 &&
                              epoch != xValues.length - 1) {
                            return const SizedBox.shrink();
                          }
                        }

                        return Text(
                          value.toInt().toString(),
                          style: AppTypography.bodySmall(context).copyWith(
                            fontSize: 10,
                          ),
                        );
                      },
                      reservedSize: 30,
                    ),
                  ),
                  leftTitles: AxisTitles(
                    axisNameWidget: Text(
                      yAxisTitle,
                      style: AppTypography.bodySmall(context),
                    ),
                    axisNameSize: 24,
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, meta) {
                        String text;

                        // Formatar com base no tipo de métrica
                        if (title.contains('mAP') || title.contains('Precisão') || title.contains('Recall')) {
                          // Exibir como porcentagem
                          text = '${(value * 100).toStringAsFixed(1)}%';
                        } else {
                          // Exibir como número decimal
                          text = value.toStringAsFixed(2);
                        }

                        return Text(
                          text,
                          style: AppTypography.bodySmall(context).copyWith(
                            fontSize: 10,
                          ),
                        );
                      },
                      reservedSize: 40,
                    ),
                  ),
                ),
                borderData: FlBorderData(
                  show: true,
                  border: Border(
                    bottom: BorderSide(
                      color: isDark ? AppColors.neutralDark : AppColors.neutralMedium,
                      width: 1,
                    ),
                    left: BorderSide(
                      color: isDark ? AppColors.neutralDark : AppColors.neutralMedium,
                      width: 1,
                    ),
                  ),
                ),
                minX: 0,
                maxX: xValues.isNotEmpty ? xValues.length - 1.0 : 0,
                minY: minY,
                maxY: maxY,
                lineTouchData: LineTouchData(
                  touchTooltipData: LineTouchTooltipData(
                    tooltipRoundedRadius: 8,
                    getTooltipItems: (List<LineBarSpot> touchedSpots) {
                      return touchedSpots.map((spot) {
                        final seriesIndex = spot.barIndex;
                        final serie = series[seriesIndex];

                        String valueString;
                        if (title.contains('mAP') || title.contains('Precisão') || title.contains('Recall')) {
                          valueString = '${(spot.y * 100).toStringAsFixed(2)}%';
                        } else {
                          valueString = spot.y.toStringAsFixed(4);
                        }

                        return LineTooltipItem(
                          '${serie.name}: $valueString\n$xAxisTitle: ${spot.x.toInt()}',
                          AppTypography.labelSmall(context).copyWith(
                            color: serie.color,
                            fontWeight: FontWeight.bold,
                          ),
                        );
                      }).toList();
                    },
                  ),
                  handleBuiltInTouches: true,
                ),
                lineBarsData: _buildLineBarsData(),
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        _buildLegend(context),
      ],
    );
  }

  /// Constrói as linhas do gráfico
  List<LineChartBarData> _buildLineBarsData() {
    return series.map((serie) {
      return LineChartBarData(
        spots: serie.values.asMap().entries.map((entry) {
          return FlSpot(entry.key.toDouble(), entry.value);
        }).toList(),
        isCurved: true,
        color: serie.color,
        barWidth: 3,
        isStrokeCapRound: true,
        dotData: FlDotData(
          show: serie.values.length < 30, // Mostrar pontos apenas para poucos dados
          getDotPainter: (p0, p1, p2, p3) => FlDotCirclePainter(
            radius: 3,
            color: serie.color,
            strokeWidth: 1,
            strokeColor: Colors.white,
          ),
        ),
        belowBarData: serie.showAreaGradient ? BarAreaData(
          show: true,
          color: serie.color.withOpacity(0.2),
          gradient: LinearGradient(
            colors: [
              serie.color.withOpacity(0.2),
              serie.color.withOpacity(0.0),
            ],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ) : null,
      );
    }).toList();
  }

  /// Constrói a legenda para o gráfico
  Widget _buildLegend(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0),
      child: Wrap(
        spacing: 16,
        runSpacing: 8,
        children: series.map((serie) {
          return Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: serie.color,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 4),
              Text(
                serie.name,
                style: AppTypography.bodySmall(context),
              ),
            ],
          );
        }).toList(),
      ),
    );
  }
}

/// Modelo para uma série de dados no gráfico
class MetricSeries {
  /// Nome da série
  final String name;

  /// Valores para plotar
  final List<double> values;

  /// Cor da linha
  final Color color;

  /// Se deve mostrar gradiente de área abaixo da linha
  final bool showAreaGradient;

  /// Construtor
  const MetricSeries({
    required this.name,
    required this.values,
    required this.color,
    this.showAreaGradient = false,
  });
}