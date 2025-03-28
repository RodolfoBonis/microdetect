import 'package:flutter/material.dart';
import '../../../design_system/app_colors.dart';
import '../../../design_system/app_typography.dart';
import '../../../design_system/app_spacing.dart';

class SettingsSection extends StatelessWidget {
  final String title;
  final List<Widget> children;
  final EdgeInsets padding;
  final bool hasTopDivider;

  const SettingsSection({
    Key? key,
    required this.title,
    required this.children,
    this.padding = const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
    this.hasTopDivider = true,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final titleColor = isDark ? AppColors.neutralLight : AppColors.neutralDark;
    final backgroundColor = isDark ? AppColors.surfaceDark : AppColors.surfaceLight;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (hasTopDivider) 
          const Divider(height: 1),
        
        Padding(
          padding: EdgeInsets.only(
            left: 16.0, 
            right: 16.0, 
            top: 16.0, 
            bottom: 8.0
          ),
          child: Text(
            title,
            style: AppTypography.textTheme.titleMedium?.copyWith(
              color: titleColor,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        
        Container(
          margin: const EdgeInsets.symmetric(horizontal: 16.0),
          decoration: BoxDecoration(
            color: backgroundColor,
            borderRadius: BorderRadius.circular(8.0),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 2.0,
                offset: const Offset(0, 1),
              ),
            ],
          ),
          child: Column(
            children: children.map((child) {
              final index = children.indexOf(child);
              final isLast = index == children.length - 1;
              
              return Column(
                children: [
                  Padding(
                    padding: padding,
                    child: child,
                  ),
                  if (!isLast)
                    const Divider(height: 1, indent: 16.0, endIndent: 16.0),
                ],
              );
            }).toList(),
          ),
        ),
        
        const SizedBox(height: 24.0),
      ],
    );
  }
} 