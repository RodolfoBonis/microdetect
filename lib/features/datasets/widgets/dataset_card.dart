import 'package:flutter/material.dart';
import '../../../design_system/app_colors.dart';
import '../../../design_system/app_spacing.dart';
import '../../../design_system/app_borders.dart';
import '../../../design_system/app_typography.dart';
import '../models/dataset.dart';

class DatasetCard extends StatelessWidget {
  final Dataset dataset;
  final VoidCallback? onTap;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;
  final bool isSelected;

  const DatasetCard({
    Key? key,
    required this.dataset,
    this.onTap,
    this.onEdit,
    this.onDelete,
    this.isSelected = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isDarkMode = Theme.of(context).brightness == Brightness.dark;
    
    return Card(
      elevation: 1,
      margin: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
        side: isSelected
            ? BorderSide(color: AppColors.primary, width: 2)
            : BorderSide(
                color: isDarkMode 
                    ? Colors.grey.shade800 
                    : Colors.grey.shade200,
                width: 1,
              ),
      ),
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(context),
            if (dataset.description != null && dataset.description!.isNotEmpty)
              _buildDescription(context),
            _buildStats(context),
            if (dataset.classes.isNotEmpty)
              _buildClasses(context),
          ],
        ),
      ),
    );
  }
  
  Widget _buildHeader(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.small,
        vertical: AppSpacing.xSmall,
      ),
      decoration: BoxDecoration(
        color: isSelected 
            ? AppColors.primary.withOpacity(0.1)
            : AppColors.secondary.withOpacity(0.05),
        border: Border(
          bottom: BorderSide(
            color: isSelected 
                ? AppColors.primary.withOpacity(0.2)
                : Colors.grey.withOpacity(0.2),
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.folder,
            size: 18,
            color: AppColors.secondary,
          ),
          const SizedBox(width: AppSpacing.xSmall),
          Expanded(
            child: Text(
              dataset.name,
              style: AppTypography.titleMedium(context).copyWith(
                fontWeight: FontWeight.w600,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (onEdit != null)
                IconButton(
                  icon: const Icon(Icons.edit_outlined, size: 18),
                  color: AppColors.tertiary,
                  tooltip: 'Editar dataset',
                  onPressed: onEdit,
                  constraints: const BoxConstraints(
                    minWidth: 30,
                    minHeight: 30,
                  ),
                  padding: EdgeInsets.zero,
                  visualDensity: VisualDensity.compact,
                ),
              if (onDelete != null)
                IconButton(
                  icon: const Icon(Icons.delete_outline, size: 18),
                  color: AppColors.error,
                  tooltip: 'Excluir dataset',
                  onPressed: onDelete,
                  constraints: const BoxConstraints(
                    minWidth: 30,
                    minHeight: 30,
                  ),
                  padding: EdgeInsets.zero,
                  visualDensity: VisualDensity.compact,
                ),
            ],
          ),
        ],
      ),
    );
  }
  
  Widget _buildDescription(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.small,
        AppSpacing.xSmall,
        AppSpacing.small,
        0,
      ),
      child: Text(
        dataset.description!,
        style: AppTypography.bodySmall(context).copyWith(
          color: Theme.of(context).textTheme.bodySmall?.color?.withOpacity(0.7),
        ),
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
      ),
    );
  }
  
  Widget _buildStats(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.small),
      child: Row(
        children: [
          Expanded(
            child: Row(
              children: [
                const Icon(
                  Icons.calendar_today_outlined,
                  size: 14,
                  color: AppColors.grey,
                ),
                const SizedBox(width: 4),
                Text(
                  dataset.formattedUpdatedAt,
                  style: AppTypography.labelSmall(context).copyWith(
                    color: AppColors.grey,
                  ),
                ),
              ],
            ),
          ),
          _buildStatItem(context, 'Imagens', dataset.imagesCount.toString(), Icons.image_outlined),
          const SizedBox(width: AppSpacing.small),
          _buildStatItem(context, 'Anotações', dataset.annotationsCount?.toString() ?? '0', Icons.edit_outlined),
        ],
      ),
    );
  }
  
  Widget _buildStatItem(BuildContext context, String label, String value, IconData icon) {
    return Row(
      children: [
        Icon(
          icon,
          size: 14,
          color: AppColors.secondary,
        ),
        const SizedBox(width: 4),
        Text(
          '$value $label',
          style: AppTypography.labelSmall(context),
        ),
      ],
    );
  }
  
  Widget _buildClasses(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.small,
        0,
        AppSpacing.small,
        AppSpacing.small,
      ),
      child: Wrap(
        spacing: AppSpacing.xxSmall,
        runSpacing: AppSpacing.xxSmall,
        children: dataset.classes.take(3).map((className) {
          return Container(
            padding: const EdgeInsets.symmetric(
              horizontal: 6,
              vertical: 2,
            ),
            decoration: BoxDecoration(
              color: AppColors.tertiary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
              border: Border.all(
                color: AppColors.tertiary.withOpacity(0.3),
                width: 1,
              ),
            ),
            child: Text(
              className,
              style: AppTypography.labelSmall(context).copyWith(
                color: AppColors.tertiary,
                fontSize: 10,
              ),
            ),
          );
        }).toList() + [
          if (dataset.classes.length > 3)
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 6,
                vertical: 2,
              ),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
                border: Border.all(
                  color: AppColors.primary.withOpacity(0.3),
                  width: 1,
                ),
              ),
              child: Text(
                '+${dataset.classes.length - 3}',
                style: AppTypography.labelSmall(context).copyWith(
                  color: AppColors.primary,
                  fontSize: 10,
                ),
              ),
            ),
        ],
      ),
    );
  }
} 