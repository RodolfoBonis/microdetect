import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/models/system_status_model.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'status_row_widget.dart';

class SystemStatusSectionWidget extends StatelessWidget {
  final SystemStatusModel systemStatus;

  const SystemStatusSectionWidget({
    Key? key,
    required this.systemStatus,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final borderColor = ThemeColors.border(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Status do Sistema',
          style: AppTypography.titleLarge(context),
        ),
        const SizedBox(height: AppSpacing.small),
        
        Container(
          decoration: BoxDecoration(
            color: ThemeColors.surface(context),
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
            border: Border.all(color: borderColor),
          ),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.medium),
            child: Column(
              children: [
                // Linha de status de GPU
                StatusRowWidget(
                  label: 'GPU',
                  value: '${systemStatus.gpu.model} (${systemStatus.gpu.memory})',
                  statusIcon: systemStatus.gpu.available ? Icons.check_circle : Icons.error,
                  statusColor: systemStatus.gpu.available ? AppColors.success : AppColors.error,
                  statusText: systemStatus.gpu.available ? 'Disponível' : 'Indisponível',
                ),
                
                // Linha de status de armazenamento
                StatusRowWidget(
                  label: 'Armazenamento',
                  value: '${systemStatus.storage.used} / ${systemStatus.storage.total}',
                  statusIcon: Icons.check_circle,
                  statusColor: AppColors.success,
                  statusText: '${systemStatus.storage.percentage}% utilizado',
                ),
                
                // Linha de status do servidor Python
                StatusRowWidget(
                  label: 'Servidor Python',
                  value: systemStatus.server.version,
                  statusIcon: systemStatus.server.active ? Icons.check_circle : Icons.error,
                  statusColor: systemStatus.server.active ? AppColors.success : AppColors.error,
                  statusText: systemStatus.server.active ? 'Ativo' : 'Inativo',
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
} 