import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import 'package:microdetect/core/widgets/base_page_scaffold.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';
import 'package:microdetect/routes/app_pages.dart';

import '../controllers/hyperparameter_search_controller.dart';
import '../widgets/cards/hyperparameter_search_card.dart';
import '../widgets/forms/hyperparameter_search_form.dart';

/// Página para listar e iniciar buscas de hiperparâmetros
class HyperparameterSearchPage extends StatelessWidget {
  final hyperparamController = Get.find<HyperparameterSearchController>();
  final datasetController =
      Get.find<DatasetController>(tag: 'datasetController');

  /// Construtor
  HyperparameterSearchPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return BasePageScaffold(
      title: 'Otimização de Hiperparâmetros',
      actions: [
        Obx(() => IconButton(
              icon: Icon(
                hyperparamController.autoRefresh.value
                    ? Icons.autorenew
                    : Icons.autorenew_outlined,
                color: hyperparamController.autoRefresh.value
                    ? AppColors.primary
                    : ThemeColors.icon(context),
              ),
              tooltip: hyperparamController.autoRefresh.value
                  ? 'Atualização automática ativada'
                  : 'Atualização automática desativada',
              onPressed: () => hyperparamController.toggleAutoRefresh(
                !hyperparamController.autoRefresh.value,
              ),
            )),
        IconButton(
          icon: const Icon(Icons.refresh),
          tooltip: 'Atualizar',
          onPressed: () => hyperparamController.fetchHyperparamSearches(),
        ),
      ],
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateSearchDialog(context),
        icon: const Icon(Icons.add, color: AppColors.white),
        label: Text(
          'Nova Busca',
          style: AppTypography.headlineMedium(context).copyWith(
            color: AppColors.white,
          ),
        ),
        backgroundColor: AppColors.primary,
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Seção de filtros
          _buildFiltersSection(
              context, hyperparamController, datasetController),

          // Lista de buscas
          Expanded(
            child: Obx(() {
              if (hyperparamController.isLoading.value) {
                return const Center(
                  child: CircularProgressIndicator(),
                );
              }

              if (hyperparamController.errorMessage.value.isNotEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(
                        Icons.error_outline,
                        size: 48,
                        color: AppColors.error,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Erro ao carregar buscas de hiperparâmetros',
                        style: AppTypography.titleSmall(context),
                      ),
                      const SizedBox(height: 8),
                      Padding(
                        padding: AppSpacing.paddingHorizontalLarge,
                        child: Text(
                          hyperparamController.errorMessage.value,
                          style: AppTypography.bodyMedium(context),
                          textAlign: TextAlign.center,
                        ),
                      ),
                      const SizedBox(height: 16),
                      AppButton(
                        label: 'Tentar novamente',
                        onPressed: () =>
                            hyperparamController.fetchHyperparamSearches(),
                        type: AppButtonType.secondary,
                        prefixIcon: Icons.refresh,
                      ),
                    ],
                  ),
                );
              }

              if (hyperparamController.searches.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.auto_fix_high,
                        size: 64,
                        color: ThemeColors.textSecondary(context),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Nenhuma busca de hiperparâmetros encontrada',
                        style: AppTypography.titleSmall(context),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Crie uma nova busca para encontrar os melhores parâmetros para seu modelo',
                        style: AppTypography.bodyMedium(context).copyWith(
                          color: ThemeColors.textSecondary(context),
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 24),
                      AppButton(
                        label: 'Nova Busca',
                        onPressed: () => _showCreateSearchDialog(context),
                        prefixIcon: Icons.add,
                      ),
                    ],
                  ),
                );
              }

              return ListView.builder(
                padding: AppSpacing.paddingMedium,
                itemCount: hyperparamController.searches.length,
                itemBuilder: (context, index) {
                  final search = hyperparamController.searches[index];
                  return HyperparameterSearchCard(
                    search: search,
                    onTap: () {
                      if (search.id > 0) {
                        hyperparamController.selectHyperparamSearch(search.id);
                        // Make sure the route is properly defined and matches the route registration
                        Get.toNamed('${AppRoutes.hyperparameterDetails}/${search.id}');
                      }
                    },
                    onUseBestParams: search.bestParams != null
                        ? () =>
                            hyperparamController.startTrainingWithBestParams()
                        : null,
                    onViewFinalModel: search.trainingSessionId != null
                        ? () => hyperparamController.viewFinalModel()
                        : null,
                  );
                },
              );
            }),
          ),
        ],
      ),
    );
  }

  /// Constrói a seção de filtros
  Widget _buildFiltersSection(
    BuildContext context,
    HyperparameterSearchController hyperparamController,
    DatasetController datasetController,
  ) {
    return Container(
      padding: AppSpacing.paddingMedium,
      color: ThemeColors.surfaceVariant(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Filtros',
            style: AppTypography.labelMedium(context),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              // Filtro por dataset
              Expanded(
                child: Obx(() => DropdownButtonFormField<int?>(
                      decoration: InputDecoration(
                        labelText: 'Dataset',
                        filled: true,
                        fillColor: ThemeColors.inputFill(context),
                        isDense: true,
                        contentPadding: AppSpacing.paddingSmall,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide.none,
                        ),
                      ),
                      value: hyperparamController.filterDatasetId.value,
                      items: [
                        const DropdownMenuItem<int?>(
                          value: null,
                          child: Text('Todos os datasets'),
                        ),
                        ...datasetController.datasets.map((dataset) {
                          return DropdownMenuItem<int?>(
                            value: dataset.id,
                            child: Text(dataset.name),
                          );
                        }).toList(),
                      ],
                      onChanged: (value) =>
                          hyperparamController.setDatasetFilter(value),
                    )),
              ),
              const SizedBox(width: 16),
              // Filtro por status
              Expanded(
                child: Obx(() => DropdownButtonFormField<String>(
                      decoration: InputDecoration(
                        labelText: 'Status',
                        filled: true,
                        fillColor: ThemeColors.inputFill(context),
                        isDense: true,
                        contentPadding: AppSpacing.paddingSmall,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide.none,
                        ),
                      ),
                      value: hyperparamController.filterStatus.value.isEmpty
                          ? 'all'
                          : hyperparamController.filterStatus.value,
                      items: const [
                        DropdownMenuItem<String>(
                          value: 'all',
                          child: Text('Todos os status'),
                        ),
                        DropdownMenuItem<String>(
                          value: 'pending',
                          child: Text('Pendente'),
                        ),
                        DropdownMenuItem<String>(
                          value: 'running',
                          child: Text('Em execução'),
                        ),
                        DropdownMenuItem<String>(
                          value: 'completed',
                          child: Text('Concluído'),
                        ),
                        DropdownMenuItem<String>(
                          value: 'failed',
                          child: Text('Falhou'),
                        ),
                      ],
                      onChanged: (value) =>
                          hyperparamController.setStatusFilter(
                        value == 'all' ? '' : value!,
                      ),
                    )),
              ),
              const SizedBox(width: 8),
              // Botão para limpar filtros
              Obx(() {
                final hasFilters =
                    hyperparamController.filterDatasetId.value != null ||
                        hyperparamController.filterStatus.value.isNotEmpty;

                return IconButton(
                  icon: const Icon(Icons.filter_list_off),
                  tooltip: 'Limpar filtros',
                  onPressed: hasFilters
                      ? () => hyperparamController.clearFilters()
                      : null,
                  color: hasFilters ? AppColors.primary : Colors.grey,
                );
              }),
            ],
          ),
        ],
      ),
    );
  }

  /// Exibe o diálogo para criar uma nova busca
  void _showCreateSearchDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        insetPadding: const EdgeInsets.all(16),
        child: Container(
          width: MediaQuery.of(context).size.width * 0.9,
          height: MediaQuery.of(context).size.height * 0.9,
          padding: AppSpacing.paddingMedium,
          child: Column(
            children: [
              // Cabeçalho
              Row(
                children: [
                  const Icon(
                    Icons.auto_fix_high,
                    color: AppColors.primary,
                    size: 24,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Nova Busca de Hiperparâmetros',
                    style: AppTypography.titleMedium(context),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
              const Divider(),
              // Formulário
              Expanded(
                child: HyperparameterSearchForm(
                  onSubmit: (data) {
                    Navigator.of(context).pop();
                    final controller =
                        Get.find<HyperparameterSearchController>();
                    controller.startHyperparamSearch(data);
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
