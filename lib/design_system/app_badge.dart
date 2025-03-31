import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';

class AppBadge extends StatelessWidget {
  final String text;
  final Color? color;
  final Color? textColor;
  final String? tooltipText;
  final IconData? prefixIcon;
  final double radius;

  const AppBadge({
    super.key,
    required this.text,
    this.color = AppColors.grey,
    this.textColor,
    this.tooltipText,
    this.prefixIcon,
    this.radius = AppSpacing.small,
  });

  @override
  Widget build(BuildContext context) {
    final badge = Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(radius),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (prefixIcon != null)
            Padding(
              padding: const EdgeInsets.only(
                right: AppSpacing.xxSmall,
              ),
              child: Icon(
                prefixIcon,
                size: 16,
                color: textColor ?? AppColors.white,
              ),
            ),
          Text(
            text,
            style: AppTypography.labelMedium(context).copyWith(
              color: textColor ?? AppColors.white,
            ),
          ),
        ],
      ),
    );

    // Only wrap with tooltip if tooltipText is provided and not empty
    if (tooltipText != null && tooltipText!.isNotEmpty) {
      return Tooltip(
        message: tooltipText!,
        child: badge,
      );
    }

    return badge;
  }
}
