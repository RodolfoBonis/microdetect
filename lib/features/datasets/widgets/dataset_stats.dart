import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_borders.dart';
import '../models/dataset.dart';

class DatasetStats extends StatelessWidget {
  final List<Dataset> datasets;

  const DatasetStats({
    Key? key,
    required this.datasets,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Calcular estatísticas
    int totalImages = 0;
    int totalAnnotations = 0;

    final isDarkMode = Theme.of(context).brightness == Brightness.dark;
    
    for (final dataset in datasets) {
      totalImages += dataset.imagesCount;
      totalAnnotations += dataset.annotationsCount ?? 0;
    }
    
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.small,
        vertical: AppSpacing.xSmall,
      ),
      decoration: BoxDecoration(
        color: isDarkMode ? AppColors.surfaceDark : AppColors.white,
        borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
        border: Border.all(
          color: Theme.of(context).dividerColor.withOpacity(0.2),
        ),
      ),
      child: IntrinsicHeight(
        child: Row(
          children: [
            Expanded(
              child: _buildStatCard(
                context,
                'Datasets',
                datasets.length.toString(),
                Icons.folder,
                AppColors.primary,
              ),
            ),
            VerticalDivider(
              color: Theme.of(context).dividerColor.withOpacity(0.2),
              thickness: 1,
              width: AppSpacing.medium,
            ),
            Expanded(
              child: _buildStatCard(
                context,
                'Imagens',
                totalImages.toString(),
                Icons.image,
                AppColors.secondary,
              ),
            ),
            VerticalDivider(
              color: Theme.of(context).dividerColor.withOpacity(0.2),
              thickness: 1,
              width: AppSpacing.medium,
            ),
            Expanded(
              child: _buildStatCard(
                context,
                'Anotações',
                totalAnnotations.toString(),
                Icons.create,
                AppColors.info,
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildStatCard(
    BuildContext context,
    String title,
    String value,
    IconData icon,
    Color color,
  ) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.medium),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: color, size: AppSpacing.large),
              const SizedBox(width: AppSpacing.small),
              Text(
                title,
                style: AppTypography.headlineMedium(context).copyWith(
                  color: Theme.of(context).textTheme.bodySmall?.color,
                ),
              )
            ],
          ),
          const SizedBox(height: AppSpacing.small),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xxSmall),
            child: Text(
              value,
              style: AppTypography.headlineMedium(context).copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }
} 