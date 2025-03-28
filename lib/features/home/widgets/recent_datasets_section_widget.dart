import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import '../widgets/recent_dataset_card.dart';

class RecentDatasetsSectionWidget extends StatelessWidget {
  final VoidCallback? onViewAllPressed;

  const RecentDatasetsSectionWidget({
    Key? key,
    this.onViewAllPressed,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final borderColor = ThemeColors.border(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Datasets Recentes',
          style: AppTypography.titleLarge(context),
        ),
        const SizedBox(height: AppSpacing.small),
        
        Container(
          decoration: BoxDecoration(
            color: ThemeColors.surface(context),
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
            border: Border.all(color: borderColor),
          ),
          child: Column(
            children: [
              // Lista de datasets recentes
              RecentDatasetCard(
                name: 'Contagem de Leveduras',
                imageCount: 245,
                progress: 0.8,
                timeAgo: '2 h atrás',
                lastModified: DateTime.now().subtract(const Duration(hours: 2)),
              ),
              Divider(color: borderColor, height: 1),
              RecentDatasetCard(
                name: 'Microplásticos em Amostras',
                imageCount: 124,
                progress: 0.6,
                timeAgo: '1 dia atrás',
                lastModified: DateTime.now().subtract(const Duration(days: 1)),
              ),
              Divider(color: borderColor, height: 1),
              RecentDatasetCard(
                name: 'Micróbios do Solo',
                imageCount: 89,
                progress: 0.4,
                timeAgo: '3 dias atrás',
                lastModified: DateTime.now().subtract(const Duration(days: 3)),
              ),
              
              // Botão para ver todos
              Padding(
                padding: const EdgeInsets.all(AppSpacing.small),
                child: Center(
                  child: TextButton(
                    onPressed: onViewAllPressed,
                    child: Text(
                      'Ver Todos',
                      style: AppTypography.labelMedium(context).copyWith(
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
} 