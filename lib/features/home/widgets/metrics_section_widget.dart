import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import '../widgets/dashboard_card.dart';

class MetricsSectionWidget extends StatelessWidget {
  const MetricsSectionWidget({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        // Datasets
        Expanded(
          child: DashboardCard(
            icon: Icons.folder,
            label: 'Datasets',
            value: '12',
            color: AppColors.primary,
          ),
        ),
        const SizedBox(width: AppSpacing.medium),
        
        // Modelos treinados
        Expanded(
          child: DashboardCard(
            icon: Icons.model_training,
            label: 'Modelos Treinados',
            value: '5',
            color: AppColors.secondary,
          ),
        ),
        const SizedBox(width: AppSpacing.medium),
        
        // Imagens analisadas
        Expanded(
          child: DashboardCard(
            icon: Icons.image,
            label: 'Imagens Analisadas',
            value: '1,245',
            color: AppColors.tertiary,
          ),
        ),
        const SizedBox(width: AppSpacing.medium),
        
        // Microorganismos
        Expanded(
          child: DashboardCard(
            icon: Icons.bug_report,
            label: 'Microorganismos',
            value: '32',
            color: AppColors.info,
          ),
        ),
      ],
    );
  }
} 