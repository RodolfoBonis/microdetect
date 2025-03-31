import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/datasets/models/class_distribution.dart';

class ClassDistributionChart extends StatelessWidget {
  /// Dados de distribuição de classes
  final List<ClassDistribution> distribution;
  
  /// Altura do gráfico
  final double height;
  
  /// Mostrar legenda
  final bool showLegend;
  
  /// Mostrar títulos
  final bool showTitles;
  
  /// Número máximo de classes a mostrar (as restantes são agrupadas como "Outras")
  final int maxClassesToShow;
  
  /// Usar gradiente nas barras
  final bool useGradient;

  const ClassDistributionChart({
    Key? key,
    required this.distribution,
    this.height = 200,
    this.showLegend = true,
    this.showTitles = true,
    this.maxClassesToShow = 8,
    this.useGradient = true,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (distribution.isEmpty) {
      return SizedBox(
        height: height,
        child: const Center(
          child: Text('Sem dados de distribuição de classes'),
        ),
      );
    }

    // Ordenar distribuição por quantidade (decrescente)
    final sortedDistribution = List<ClassDistribution>.from(distribution)
      ..sort((a, b) => b.count.compareTo(a.count));
    
    // Limitar o número de classes exibidas
    final List<ClassDistribution> displayedClasses;
    
    if (sortedDistribution.length > maxClassesToShow) {
      // Extrair as classes mais frequentes
      final topClasses = sortedDistribution.take(maxClassesToShow - 1).toList();
      
      // Somar as demais classes como "Outras"
      final otherClasses = sortedDistribution.skip(maxClassesToShow - 1).toList();
      final otherClassesCount = otherClasses.fold<int>(0, (sum, item) => sum + item.count);
      final otherClassesPercentage = otherClasses.fold<double>(0, (sum, item) => sum + item.percentage);
      
      displayedClasses = [
        ...topClasses,
        ClassDistribution(
          className: 'Outras',
          count: otherClassesCount,
          percentage: otherClassesPercentage,
          isUndefined: false,
        ),
      ];
    } else {
      displayedClasses = sortedDistribution;
    }

    return SizedBox(
      height: height,
      child: BarChart(
        BarChartData(
          alignment: BarChartAlignment.spaceAround,
          maxY: 1.0, // Trabalhamos com percentual (0-1)
          barTouchData: BarTouchData(
            enabled: true,
            touchTooltipData: BarTouchTooltipData(
              tooltipPadding: const EdgeInsets.all(8),
              tooltipMargin: 8,
              getTooltipItem: (group, groupIndex, rod, rodIndex) {
                final classData = displayedClasses[groupIndex];
                return BarTooltipItem(
                  '${classData.className}\n',
                  const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                  children: [
                    TextSpan(
                      text: '${classData.count} imagens\n',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.normal,
                      ),
                    ),
                    TextSpan(
                      text: '${(classData.percentage).toStringAsFixed(2)}%',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.normal,
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
          titlesData: FlTitlesData(
            show: showTitles,
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (value, meta) {
                  if (value < 0 || value >= displayedClasses.length) {
                    return const SizedBox.shrink();
                  }
                  
                  final className = displayedClasses[value.toInt()].className;
                  // Truncar o nome da classe se for muito longo
                  final displayName = className.length > 6
                      ? '${className.substring(0, 6)}...'
                      : className;
                  
                  return Padding(
                    padding: const EdgeInsets.only(top: 8.0),
                    child: Text(
                      displayName,
                      style: AppTypography.labelSmall(context),
                      textAlign: TextAlign.center,
                    ),
                  );
                },
              ),
            ),
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 40,
                getTitlesWidget: (value, meta) {
                  // Mostrar percentual em 0%, 25%, 50%, 75%, 100%
                  final percentageStrings = {0.0: '0%', 0.25: '25%', 0.5: '50%', 0.75: '75%', 1.0: '100%'};
                  final label = percentageStrings[value];
                  
                  return label != null
                      ? Text(
                          label,
                          style: AppTypography.labelSmall(context),
                          textAlign: TextAlign.right,
                        )
                      : const SizedBox.shrink();
                },
              ),
            ),
            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          ),
          borderData: FlBorderData(show: false),
          gridData: FlGridData(
            show: true,
            drawHorizontalLine: true,
            drawVerticalLine: false,
            horizontalInterval: 0.25, // Linhas em 0%, 25%, 50%, 75%, 100%
            getDrawingHorizontalLine: (value) => const FlLine(
              color: AppColors.lightGrey,
              strokeWidth: 1,
              dashArray: [5, 5],
            ),
          ),
          barGroups: List.generate(
            displayedClasses.length,
            (index) => _generateBarGroup(
              index,
              displayedClasses[index],
              context,
            ),
          ),
        ),
      ),
    );
  }

  BarChartGroupData _generateBarGroup(
    int x,
    ClassDistribution classData,
    BuildContext context,
  ) {
    // Normalizar o percentual para estar entre 0 e 1
    // Se percentage já estiver entre 0-1, mantém; caso contrário, divide por 100
    final normalizedPercentage = classData.percentage <= 1.0 
        ? classData.percentage 
        : classData.percentage / 100;

    return BarChartGroupData(
      x: x,
      barRods: [
        BarChartRodData(
          toY: normalizedPercentage,
          width: 20,
          color: _getBarColor(classData, x),
          gradient: useGradient
              ? _getBarGradient(classData, x)
              : null,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(6),
            topRight: Radius.circular(6),
          ),
        ),
      ],
    );
  }

  Color _getBarColor(ClassDistribution classData, int index) {
    if (classData.isUndefined) {
      return AppColors.warning;
    }
    
    // Lista de cores para as classes
    final List<Color> classColors = [
      AppColors.primary,
      AppColors.secondary,
      AppColors.info,
      AppColors.tertiary,
      Colors.purple,
      Colors.orange,
      Colors.teal,
      Colors.indigo,
      Colors.lime,
      Colors.brown,
    ];
    
    return classColors[index % classColors.length];
  }

  LinearGradient? _getBarGradient(ClassDistribution classData, int index) {
    final baseColor = _getBarColor(classData, index);
    
    return LinearGradient(
      colors: [
        baseColor,
        baseColor.withOpacity(0.6),
      ],
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
    );
  }
} 