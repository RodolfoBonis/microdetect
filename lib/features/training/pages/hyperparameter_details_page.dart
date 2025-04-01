import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/widgets/base_page_scaffold.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/design_system/app_badge.dart';
import 'package:percent_indicator/percent_indicator.dart';

import '../controllers/hyperparameter_search_controller.dart';
import '../models/hyperparameter_search.dart';
import '../widgets/progress/hyperparameter_search_progress.dart';

/// Página de detalhes da busca de hiperparâmetros
class HyperparameterDetailsPage extends StatefulWidget {
  /// Construtor
  const HyperparameterDetailsPage({Key? key}) : super(key: key);

  @override
  State<HyperparameterDetailsPage> createState() => _HyperparameterDetailsPageState();
}

class _HyperparameterDetailsPageState extends State<HyperparameterDetailsPage> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final HyperparameterSearchController _controller = Get.find<HyperparameterSearchController>();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      try {
        // Get ID from parameters with null checks
        final String? idParam = Get.parameters['id'];
        final int? searchId = idParam != null ? int.tryParse(idParam) : null;

        if (searchId != null && searchId > 0) {
          // Load search details if ID is valid
          if (_controller.selectedSearch.value?.id != searchId) {
            _controller.selectHyperparamSearch(searchId);
          }
        } else {
          // Handle invalid ID gracefully
          Get.snackbar(
            'Erro',
            'ID de busca inválido',
            snackPosition: SnackPosition.BOTTOM,
          );
          Future.delayed(const Duration(seconds: 1), () {
            Get.back();
          });
        }
      } catch (e) {
        debugPrint('Error getting search ID: $e');
        Get.back();
      }
    });
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
          title: 'Detalhes da Busca',
          body: Center(
            child: CircularProgressIndicator(),
          ),
        );
      }

      final search = _controller.selectedSearch.value;
      if (search == null) {
        return BasePageScaffold(
          title: 'Detalhes da Busca',
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
                  'Busca não encontrada',
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
        title: search.name,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Atualizar',
            onPressed: () {
              if (search.id > 0) {
                _controller.selectHyperparamSearch(search.id);
              }
            },
          ),
        ],
        body: Column(
          children: [
            _buildHeader(context, search),
            Expanded(
              child: _buildTabView(context, search),
            ),
          ],
        ),
      );
    });
  }

  /// Constrói o cabeçalho da página
  Widget _buildHeader(BuildContext context, HyperparamSearch search) {
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
              _buildStatusBadge(context, search),
            ],
          ),
          const SizedBox(height: 16),

          // Informações adicionais
          Row(
            children: [
              _buildInfoBox(
                context: context,
                label: 'Dataset',
                value: 'ID: ${search.datasetId}',
                icon: Icons.folder,
              ),
              _buildInfoBox(
                context: context,
                label: 'Iterações',
                value: '${search.trialsData?.length ?? 0} / ${search.iterations}',
                icon: Icons.repeat,
              ),
              _buildInfoBox(
                context: context,
                label: 'Criado em',
                value: search.createdAtFormatted,
                icon: Icons.calendar_today,
              ),
              _buildInfoBox(
                context: context,
                label: 'Duração',
                value: search.durationFormatted,
                icon: Icons.timer,
              ),
            ],
          ),

          // Indicador de progresso (se em execução)
          if (search.status == 'running')
            Padding(
              padding: const EdgeInsets.only(top: 16.0),
              child: LinearPercentIndicator(
                lineHeight: 14,
                percent: search.progress.clamp(0.0, 1.0),
                backgroundColor: ThemeColors.surfaceVariant(context),
                progressColor: AppColors.primary,
                barRadius: Radius.circular(AppBorders.radiusSmall),
                padding: EdgeInsets.zero,
                animation: true,
                center: Text(
                  '${(search.progress * 100).toStringAsFixed(0)}%',
                  style: AppTypography.bodySmall(context).copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),

          // Botões de ação (se aplicável)
          if (_shouldShowActionButtons(search))
            Padding(
              padding: const EdgeInsets.only(top: 16.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  if (search.trainingSessionId != null)
                    AppButton(
                      label: 'Ver Modelo Final',
                      onPressed: () => _controller.viewFinalModel(),
                      type: AppButtonType.secondary,
                      prefixIcon: Icons.visibility,
                    ),
                  if (search.bestParams != null) ...[
                    const SizedBox(width: 16),
                    AppButton(
                      label: 'Treinar com Estes Parâmetros',
                      onPressed: () => _controller.startTrainingWithBestParams(),
                      prefixIcon: Icons.play_arrow,
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
  Widget _buildTabView(BuildContext context, HyperparamSearch search) {
    return Column(
      children: [
        // Barra de abas
        TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Progresso & Resultados'),
            Tab(text: 'Espaço de Busca'),
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
              // Aba 1: Progresso e Resultados
              _buildProgressTab(context, search),

              // Aba 2: Espaço de Busca
              _buildSearchSpaceTab(context, search),
            ],
          ),
        ),
      ],
    );
  }

  /// Constrói a aba de progresso e resultados
  Widget _buildProgressTab(BuildContext context, HyperparamSearch search) {
    if (search.status == 'running') {
      return HyperparameterSearchProgress(
        search: search,
      );
    }

    // Para buscas concluídas
    if (search.status == 'completed' && search.bestParams != null) {
      return SingleChildScrollView(
        padding: AppSpacing.paddingMedium,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Resultados da busca
            _buildSearchResults(context, search),

            // Tabela de tentativas
            const SizedBox(height: 24),
            _buildTrialsTable(context, search),
          ],
        ),
      );
    }

    // Para buscas com erro ou pendentes
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            _getStatusIcon(search.status),
            size: 64,
            color: _getStatusColor(search.status),
          ),
          const SizedBox(height: 16),
          Text(
            'Status: ${search.statusDisplay}',
            style: AppTypography.titleSmall(context),
          ),
          const SizedBox(height: 8),
          Text(
            _getStatusMessage(search.status),
            style: AppTypography.bodyMedium(context),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Constrói a aba de espaço de busca
  Widget _buildSearchSpaceTab(BuildContext context, HyperparamSearch search) {
    final searchSpace = search.searchSpace;

    return SingleChildScrollView(
      padding: AppSpacing.paddingLarge,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Espaço de Busca de Hiperparâmetros',
            style: AppTypography.titleMedium(context),
          ),
          const SizedBox(height: 16),
          Text(
            'Este é o espaço de parâmetros que está sendo explorado durante a otimização.',
            style: AppTypography.bodyMedium(context),
          ),
          const SizedBox(height: 24),

          // Listar parâmetros do espaço de busca
          ...searchSpace.entries.map((entry) {
            return _buildSearchSpaceItem(context, entry.key, entry.value);
          }).toList(),
        ],
      ),
    );
  }

  /// Constrói a seção de resultados da busca
  Widget _buildSearchResults(BuildContext context, HyperparamSearch search) {
    final bestParams = search.bestParams!;
    final bestMetrics = search.bestMetrics!;

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
            'Melhores Parâmetros Encontrados',
            style: AppTypography.titleMedium(context),
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
            itemCount: bestParams.length,
            itemBuilder: (context, index) {
              final entry = bestParams.entries.elementAt(index);
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
            itemCount: bestMetrics.length,
            itemBuilder: (context, index) {
              final entry = bestMetrics.entries.elementAt(index);

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
                isMetric: true,
              );
            },
          ),
        ],
      ),
    );
  }

  /// Constrói a tabela de tentativas
  Widget _buildTrialsTable(BuildContext context, HyperparamSearch search) {
    if (search.trialsData == null || search.trialsData!.isEmpty) {
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
            child: Text(
              'Nenhuma tentativa registrada',
              style: AppTypography.titleSmall(context),
            ),
          ),
        ),
      );
    }

    // Extrair todas as chaves de parâmetros e métricas das tentativas
    final Set<String> paramKeys = {};
    final Set<String> metricKeys = {};

    for (final trial in search.trialsData!) {
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
            'Histórico de Tentativas',
            style: AppTypography.titleMedium(context),
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
              rows: search.trialsData!.asMap().entries.map((entry) {
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

  /// Constrói um item de parâmetro do espaço de busca
  Widget _buildSearchSpaceItem(BuildContext context, String key, dynamic value) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: AppSpacing.paddingMedium,
      decoration: BoxDecoration(
        color: ThemeColors.surface(context),
        borderRadius: AppBorders.medium,
        border: Border.all(
          color: ThemeColors.border(context),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Nome do parâmetro
          Text(
            _formatParamName(key),
            style: AppTypography.titleSmall(context),
          ),
          const SizedBox(height: 8),
          const Divider(),
          const SizedBox(height: 8),

          // Valor do parâmetro
          if (value is List) ...[
            Text(
              'Valores Possíveis:',
              style: AppTypography.labelMedium(context),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: value.map((item) {
                return Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: isDark
                        ? AppColors.primary.withOpacity(0.2)
                        : AppColors.primary.withOpacity(0.1),
                    borderRadius: AppBorders.small,
                  ),
                  child: Text(
                    item.toString(),
                    style: AppTypography.bodySmall(context).copyWith(
                      color: AppColors.primary,
                    ),
                  ),
                );
              }).toList(),
            ),
          ] else if (value is Map) ...[
            // Range de valores
            if (value.containsKey('min') && value.containsKey('max')) ...[
              Text(
                'Intervalo:',
                style: AppTypography.labelMedium(context),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Text(
                    'Mínimo: ${value['min']}',
                    style: AppTypography.bodyMedium(context),
                  ),
                  const SizedBox(width: 24),
                  Text(
                    'Máximo: ${value['max']}',
                    style: AppTypography.bodyMedium(context),
                  ),
                ],
              ),
            ] else ...[
              // Outro tipo de mapa
              Text(
                'Configuração:',
                style: AppTypography.labelMedium(context),
              ),
              const SizedBox(height: 8),
              ...value.entries.map((e) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 4.0),
                  child: Text(
                    '${_formatParamName(e.key.toString())}: ${e.value}',
                    style: AppTypography.bodyMedium(context),
                  ),
                );
              }),
            ],
          ] else ...[
            // Valor simples
            Text(
              'Valor:',
              style: AppTypography.labelMedium(context),
            ),
            const SizedBox(height: 8),
            Text(
              value.toString(),
              style: AppTypography.bodyMedium(context),
            ),
          ],
        ],
      ),
    );
  }

  /// Constrói o card de parâmetro
  Widget _buildParamCard({
    required BuildContext context,
    required String name,
    required String value,
    bool isMetric = false,
  }) {
    final color = isMetric ? AppColors.primary : AppColors.secondary;
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

  /// Constrói o card de métrica
  Widget _buildMetricCard({
    required BuildContext context,
    required String name,
    required String value,
    bool isMetric = false,
  }) {
    final colors = [
      AppColors.primary,
      AppColors.secondary,
      AppColors.tertiary,
      AppColors.info,
    ];

    final index = name.hashCode % colors.length;
    final color = colors[index];

    return _buildParamCard(
      context: context,
      name: name,
      value: value,
      isMetric: true,
    );
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

  /// Constrói o badge de status
  Widget _buildStatusBadge(BuildContext context, HyperparamSearch search) {
    return AppBadge(
      text: search.statusDisplay,
      color: _getStatusColor(search.status),
      prefixIcon: _getStatusIcon(search.status),
    );
  }

  /// Verifica se deve mostrar botões de ação
  bool _shouldShowActionButtons(HyperparamSearch search) {
    return search.status == 'completed' &&
        (search.bestParams != null || search.trainingSessionId != null);
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
      default:
        return Icons.help_outline;
    }
  }

  /// Obtém uma mensagem para o status
  String _getStatusMessage(String status) {
    switch (status) {
      case 'pending':
        return 'A busca está aguardando para iniciar.';
      case 'failed':
        return 'A busca falhou. Verifique os logs para mais detalhes.';
      default:
        return '';
    }
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