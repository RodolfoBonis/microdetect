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

class DatasetsPage extends StatefulWidget {
  const DatasetsPage({Key? key}) : super(key: key);

  @override
  State<DatasetsPage> createState() => _DatasetsPageState();
}

class _DatasetsPageState extends State<DatasetsPage> {
  late final DatasetController controller;
  late final TextEditingController searchController;

  @override
  void initState() {
    controller = Get.find<DatasetController>(tag: 'datasetController');
    searchController = TextEditingController();
    super.initState();
  }

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDarkMode = Theme
        .of(context)
        .brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDarkMode ? AppColors.surfaceDark : AppColors.white,
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.medium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Estatísticas
            Obx(() {
              return DatasetStatsWrapper(datasets: controller.datasets);
            }),
            const SizedBox(height: AppSpacing.medium),

            // Barra de ferramentas
            DatasetToolbar(
              searchController: searchController,
              onSearch: controller.setSearchQuery,
              onRefresh: controller.fetchDatasets,
              onCreateDataset: () => _showCreateDatasetModal(context),
            ),
            const SizedBox(height: AppSpacing.medium),

            // Lista/Grid de datasets
            Expanded(
              child: DatasetsListWrapper(
                controller: controller,
                onNavigateToDetail: _navigateToDatasetDetail,
                onEdit: (dataset) => _showEditDatasetModal(context, dataset),
                onDelete: (dataset) => _confirmDeleteDataset(context, dataset),
                searchController: searchController,
                onCreateDataset: () => _showCreateDatasetModal(context),
              ),
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
      builder: (context) =>
          AlertDialog(
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
}

// Widget separado para as estatísticas
class DatasetStatsWrapper extends StatelessWidget {
  final List<Dataset> datasets;

  const DatasetStatsWrapper({Key? key, required this.datasets})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    return DatasetStats(datasets: datasets);
  }
}

// Widget separado para a lista de datasets
class DatasetsListWrapper extends StatelessWidget {
  final DatasetController controller;
  final ValueChanged<Dataset> onNavigateToDetail;
  final ValueChanged<Dataset> onEdit;
  final ValueChanged<Dataset> onDelete;
  final TextEditingController searchController;
  final VoidCallback onCreateDataset;

  const DatasetsListWrapper({
    Key? key,
    required this.controller,
    required this.onNavigateToDetail,
    required this.onEdit,
    required this.onDelete,
    required this.searchController,
    required this.onCreateDataset,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Obx(() {
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
        return _buildEmptySearchState(context);
      }

      return _buildDatasetGrid(context, filteredDatasets);
    });
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
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
                onPressed: onCreateDataset,
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
      ),
    );
  }

  Widget _buildEmptySearchState(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
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
      ),
    );
  }

  Widget _buildDatasetGrid(BuildContext context, List<Dataset> datasets) {
    return LayoutBuilder(
      builder: (context, constraints) {
        // Largura mínima de cada card para manter legibilidade
        const double minCardWidth = 280;

        int crossAxisCount = (constraints.maxWidth / minCardWidth).floor();
        crossAxisCount = crossAxisCount > 0 ? crossAxisCount : 1;

        final double spacing = constraints.maxWidth < 600
            ? AppSpacing.xSmall
            : AppSpacing.small;

        return GridView.builder(
          padding: EdgeInsets.all(spacing),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: crossAxisCount,
            crossAxisSpacing: spacing,
            mainAxisSpacing: spacing,
            childAspectRatio: 1.0,
          ),
          itemCount: datasets.length,
          itemBuilder: (context, index) {
            final dataset = datasets[index];
            return DatasetCard(
              dataset: dataset,
              onTap: () => onNavigateToDetail(dataset),
              onEdit: () => onEdit(dataset),
              onDelete: () => onDelete(dataset),
            );
          },
        );
      },
    );
  }
}
