import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_borders.dart';

/// Card para exibir métricas no dashboard
class DashboardCard extends StatelessWidget {
  /// Ícone do card
  final IconData icon;
  
  /// Descrição da métrica
  final String label;
  
  /// Valor numérico da métrica
  final String value;
  
  /// Cor do ícone e valor
  final Color color;
  
  /// Cor de fundo personalizada (opcional)
  final Color? backgroundColor;
  
  /// Callback quando o card é pressionado
  final VoidCallback? onTap;

  const DashboardCard({
    Key? key,
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
    this.backgroundColor,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Detectar o tema atual
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    // Obter cores adaptativas baseadas no tema
    final cardBackgroundColor = backgroundColor ?? 
        (isDark ? AppColors.surfaceDark : AppColors.white);
    final textColor = isDark ? AppColors.white : AppColors.neutralDarkest;
    final borderColor = isDark ? AppColors.neutralDark : AppColors.neutralLight;
    
    return Card(
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
        side: BorderSide(color: borderColor, width: 1),
      ),
      elevation: 0,
      color: cardBackgroundColor,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.medium),
          child: Row(
            children: [
              // Ícone
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
                ),
                child: Icon(
                  icon,
                  color: color,
                  size: 24,
                ),
              ),
              const SizedBox(width: AppSpacing.medium),
              
              // Conteúdo principal
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Valor
                    Text(
                      value,
                      style: AppTypography.headlineSmall(context).copyWith(
                        color: color,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.xxSmall),
                    
                    // Descrição
                    Text(
                      label,
                      style: AppTypography.bodyMedium(context).copyWith(
                        color: textColor,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
} 