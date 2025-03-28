import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_borders.dart';

class DatasetToolbar extends StatelessWidget {
  final TextEditingController searchController;
  final Function(String) onSearch;
  final VoidCallback onRefresh;
  final VoidCallback onCreateDataset;
  final VoidCallback onToggleViewMode;
  final bool isGridView;

  const DatasetToolbar({
    Key? key,
    required this.searchController,
    required this.onSearch,
    required this.onRefresh,
    required this.onCreateDataset,
    required this.onToggleViewMode,
    required this.isGridView,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.small,
        vertical: AppSpacing.xSmall,
      ),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
        border: Border.all(
          color: Theme.of(context).dividerColor.withOpacity(0.2),
        ),
      ),
      child: Row(
        children: [
          // Campo de busca
          Expanded(
            child: TextField(
              controller: searchController,
              decoration: InputDecoration(
                hintText: 'Buscar datasets...',
                prefixIcon: const Icon(Icons.search, size: 20),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
                  borderSide: BorderSide(
                    color: Theme.of(context).dividerColor,
                    width: 1,
                  ),
                ),
                contentPadding: const EdgeInsets.symmetric(
                  vertical: 8,
                  horizontal: AppSpacing.small,
                ),
                isDense: true,
              ),
              onChanged: onSearch,
            ),
          ),
          
          const SizedBox(width: AppSpacing.small),
          
          // Botões de visualização (grade/lista)
          ToggleButtons(
            borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
            constraints: const BoxConstraints(
              minWidth: 36,
              minHeight: 36,
            ),
            isSelected: [isGridView, !isGridView],
            onPressed: (_) => onToggleViewMode(),
            children: const [
              Tooltip(
                message: 'Visualização em grade',
                child: Padding(
                  padding: EdgeInsets.all(6),
                  child: Icon(Icons.grid_view, size: 18),
                ),
              ),
              Tooltip(
                message: 'Visualização em lista',
                child: Padding(
                  padding: EdgeInsets.all(6),
                  child: Icon(Icons.view_list, size: 18),
                ),
              ),
            ],
          ),
          
          const SizedBox(width: AppSpacing.small),
          
          // Botão de atualização
          IconButton(
            onPressed: onRefresh,
            icon: const Icon(Icons.refresh, size: 20),
            tooltip: 'Atualizar',
            color: AppColors.secondary,
            constraints: const BoxConstraints(
              minWidth: 36,
              minHeight: 36,
            ),
            style: IconButton.styleFrom(
              backgroundColor: AppColors.secondary.withOpacity(0.1),
            ),
            padding: const EdgeInsets.all(8),
          ),
          
          const SizedBox(width: AppSpacing.small),
          
          // Botão para criar novo dataset
          SizedBox(
            height: 36,
            child: ElevatedButton.icon(
              onPressed: onCreateDataset,
              icon: const Icon(Icons.add, size: 18),
              label: const Text('Novo Dataset'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.small,
                ),
                textStyle: AppTypography.labelMedium(context).copyWith(
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
} 