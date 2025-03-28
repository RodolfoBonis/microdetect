import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';
import 'package:microdetect/features/datasets/widgets/dataset_card.dart';
import 'package:microdetect/features/datasets/widgets/dataset_form_modal.dart';
import 'package:microdetect/features/datasets/widgets/dataset_stats.dart';
import 'package:microdetect/features/datasets/widgets/dataset_toolbar.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/routes/app_pages.dart';
import '../models/dataset.dart';

class DatasetsPage extends GetView<DatasetController> {
  const DatasetsPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Controller para o campo de busca
    final TextEditingController searchController = TextEditingController();

    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.medium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Estatísticas
            Obx(() => DatasetStats(datasets: controller.datasets)),
            const SizedBox(height: AppSpacing.medium),

            // Barra de ferramentas
            Obx(() => DatasetToolbar(
              searchController: searchController,
              onSearch: controller.setSearchQuery,
              onRefresh: controller.fetchDatasets,
              onCreateDataset: () => _showCreateDatasetModal(context),
              onToggleViewMode: controller.toggleViewMode,
              isGridView: controller.isGridView,
            )),
            const SizedBox(height: AppSpacing.medium),

            // Lista/Grid de datasets
            Expanded(
              child: Obx(() {
                // Mostrar loading
                if (controller.isLoading && controller.datasets.isEmpty) {
                  return const Center(
                    child: CircularProgressIndicator(),
                  );
                }

                // Mostrar estado vazio
                if (controller.datasets.isEmpty) {
                  return _buildEmptyState(context);
                }

                // Mostrar datasets (filtrados)
                final filteredDatasets = controller.getFilteredDatasets();
                
                if (filteredDatasets.isEmpty) {
                  return _buildEmptySearchState(context, searchController);
                }

                return controller.isGridView
                    ? _buildDatasetGrid(context, filteredDatasets)
                    : _buildDatasetListView(context, filteredDatasets);
              }),
            ),
          ],
        ),
      ),
    );
  }

  void _showCreateDatasetModal(BuildContext context) {
    DatasetFormModal.show(
      context: context,
      onSubmit: (name, description, classes) => 
        controller.createDataset(
          name: name,
          description: description,
          classes: classes,
        ),
    );
  }

  void _showEditDatasetModal(BuildContext context, Dataset dataset) {
    DatasetFormModal.show(
      context: context,
      isEditing: true,
      dataset: dataset,
      onSubmit: (name, description, classes) => 
        controller.updateDataset(
          id: dataset.id,
          name: name,
          description: description,
          classes: classes,
        ),
    );
  }

  void _confirmDeleteDataset(BuildContext context, Dataset dataset) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Excluir Dataset'),
        content: Text(
          'Tem certeza que deseja excluir o dataset "${dataset.name}"? '
          'Esta ação não pode ser desfeita e todos os dados associados serão perdidos.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('CANCELAR'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              controller.deleteDataset(dataset.id);
            },
            child: const Text('EXCLUIR'),
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
          ),
        ],
      ),
    );
  }

  void _navigateToDatasetDetail(Dataset dataset) {
    Get.rootDelegate.toNamed(
      '${AppRoutes.datasets}/${dataset.id}',
      arguments: {'datasetId': dataset.id},
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 600),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(AppSpacing.medium),
              decoration: BoxDecoration(
                color: AppColors.tertiary.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.folder_open,
                size: 80,
                color: AppColors.tertiary,
              ),
            ),
            const SizedBox(height: AppSpacing.medium),
            Text(
              'Nenhum dataset encontrado',
              style: AppTypography.headlineLarge(context),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.small),
            Text(
              'Crie um novo dataset para começar a catalogar e treinar seus modelos',
              style: AppTypography.bodyLarge(context),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.large),
            ElevatedButton.icon(
              onPressed: () => _showCreateDatasetModal(context),
              icon: const Icon(Icons.add),
              label: const Text('Criar Novo Dataset'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.medium,
                  vertical: AppSpacing.small,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptySearchState(BuildContext context, TextEditingController searchController) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.search_off,
            size: 64,
            color: AppColors.grey,
          ),
          const SizedBox(height: AppSpacing.medium),
          Text(
            'Nenhum dataset encontrado com "${controller.searchQuery}"',
            style: AppTypography.titleLarge(context),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: AppSpacing.medium),
          ElevatedButton.icon(
            onPressed: () {
              searchController.clear();
              controller.clearSearchQuery();
            },
            icon: const Icon(Icons.clear),
            label: const Text('Limpar busca'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.secondary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDatasetGrid(BuildContext context, List<Dataset> datasets) {
    return GridView.builder(
      padding: const EdgeInsets.all(AppSpacing.small),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        childAspectRatio: 2 / 1,
        crossAxisSpacing: AppSpacing.small,
        mainAxisSpacing: AppSpacing.small,
      ),
      itemCount: datasets.length,
      itemBuilder: (context, index) {
        final dataset = datasets[index];
        return DatasetCard(
          dataset: dataset,
          onTap: () => _navigateToDatasetDetail(dataset),
          onEdit: () => _showEditDatasetModal(context, dataset),
          onDelete: () => _confirmDeleteDataset(context, dataset),
        );
      },
    );
  }

  Widget _buildDatasetListView(BuildContext context, List<Dataset> datasets) {
    return ListView.builder(
      padding: const EdgeInsets.all(AppSpacing.small),
      itemCount: datasets.length,
      itemBuilder: (context, index) {
        final dataset = datasets[index];
        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.small),
          child: DatasetCard(
            dataset: dataset,
            onTap: () => _navigateToDatasetDetail(dataset),
            onEdit: () => _showEditDatasetModal(context, dataset),
            onDelete: () => _confirmDeleteDataset(context, dataset),
          ),
        );
      },
    );
  }
} 