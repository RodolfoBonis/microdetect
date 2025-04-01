import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/widgets/base_page_scaffold.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import 'package:microdetect/design_system/app_icons.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';
import 'package:microdetect/routes/app_pages.dart';

import '../controllers/training_controller.dart';
import '../widgets/cards/training_session_card.dart';

/// Página inicial do módulo de treinamento
class TrainingHomePage extends StatelessWidget {
  final trainingController = Get.find<TrainingController>();
  final datasetController =
      Get.find<DatasetController>(tag: 'datasetController');

  /// Construtor
  TrainingHomePage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return BasePageScaffold(
      title: 'Treinamento de Modelos',
      actions: [
        Obx(() => IconButton(
              icon: Icon(
                trainingController.autoRefresh.value
                    ? Icons.autorenew
                    : Icons.autorenew_outlined,
                color: trainingController.autoRefresh.value
                    ? AppColors.primary
                    : ThemeColors.icon(context),
              ),
              tooltip: trainingController.autoRefresh.value
                  ? 'Atualização automática ativada'
                  : 'Atualização automática desativada',
              onPressed: () => trainingController.toggleAutoRefresh(
                !trainingController.autoRefresh.value,
              ),
            )),
        IconButton(
          icon: const Icon(Icons.refresh),
          tooltip: 'Atualizar',
          onPressed: () => trainingController.fetchTrainingSessions(),
        ),
      ],
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Get.toNamed('/root/training/create'),
        icon: const Icon(Icons.add, color: AppColors.white),
        label: Text(
          'Novo treinamento',
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
          _buildFiltersSection(context, trainingController, datasetController),

          // Lista de sessões
          Expanded(
            child: Obx(() {
              if (trainingController.isLoading.value) {
                return const Center(
                  child: CircularProgressIndicator(),
                );
              }

              if (trainingController.errorMessage.value.isNotEmpty) {
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
                        'Erro ao carregar sessões de treinamento',
                        style: AppTypography.titleSmall(context),
                      ),
                      const SizedBox(height: 8),
                      Padding(
                        padding: AppSpacing.paddingHorizontalLarge,
                        child: Text(
                          trainingController.errorMessage.value,
                          style: AppTypography.bodyMedium(context),
                          textAlign: TextAlign.center,
                        ),
                      ),
                      const SizedBox(height: 16),
                      AppButton(
                        label: 'Tentar novamente',
                        onPressed: () =>
                            trainingController.fetchTrainingSessions(),
                        type: AppButtonType.secondary,
                        prefixIcon: Icons.refresh,
                      ),
                    ],
                  ),
                );
              }

              if (trainingController.trainingSessions.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        AppIcons.analysis,
                        size: 64,
                        color: ThemeColors.textSecondary(context),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Nenhuma sessão de treinamento encontrada',
                        style: AppTypography.titleSmall(context),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Crie um novo treinamento para começar',
                        style: AppTypography.bodyMedium(context).copyWith(
                          color: ThemeColors.textSecondary(context),
                        ),
                      ),
                      const SizedBox(height: 24),
                      AppButton(
                        label: 'Novo treinamento',
                        onPressed: () => Get.toNamed('/root/training/create'),
                        prefixIcon: Icons.add,
                      ),
                      const SizedBox(height: 16),
                      AppButton(
                        label: 'Otimizar hiperparâmetros',
                        onPressed: () =>
                            Get.rootDelegate.toNamed(AppRoutes.hyperparameters),
                        type: AppButtonType.secondary,
                        prefixIcon: Icons.auto_fix_high,
                      ),
                    ],
                  ),
                );
              }

              return ListView.builder(
                padding: AppSpacing.paddingMedium,
                itemCount: trainingController.trainingSessions.length,
                itemBuilder: (context, index) {
                  final session = trainingController.trainingSessions[index];
                  return TrainingSessionCard(
                    session: session,
                    onTap: () {
                      trainingController.selectTrainingSession(session.id);
                      Get.toNamed('/root/training/details/${session.id}');
                    },
                    onPause: session.canBePaused
                        ? () => trainingController.pauseTraining(session.id)
                        : null,
                    onResume: session.canBeResumed
                        ? () => trainingController.resumeTraining(session.id)
                        : null,
                    onCancel: session.canBeCancelled
                        ? () => _showCancelConfirmDialog(
                            context, trainingController, session.id)
                        : null,
                  );
                },
              );
            }),
          ),

          // Seção de hiperparâmetros
          _buildHyperParamSection(context),
        ],
      ),
    );
  }

  /// Constrói a seção de filtros
  Widget _buildFiltersSection(
    BuildContext context,
    TrainingController trainingController,
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
                      value: trainingController.filterDatasetId.value,
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
                          trainingController.setDatasetFilter(value),
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
                      value: trainingController.filterStatus.value.isEmpty
                          ? 'all'
                          : trainingController.filterStatus.value,
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
                        DropdownMenuItem<String>(
                          value: 'paused',
                          child: Text('Pausado'),
                        ),
                      ],
                      onChanged: (value) => trainingController.setStatusFilter(
                        value == 'all' ? '' : value!,
                      ),
                    )),
              ),
              const SizedBox(width: 8),
              // Botão para limpar filtros
              Obx(() {
                final hasFilters =
                    trainingController.filterDatasetId.value != null ||
                        trainingController.filterStatus.value.isNotEmpty;

                return IconButton(
                  icon: const Icon(Icons.filter_list_off),
                  tooltip: 'Limpar filtros',
                  onPressed: hasFilters
                      ? () => trainingController.clearFilters()
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

  /// Constrói a seção de hiperparâmetros
  Widget _buildHyperParamSection(BuildContext context) {
    return Container(
      padding: AppSpacing.paddingMedium,
      decoration: BoxDecoration(
        color: ThemeColors.surfaceVariant(context),
        border: Border(
          top: BorderSide(
            color: ThemeColors.border(context),
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Otimização de Hiperparâmetros',
                  style: AppTypography.titleSmall(context),
                ),
                const SizedBox(height: 4),
                Text(
                  'Encontre os melhores parâmetros para seu modelo',
                  style: AppTypography.bodySmall(context).copyWith(
                    color: ThemeColors.textSecondary(context),
                  ),
                ),
              ],
            ),
          ),
          AppButton(
            label: 'Iniciar busca',
            onPressed: () => Get.toNamed('/root/training/hyperparameters'),
            type: AppButtonType.secondary,
            prefixIcon: Icons.auto_fix_high,
          ),
        ],
      ),
    );
  }

  /// Exibe diálogo de confirmação para cancelar treinamento
  void _showCancelConfirmDialog(
    BuildContext context,
    TrainingController controller,
    int sessionId,
  ) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancelar treinamento'),
        content: const Text(
            'Tem certeza que deseja cancelar este treinamento? Esta ação não pode ser desfeita.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              controller.cancelTraining(sessionId);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              foregroundColor: Colors.white,
            ),
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );
  }
}
