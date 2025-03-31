import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_borders.dart';

class DatasetToolbar extends StatelessWidget {
  final TextEditingController searchController;
  final Function(String) onSearch;
  final VoidCallback onRefresh;
  final VoidCallback onCreateDataset;

  const DatasetToolbar({
    Key? key,
    required this.searchController,
    required this.onSearch,
    required this.onRefresh,
    required this.onCreateDataset,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
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
                vertical: AppSpacing.medium,
                horizontal: AppSpacing.small,
              ),
              isDense: true,
            ),
            onChanged: onSearch,
          ),
        ),

        const SizedBox(width: AppSpacing.small),

        // Botão de atualização
        // IconButton(
        //   onPressed: onRefresh,
        //   icon: const Icon(Icons.refresh, size: 20),
        //   tooltip: 'Atualizar',
        //   color: AppColors.secondary,
        //   constraints: const BoxConstraints(
        //     minWidth: 36,
        //     minHeight: 36,
        //   ),
        //   style: IconButton.styleFrom(
        //     backgroundColor: AppColors.secondary.withOpacity(0.1),
        //   ),
        //   padding: const EdgeInsets.all(8),
        // ),

        const SizedBox(width: AppSpacing.small),

        // Botão para criar novo dataset
        AppButton(
          onPressed: onCreateDataset,
          prefixIcon: Icons.add_circle_outline,
          label: 'Novo Dataset',
          size: AppButtonSize.medium,
        ),
      ],
    );
  }
} 