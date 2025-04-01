import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/features/training/controllers/hyperparameter_search_controller.dart';
import 'package:microdetect/features/training/models/hyperparameter_search.dart';
import 'package:percent_indicator/percent_indicator.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_borders.dart';

/// Widget para exibir e acompanhar o progresso de busca de hiperparâmetros em tempo real
class HyperparameterSearchProgress extends StatelessWidget {
  /// Busca de hiperparâmetros
  final HyperparamSearch search;

  /// Construtor
  const HyperparameterSearchProgress({
    Key? key,
    required this.search,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<HyperparameterSearchController>();

    return Obx(() {
      return RefreshIndicator(
        onRefresh: () async {
          await controller.selectHyperparamSearch(search.id);
        },
        child: SingleChildScrollView(
          padding: AppSpacing.paddingMedium,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Progresso atual
              _buildProgressSection(context, controller),

              // Tabela de tentativas
              _buildTrialsSection(context, controller),

              // Melhores parâmetros até agora
              _buildBestParamsSection(context, controller),
            ],
          ),
        ),
      );
    });
  }

  /// Constrói a seção de progresso atual
  Widget _buildProgressSection(BuildContext context, HyperparameterSearchController controller) {
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
                Icons.search,
                size: 20,
                color: AppColors.primary,
              ),
              const SizedBox(width: 8),
              Text(
                'Progresso da Busca',
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
              percent: controller.currentIteration.value /
                  (controller.totalIterations.value > 0 ? controller.totalIterations.value : 1),
              center: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    '${controller.currentIteration.value}',
                    style: AppTypography.titleLarge(context),
                  ),
                  Text(
                    'de ${controller.totalIterations.value}',
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
              'Tentativa ${controller.currentIteration.value} de ${controller.totalIterations.value}',
              style: AppTypography.titleSmall(context),
            ),
          ),
          const SizedBox(height: 8),

          // Barra de progresso linear
          LinearPercentIndicator(
            lineHeight: 16.0,
            percent: controller.currentIteration.value /
                (controller.totalIterations.value > 0 ? controller.totalIterations.value : 1),
            backgroundColor: ThemeColors.surfaceVariant(context),
            progressColor: AppColors.primary,
            animation: true,
            animationDuration: 500,
            center: Text(
              '${(controller.currentIteration.value / controller.totalIterations.value * 100).toStringAsFixed(0)}%',
              style: AppTypography.bodySmall(context).copyWith(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
            barRadius: Radius.circular(AppBorders.radiusSmall),
          ),
          const SizedBox(height: 16),

          // Status atual
          if (controller.searchStatus.value.isNotEmpty)
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
                    'Status: ${controller.searchStatus.value}',
                    style: AppTypography.bodyMedium(context),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  /// Constrói a seção de tentativas
  Widget _buildTrialsSection(BuildContext context, HyperparameterSearchController controller) {
    if (controller.trialsList.isEmpty) {
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
              'Tentativas Realizadas',
              style: AppTypography.titleSmall(context),
            ),
            const SizedBox(height: 16),
            Center(
              child: Padding(
                padding: const EdgeInsets.all(32.0),
                child: Column(
                  children: [
                    Icon(
                      Icons.hourglass_empty,
                      size: 48,
                      color: ThemeColors.textSecondary(context),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Aguardando tentativas...',
                      style: AppTypography.titleSmall(context),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Os resultados aparecerão aqui conforme as tentativas forem concluídas.',
                      style: AppTypography.bodyMedium(context),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      );
    }

    // Extrair todas as chaves de parâmetros e métricas das tentativas
    final Set<String> paramKeys = {};
    final Set<String> metricKeys = {};

    for (final trial in controller.trialsList) {
      if (trial['params'] != null) {
        paramKeys.addAll((trial['params'] as Map<String, dynamic>).keys);
      }
      if (trial['metrics'] != null) {
        metricKeys.addAll((trial['metrics'] as Map<String, dynamic>).keys);
      }
    }

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
            'Tentativas Realizadas',
            style: AppTypography.titleSmall(context),
          ),
          const SizedBox(height: 16),

          // Tabela de tentativas
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columnSpacing: 20,
              dataRowMinHeight: 48,
              dataRowMaxHeight: 64,
              headingRowColor: MaterialStateProperty.all(
                ThemeColors.surfaceVariant(context),
              ),
              columns: [
                const DataColumn(
                  label: Text('Nº'),
                  tooltip: 'Número da tentativa',
                ),
                // Colunas de parâmetros
                ...paramKeys.map((key) => DataColumn(
                  label: Text(_formatParamName(key)),
                  tooltip: key,
                )),
                // Colunas de métricas
                ...metricKeys.map((key) => DataColumn(
                  label: Text(_formatParamName(key)),
                  tooltip: key,
                )),
              ],
              rows: controller.trialsList.asMap().entries.map((entry) {
                final index = entry.key;
                final trial = entry.value;

                return DataRow(
                  color: index % 2 == 0
                      ? null
                      : MaterialStateProperty.all(ThemeColors.surfaceVariant(context).withOpacity(0.3)),
                  cells: [
                    // Número da tentativa
                    DataCell(Text('${index + 1}')),

                    // Células de parâmetros
                    ...paramKeys.map((key) {
                      final params = trial['params'] as Map<String, dynamic>?;
                      final value = params != null ? params[key]?.toString() ?? '-' : '-';
                      return DataCell(Text(value));
                    }),

                    // Células de métricas
                    ...metricKeys.map((key) {
                      final metrics = trial['metrics'] as Map<String, dynamic>?;
                      final value = metrics != null ? metrics[key] : null;

                      String displayValue = '-';
                      if (value != null) {
                        if ((key.contains('map') ||
                            key == 'precision' ||
                            key == 'recall' ||
                            key.contains('score')) &&
                            value is num) {
                          displayValue = '${(value * 100).toStringAsFixed(1)}%';
                        } else {
                          displayValue = value.toString();
                        }
                      }

                      return DataCell(Text(displayValue));
                    }),
                  ],
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  /// Constrói a seção de melhores parâmetros até agora
  Widget _buildBestParamsSection(BuildContext context, HyperparameterSearchController controller) {
    if (controller.bestParams.value == null || controller.bestMetrics.value == null) {
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
              'Melhores Parâmetros (Até Agora)',
              style: AppTypography.titleSmall(context),
            ),
            const SizedBox(height: 16),
            Center(
              child: Padding(
                padding: const EdgeInsets.all(32.0),
                child: Column(
                  children: [
                    Icon(
                      Icons.insights,
                      size: 48,
                      color: ThemeColors.textSecondary(context),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Aguardando resultados...',
                      style: AppTypography.titleSmall(context),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Os melhores parâmetros serão exibidos aqui após a conclusão de pelo menos uma tentativa.',
                      style: AppTypography.bodyMedium(context),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      );
    }

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
            'Melhores Parâmetros (Até Agora)',
            style: AppTypography.titleSmall(context),
          ),
          const SizedBox(height: 16),

          // Melhores parâmetros em grid
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3,
              childAspectRatio: 2.5,
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
            ),
            itemCount: controller.bestParams.value!.length,
            itemBuilder: (context, index) {
              final entry = controller.bestParams.value!.entries.elementAt(index);
              return _buildParamCard(
                context: context,
                name: _formatParamName(entry.key),
                value: entry.value.toString(),
              );
            },
          ),

          const SizedBox(height: 24),
          const Divider(),
          const SizedBox(height: 16),

          // Melhores métricas
          Text(
            'Métricas com os Melhores Parâmetros',
            style: AppTypography.titleSmall(context),
          ),
          const SizedBox(height: 16),

          // Grid de métricas
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 4,
              childAspectRatio: 2.0,
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
            ),
            itemCount: controller.bestMetrics.value!.length,
            itemBuilder: (context, index) {
              final entry = controller.bestMetrics.value!.entries.elementAt(index);

              // Formatação especial para valores de porcentagem
              String value = entry.value.toString();
              if (entry.key.contains('map') ||
                  entry.key == 'precision' ||
                  entry.key == 'recall' ||
                  entry.key.contains('score')) {
                if (entry.value is num) {
                  value = '${(entry.value * 100).toStringAsFixed(1)}%';
                }
              }

              return _buildMetricCard(
                context: context,
                name: _formatParamName(entry.key),
                value: value,
              );
            },
          ),
        ],
      ),
    );
  }

  /// Constrói um card de parâmetro
  Widget _buildParamCard({
    required BuildContext context,
    required String name,
    required String value,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: AppSpacing.paddingSmall,
      decoration: BoxDecoration(
        color: isDark
            ? AppColors.secondary.withOpacity(0.15)
            : AppColors.secondary.withOpacity(0.1),
        borderRadius: AppBorders.small,
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            name,
            style: AppTypography.labelSmall(context).copyWith(
              color: AppColors.secondary,
            ),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: AppTypography.titleSmall(context).copyWith(
              color: AppColors.secondary,
              fontSize: 16,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  /// Constrói um card de métrica
  Widget _buildMetricCard({
    required BuildContext context,
    required String name,
    required String value,
  }) {
    final colors = [
      AppColors.primary,
      AppColors.tertiary,
      AppColors.info,
      AppColors.success,
    ];

    final index = name.hashCode % colors.length;
    final color = colors[index];
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: AppSpacing.paddingSmall,
      decoration: BoxDecoration(
        color: isDark
            ? color.withOpacity(0.15)
            : color.withOpacity(0.1),
        borderRadius: AppBorders.small,
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            name,
            style: AppTypography.labelSmall(context).copyWith(
              color: color,
            ),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: AppTypography.titleSmall(context).copyWith(
              color: color,
              fontSize: 16,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  /// Formata o nome do parâmetro
  String _formatParamName(String key) {
    // Substituir underscores por espaços e capitalizar a primeira letra
    final words = key.split('_');
    final formattedWords = words.map((word) {
      if (word.isNotEmpty) {
        return word[0].toUpperCase() + word.substring(1);
      }
      return word;
    });
    return formattedWords.join(' ');
  }
}