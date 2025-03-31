import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:microdetect/core/utils/extensions/datetime_extension.dart';
import 'package:microdetect/core/utils/extensions/str_extensions.dart';
import 'package:microdetect/design_system/app_badge.dart';
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
  final double? width;
  final double? height;

  const DatasetCard({
    Key? key,
    required this.dataset,
    this.onTap,
    this.onEdit,
    this.onDelete,
    this.width,
    this.height,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isDarkMode = Theme.of(context).brightness == Brightness.dark;

    final Color descriptionColor = isDarkMode
        ? AppColors.white.withValues(alpha: .5)
        : AppColors.black.withValues(alpha: .5);

    return LayoutBuilder(
      builder: (context, constraints) {
        // Determinar se estamos em um card muito estreito
        final isNarrow = constraints.maxWidth < 300;
        
        return Container(
          margin: EdgeInsets.zero,
          clipBehavior: Clip.antiAlias,
          decoration: BoxDecoration(
            color: isDarkMode ? AppColors.surfaceDark : AppColors.white,
            borderRadius: BorderRadius.circular(AppBorders.radiusXLarge),
            border: Border.all(
              color: isDarkMode ? Colors.grey.shade800 : Colors.grey.shade200,
              width: 1,
            ),
            boxShadow: AppColors.shadow,
          ),
          child: InkWell(
            onTap: onTap,
            enableFeedback: true,
            child: SizedBox(
              width: width,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Imagem do dataset
                  Stack(
                    children: [
                      AspectRatio(
                        aspectRatio: 21 / 9,
                        child: CachedNetworkImage(
                          imageUrl: dataset.thumb,
                          fit: BoxFit.cover,
                          width: double.infinity,
                          placeholder: (context, url) => Container(
                            color: isDarkMode ? Colors.grey.shade800 : Colors.grey.shade200,
                            child: const Center(
                              child: Icon(
                                Icons.image,
                                color: AppColors.grey,
                                size: 36,
                              ),
                            ),
                          ),
                          errorWidget: (context, url, error) => Container(
                            color: isDarkMode ? Colors.grey.shade800 : Colors.grey.shade200,
                            child: const Center(
                              child: Icon(
                                Icons.broken_image,
                                color: AppColors.error,
                                size: 36,
                              ),
                            ),
                          ),
                        ),
                      ),
                      Positioned(
                        right: AppSpacing.small,
                        top: AppSpacing.small,
                        child: AppBadge(
                          text: '${dataset.imagesCount} ${dataset.imagesCount == 1 ? 'Imagem' : 'Imagens'}',
                          color: AppColors.primary,
                          prefixIcon: Icons.image,
                          radius: AppSpacing.xxSmall,
                        ),
                      )
                    ],
                  ),
                  
                  // Conteúdo do card
                  Padding(
                    padding: EdgeInsets.all(isNarrow ? AppSpacing.small : AppSpacing.medium),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // Nome do dataset
                        Text(
                          dataset.name.toTitleCase(),
                          style: (isNarrow 
                              ? AppTypography.headlineSmall(context) 
                              : AppTypography.headlineMedium(context))
                              .copyWith(
                                fontWeight: FontWeight.w600,
                              ),
                          overflow: TextOverflow.ellipsis,
                          maxLines: 2,
                        ),
                        
                        SizedBox(height: isNarrow ? AppSpacing.xxSmall : AppSpacing.xxxSmall),
                        
                        // Descrição (opcional)
                        if (dataset.description != null && dataset.description!.isNotEmpty)
                          Text(
                            dataset.description!.toTitleCase(),
                            style: AppTypography.labelMedium(context).copyWith(
                              color: descriptionColor,
                              fontSize: isNarrow ? 11 : null,
                            ),
                            overflow: TextOverflow.ellipsis,
                            maxLines: 2,
                          ),
                        
                        SizedBox(height: isNarrow ? AppSpacing.small : AppSpacing.medium),
                        
                        // Classes (badges)
                        ConstrainedBox(
                          constraints: BoxConstraints(
                            maxHeight: isNarrow ? 60 : 80,
                          ),
                          child: SingleChildScrollView(
                            child: Wrap(
                              spacing: AppSpacing.xSmall,
                              runSpacing: AppSpacing.xxSmall,
                              children: dataset.classes.length <= 2
                                  ? dataset.classes
                                      .map(
                                        (classe) => AppBadge(
                                          text: classe.toTitleCase(),
                                          color: AppColors.primary,
                                        ),
                                      )
                                      .toList()
                                  : [
                                      ...dataset.classes.take(2).map(
                                            (classe) => AppBadge(
                                              text: classe.toTitleCase(),
                                              color: AppColors.primary,
                                            ),
                                          ),
                                      AppBadge(
                                        text: '+${dataset.classes.length - 2}',
                                        color: AppColors.secondary,
                                        tooltipText: dataset.classes
                                            .skip(2)
                                            .map((classe) => classe.toTitleCase())
                                            .join(', '),
                                      ),
                                    ],
                            ),
                          ),
                        ),
                        
                        SizedBox(height: isNarrow ? AppSpacing.xxSmall : AppSpacing.xSmall),
                        
                        const Divider(
                          color: AppColors.grey,
                          height: AppSpacing.xSmall,
                        ),
                        
                        SizedBox(height: isNarrow ? AppSpacing.xxSmall : AppSpacing.xSmall),
                        
                        // Informações adicionais (anotações e data)
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.sell_outlined,
                                  size: isNarrow ? 14 : 16,
                                  color: AppColors.grey,
                                ),
                                SizedBox(width: isNarrow ? AppSpacing.xxxSmall : AppSpacing.xxSmall),
                                Text(
                                  '${dataset.annotationsCount ?? 0} Anotações',
                                  style: AppTypography.labelMedium(context)
                                      .copyWith(
                                    color: descriptionColor,
                                    fontSize: isNarrow ? 11 : null,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ],
                            ),
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.access_time_outlined,
                                  size: isNarrow ? 14 : 16,
                                  color: AppColors.grey,
                                ),
                                SizedBox(width: isNarrow ? AppSpacing.xxxSmall : AppSpacing.xxxSmall),
                                Text(
                                  dataset.createdAt.timeAgo,
                                  style: AppTypography.labelMedium(context).copyWith(
                                    color: descriptionColor,
                                    fontSize: isNarrow ? 11 : null,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ],
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      }
    );
  }
}
