import 'package:flutter/material.dart';
import '../../../design_system/app_colors.dart';
import '../../../design_system/app_typography.dart';

class SettingsButtonTile extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Future<void> Function()? onPressed;
  final IconData? icon;
  final IconData? trailingIcon;
  final bool isLoading;
  final bool isDestructive;

  const SettingsButtonTile({
    Key? key,
    required this.title,
    this.subtitle,
    required this.onPressed,
    this.icon,
    this.trailingIcon = Icons.chevron_right,
    this.isLoading = false,
    this.isDestructive = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final titleColor = isDestructive
        ? AppColors.error
        : (isDark ? AppColors.neutralLight : AppColors.neutralDark);
    final subtitleColor = isDark 
        ? AppColors.neutralLight.withOpacity(0.7) 
        : AppColors.neutralDark.withOpacity(0.7);
    final iconColor = isDestructive
        ? AppColors.error
        : (isDark ? AppColors.primary.withOpacity(0.9) : AppColors.primary);
    
    return InkWell(
      onTap: isLoading ? null : onPressed,
      child: Row(
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
          
          isLoading
              ? SizedBox(
                  width: 24.0,
                  height: 24.0,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.0,
                    valueColor: AlwaysStoppedAnimation<Color>(
                        isDestructive ? AppColors.error : AppColors.primary),
                  ),
                )
              : (trailingIcon != null
                  ? Icon(
                      trailingIcon,
                      color: isDark ? AppColors.neutralLight.withOpacity(0.5) : AppColors.neutralDark.withOpacity(0.5),
                      size: 20.0,
                    )
                  : const SizedBox.shrink()),
        ],
      ),
    );
  }
} 