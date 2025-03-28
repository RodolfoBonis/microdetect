import 'package:flutter/material.dart';
import '../../../design_system/app_colors.dart';
import '../../../design_system/app_typography.dart';

class SettingsInputTile extends StatelessWidget {
  final String title;
  final String? subtitle;
  final String value;
  final Function(String) onChanged;
  final String? hintText;
  final IconData? icon;
  final IconData? trailingIcon;
  final VoidCallback? onTrailingIconPressed;
  final bool isEnabled;
  final TextInputType keyboardType;

  const SettingsInputTile({
    Key? key,
    required this.title,
    this.subtitle,
    required this.value,
    required this.onChanged,
    this.hintText,
    this.icon,
    this.trailingIcon,
    this.onTrailingIconPressed,
    this.isEnabled = true,
    this.keyboardType = TextInputType.text,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final titleColor = isDark ? AppColors.neutralLight : AppColors.neutralDark;
    final subtitleColor = isDark ? AppColors.neutralLight.withOpacity(0.7) : AppColors.neutralDark.withOpacity(0.7);
    final iconColor = isDark ? AppColors.primary.withOpacity(0.9) : AppColors.primary;
    final backgroundColor = isDark ? AppColors.surfaceDark.withOpacity(0.5) : AppColors.surfaceLight;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
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
          ],
        ),
        
        const SizedBox(height: 8.0),
        
        Container(
          decoration: BoxDecoration(
            color: backgroundColor,
            borderRadius: BorderRadius.circular(8.0),
            border: Border.all(
              color: isDark ? Colors.white12 : Colors.black12,
            ),
          ),
          child: Row(
            children: [
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12.0),
                  child: TextField(
                    controller: TextEditingController(text: value)..selection = TextSelection.collapsed(offset: value.length),
                    onChanged: onChanged,
                    enabled: isEnabled,
                    keyboardType: keyboardType,
                    style: AppTypography.textTheme.bodyMedium?.copyWith(
                      color: titleColor,
                    ),
                    decoration: InputDecoration(
                      hintText: hintText,
                      hintStyle: AppTypography.textTheme.bodyMedium?.copyWith(
                        color: subtitleColor,
                      ),
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(vertical: 12.0),
                    ),
                  ),
                ),
              ),
              
              if (trailingIcon != null)
                IconButton(
                  icon: Icon(
                    trailingIcon,
                    color: iconColor,
                    size: 20.0,
                  ),
                  onPressed: onTrailingIconPressed,
                ),
            ],
          ),
        ),
      ],
    );
  }
} 