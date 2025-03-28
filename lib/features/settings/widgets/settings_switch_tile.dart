import 'package:flutter/material.dart';
import '../../../design_system/app_colors.dart';
import '../../../design_system/app_typography.dart';

class SettingsSwitchTile extends StatelessWidget {
  final String title;
  final String? subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;
  final IconData? icon;

  const SettingsSwitchTile({
    Key? key,
    required this.title,
    this.subtitle,
    required this.value,
    required this.onChanged,
    this.icon,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final titleColor = isDark ? AppColors.neutralLight : AppColors.neutralDark;
    final subtitleColor = isDark ? AppColors.neutralLight.withOpacity(0.7) : AppColors.neutralDark.withOpacity(0.7);
    final iconColor = isDark ? AppColors.primary.withOpacity(0.9) : AppColors.primary;
    
    return Row(
      children: [
        if (icon != null) ...[
          Icon(
            icon,
            color: iconColor,
            size: 24.0,
          ),
          const SizedBox(width: 16.0),
        ],
        
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: AppTypography.textTheme.bodyLarge?.copyWith(
                  color: titleColor,
                ),
              ),
              if (subtitle != null) ...[
                const SizedBox(height: 4.0),
                Text(
                  subtitle!,
                  style: AppTypography.textTheme.bodySmall?.copyWith(
                    color: subtitleColor,
                  ),
                ),
              ],
            ],
          ),
        ),
        
        Switch(
          value: value,
          onChanged: onChanged,
          activeColor: AppColors.primary,
        ),
      ],
    );
  }
} 