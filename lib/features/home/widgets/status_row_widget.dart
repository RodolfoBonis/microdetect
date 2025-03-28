import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';

class StatusRowWidget extends StatelessWidget {
  final String label;
  final String value;
  final IconData statusIcon;
  final Color statusColor;
  final String statusText;

  const StatusRowWidget({
    Key? key,
    required this.label,
    required this.value,
    required this.statusIcon,
    required this.statusColor,
    required this.statusText,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final labelColor = ThemeColors.textSecondary(context);
    final valueColor = ThemeColors.text(context);
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.xSmall),
      child: Row(
        children: [
          // Label
          SizedBox(
            width: 150,
            child: Text(
              label,
              style: AppTypography.bodyMedium(context).copyWith(
                color: labelColor,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          
          // Valor
          Expanded(
            child: Text(
              value,
              style: AppTypography.bodyMedium(context).copyWith(
                color: valueColor,
              ),
            ),
          ),
          
          // Status
          Row(
            children: [
              Icon(statusIcon, color: statusColor, size: 16),
              const SizedBox(width: 4),
              Text(
                statusText,
                style: AppTypography.bodySmall(context).copyWith(
                  color: statusColor,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
} 