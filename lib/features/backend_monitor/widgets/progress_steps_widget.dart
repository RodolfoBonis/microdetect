import 'package:flutter/material.dart';
import 'package:microdetect/core/enums/backend_status_enum.dart';
import 'package:microdetect/core/models/check_item_model.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';

class ProgressStepsWidget extends StatelessWidget {
  final List<CheckItem> checkItems;
  final bool active;

  const ProgressStepsWidget({
    Key? key,
    required this.checkItems,
    this.active = true,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: ThemeColors.border(context)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.medium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Progresso de Inicialização',
                  style: AppTypography.titleMedium(context),
                ),
                if (active)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.small,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.info.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const SizedBox(
                          width: 12,
                          height: 12,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(
                              AppColors.info,
                            ),
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          'Em progresso',
                          style: AppTypography.labelSmall(context).copyWith(
                            color: AppColors.info,
                          ),
                        ),
                      ],
                    ),
                  )
                else
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.small,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.success.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.check_circle,
                          size: 12,
                          color: AppColors.success,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          'Concluído',
                          style: AppTypography.labelSmall(context).copyWith(
                            color: AppColors.success,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
            const SizedBox(height: AppSpacing.medium),
            LayoutBuilder(
              builder: (context, constraints) {
                return SizedBox(
                  width: constraints.maxWidth,
                  child: _buildStepsList(context),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStepsList(BuildContext context) {
    return Column(
      children: checkItems.asMap().entries.map((entry) {
        final index = entry.key;
        final item = entry.value;
        
        // Determinar se é o último item
        final isLastItem = index == checkItems.length - 1;
        
        return Column(
          children: [
            _buildCheckItem(context, item, isLastItem),
            // Adicionando um pequeno espaçamento entre itens para manter a separação visual
            if (!isLastItem)
              const SizedBox(height: 8),
          ],
        );
      }).toList(),
    );
  }

  Widget _buildCheckItem(BuildContext context, CheckItem item, bool isLastItem) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 24,
          height: 24,
          decoration: BoxDecoration(
            color: _getStepColor(item.status).withValues(
              alpha: item.status == CheckStatus.pending ? 0.2 : 0.9,
            ),
            shape: BoxShape.circle,
          ),
          child: Center(
            child: _getStepIcon(item.status),
          ),
        ),
        const SizedBox(width: AppSpacing.small),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.title,
                  style: AppTypography.bodyMedium(context).copyWith(
                    fontWeight: FontWeight.w500,
                    color: item.status == CheckStatus.pending
                        ? ThemeColors.textSecondary(context)
                        : ThemeColors.text(context),
                  ),
                ),
                if (item.status == CheckStatus.inProgress) ...[
                  const SizedBox(height: 4),
                  LinearProgressIndicator(
                    backgroundColor: AppColors.info.withOpacity(0.2),
                    valueColor: const AlwaysStoppedAnimation<Color>(AppColors.info),
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _getStepIcon(CheckStatus status) {
    switch (status) {
      case CheckStatus.completed:
        return Icon(
          Icons.check,
          color: Colors.white,
          size: 16,
        );
      case CheckStatus.inProgress:
        return SizedBox(
          width: 12,
          height: 12,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
          ),
        );
      case CheckStatus.error:
        return Icon(
          Icons.close,
          color: Colors.white,
          size: 16,
        );
      case CheckStatus.pending:
      default:
        return Icon(
          Icons.circle,
          color: AppColors.neutralLight.withOpacity(0.5),
          size: 8,
        );
    }
  }

  Color _getStepColor(CheckStatus status) {
    switch (status) {
      case CheckStatus.completed:
        return AppColors.success;
      case CheckStatus.inProgress:
        return AppColors.info;
      case CheckStatus.error:
        return AppColors.error;
      case CheckStatus.pending:
      default:
        return AppColors.neutralLight;
    }
  }
} 