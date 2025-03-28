import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/annotation/controllers/annotation_controller.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';

/// Widget para seleção de datasets
class DatasetSelector extends StatelessWidget {
  const DatasetSelector({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final AnnotationController controller = Get.find<AnnotationController>();
    
    return Container(
      padding: const EdgeInsets.all(AppSpacing.medium),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(
          bottom: BorderSide(
            color: AppColors.surfaceDark,
            width: 1,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'Dataset',
            style: AppTypography.labelLarge(context),
          ),
          const SizedBox(height: AppSpacing.xSmall),
          Obx(() {
            if (controller.isLoading.value) {
              return const SizedBox(
                height: 48,
                child: Center(
                  child: CircularProgressIndicator(),
                ),
              );
            }
            
            if (controller.datasets.isEmpty) {
              return Container(
                padding: const EdgeInsets.all(AppSpacing.small),
                decoration: BoxDecoration(
                  color: AppColors.surfaceLight,
                  borderRadius: BorderRadius.circular(AppSpacing.xSmall),
                ),
                child: Text(
                  'Nenhum dataset disponível',
                  style: AppTypography.bodyMedium(context),
                ),
              );
            }
            
            return Container(
              height: 48,
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.small),
              decoration: BoxDecoration(
                color: AppColors.white,
                borderRadius: BorderRadius.circular(AppSpacing.xSmall),
                border: Border.all(color: AppColors.surfaceDark),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<Dataset>(
                  value: controller.selectedDataset.value,
                  hint: Text(
                    'Selecione um dataset',
                    style: AppTypography.bodyMedium(context),
                  ),
                  isExpanded: true,
                  icon: const Icon(Icons.arrow_drop_down),
                  elevation: 2,
                  style: AppTypography.bodyMedium(context),
                  onChanged: (Dataset? dataset) {
                    if (dataset != null) {
                      controller.selectDataset(dataset);
                    }
                  },
                  items: controller.datasets
                      .map<DropdownMenuItem<Dataset>>((Dataset dataset) {
                    return DropdownMenuItem<Dataset>(
                      value: dataset,
                      child: _DatasetItem(dataset: dataset),
                    );
                  }).toList(),
                ),
              ),
            );
          }),
          
          // Informações do dataset selecionado
          Obx(() {
            if (controller.selectedDataset.value == null) {
              return const SizedBox.shrink();
            }
            
            final dataset = controller.selectedDataset.value!;
            
            return Padding(
              padding: const EdgeInsets.only(top: AppSpacing.small),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Estatísticas do dataset
                  Row(
                    children: [
                      _DatasetStatistic(
                        icon: Icons.image_outlined,
                        label: 'Imagens',
                        value: dataset.imagesCount.toString(),
                      ),
                      const SizedBox(width: AppSpacing.medium),
                      _DatasetStatistic(
                        icon: Icons.category_outlined,
                        label: 'Classes',
                        value: dataset.classes.length.toString(),
                      ),
                      const SizedBox(width: AppSpacing.medium),
                      if (dataset.annotationsCount != null)
                        _DatasetStatistic(
                          icon: Icons.add_box_outlined,
                          label: 'Anotações',
                          value: dataset.annotationsCount.toString(),
                        ),
                    ],
                  ),
                  
                  // Descrição do dataset
                  if (dataset.description != null && dataset.description!.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: AppSpacing.small),
                      child: Text(
                        dataset.description!,
                        style: AppTypography.bodySmall(context),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}

/// Widget para exibir um item no dropdown de datasets
class _DatasetItem extends StatelessWidget {
  final Dataset dataset;

  const _DatasetItem({
    Key? key,
    required this.dataset,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.xxSmall),
      child: Row(
        children: [
          // Ícone
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: AppColors.surfaceLight,
              borderRadius: BorderRadius.circular(AppSpacing.xxSmall),
            ),
            child: const Icon(
              Icons.folder_outlined,
              color: AppColors.primary,
              size: 18,
            ),
          ),
          const SizedBox(width: AppSpacing.small),
          
          // Informações do dataset
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  dataset.name,
                  style: AppTypography.bodyMedium(context).copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  '${dataset.imagesCount} imagens · ${dataset.classes.length} classes',
                  style: AppTypography.bodySmall(context),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Widget para exibir uma estatística do dataset
class _DatasetStatistic extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _DatasetStatistic({
    Key? key,
    required this.icon,
    required this.label,
    required this.value,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          icon,
          size: 16,
          color: AppColors.grey,
        ),
        const SizedBox(width: AppSpacing.xxSmall),
        RichText(
          text: TextSpan(
            children: [
              TextSpan(
                text: value,
                style: AppTypography.bodyMedium(context).copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              TextSpan(
                text: ' $label',
                style: AppTypography.bodySmall(context).copyWith(
                  color: AppColors.grey,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
} 