// lib/features/backend_monitor/widgets/check_item_widget.dart
import 'package:flutter/material.dart';
import '../../../core/enums/backend_status_enum.dart';
import '../../../design_system/app_colors.dart';
import '../../../design_system/app_typography.dart';

class CheckItemWidget extends StatelessWidget {
  final String title;
  final CheckStatus status;

  const CheckItemWidget({
    required this.title,
    required this.status,
    Key? key,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    IconData icon;
    Color color;

    switch (status) {
      case CheckStatus.completed:
        icon = Icons.check_circle;
        color = AppColors.success;
        break;
      case CheckStatus.error:
        icon = Icons.error;
        color = AppColors.error;
        break;
      case CheckStatus.inProgress:
        icon = Icons.hourglass_empty;
        color = AppColors.warning;
        break;
      case CheckStatus.pending:
        icon = Icons.circle_outlined;
        color = AppColors.lightGrey;
        break;
    }

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(
            icon,
            size: 24,
            color: color,
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Text(
              title,
              style: AppTypography.textTheme.bodyLarge?.copyWith(
                color: color,
              ),
            ),
          ),
        ],
      ),
    );
  }
}