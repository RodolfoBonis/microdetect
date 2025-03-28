import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import '../widgets/activity_card.dart';

class ActivitiesSectionWidget extends StatelessWidget {
  final VoidCallback? onViewMorePressed;

  const ActivitiesSectionWidget({
    Key? key,
    this.onViewMorePressed,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final borderColor = ThemeColors.border(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Atividades Recentes',
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
              // Lista de atividades recentes
              ActivityCard(
                icon: Icons.check_circle,
                iconColor: AppColors.success,
                title: 'Treinamento Concluído',
                description: 'O modelo "Detector v2" foi treinado com sucesso',
                timeAgo: '15 min',
                time: DateTime.now().subtract(const Duration(minutes: 15)),
              ),
              Divider(color: borderColor, height: 1),
              ActivityCard(
                icon: Icons.add_circle,
                iconColor: AppColors.primary,
                title: 'Novo Dataset Criado',
                description: 'Dataset "Microplásticos em Amostras" foi criado',
                timeAgo: '2 h',
                time: DateTime.now().subtract(const Duration(hours: 2)),
              ),
              Divider(color: borderColor, height: 1),
              ActivityCard(
                icon: Icons.photo_library,
                iconColor: AppColors.tertiary,
                title: 'Imagens Adicionadas',
                description: '23 novas imagens adicionadas ao dataset "Bactérias"',
                timeAgo: '5 h',
                time: DateTime.now().subtract(const Duration(hours: 5)),
              ),
              
              // Botão para ver mais
              Padding(
                padding: const EdgeInsets.all(AppSpacing.small),
                child: Center(
                  child: TextButton(
                    onPressed: onViewMorePressed,
                    child: Text(
                      'Ver Mais',
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