import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:intl/intl.dart';

/// Card para exibição de datasets recentes
class RecentDatasetCard extends StatelessWidget {
  /// Nome do dataset
  final String name;
  
  /// Número de imagens no dataset
  final int imageCount;
  
  /// Data da última modificação
  final DateTime lastModified;
  
  /// Progresso de anotação (0.0 a 1.0)
  final double progress;
  
  /// Tempo decorrido desde a modificação
  final String timeAgo;
  
  /// Cor de fundo personalizada (opcional)
  final Color? backgroundColor;
  
  /// Função chamada ao clicar no card
  final VoidCallback? onTap;

  const RecentDatasetCard({
    Key? key,
    required this.name,
    required this.imageCount,
    required this.lastModified,
    required this.progress,
    required this.timeAgo,
    this.backgroundColor,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Determinar o tema atual
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    // Definir as cores do texto com base no tema
    final textColor = ThemeColors.text(context);
    final secondaryTextColor = ThemeColors.textSecondary(context);
    final cardColor = backgroundColor ?? ThemeColors.surface(context);
    
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: AppSpacing.paddingMedium,
        color: cardColor,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Nome do dataset e ícone
            Row(
              children: [
                Icon(
                  Icons.folder,
                  color: AppColors.primary,
                  size: 20,
                ),
                SizedBox(width: AppSpacing.small),
                Expanded(
                  child: Text(
                    name,
                    style: AppTypography.bodyLarge(context).copyWith(
                      color: textColor,
                      fontWeight: FontWeight.w600,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Icon(
                  Icons.arrow_forward_ios,
                  color: secondaryTextColor,
                  size: 14,
                ),
              ],
            ),
            
            SizedBox(height: AppSpacing.small),
            
            // Informações do dataset
            Row(
              children: [
                // Contagem de imagens
                Expanded(
                  child: Row(
                    children: [
                      Icon(
                        Icons.image_outlined,
                        color: secondaryTextColor,
                        size: 14,
                      ),
                      SizedBox(width: 4),
                      Text(
                        '$imageCount imagens',
                        style: AppTypography.bodySmall(context).copyWith(
                          color: secondaryTextColor,
                        ),
                      ),
                    ],
                  ),
                ),
                
                // Data da última modificação
                Expanded(
                  child: Row(
                    children: [
                      Icon(
                        Icons.access_time,
                        color: secondaryTextColor,
                        size: 14,
                      ),
                      SizedBox(width: 4),
                      Text(
                        timeAgo,
                        style: AppTypography.bodySmall(context).copyWith(
                          color: secondaryTextColor,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            
            SizedBox(height: AppSpacing.small),
            
            // Barra de progresso
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Progresso',
                      style: AppTypography.bodySmall(context).copyWith(
                        color: secondaryTextColor,
                      ),
                    ),
                    Text(
                      _getProgressText(),
                      style: AppTypography.bodySmall(context).copyWith(
                        color: _getProgressColor(),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
                  child: LinearProgressIndicator(
                    value: progress,
                    backgroundColor: isDark ? AppColors.neutralDark : AppColors.neutralLight,
                    valueColor: AlwaysStoppedAnimation<Color>(_getProgressColor()),
                    minHeight: 4,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// Formata a data para exibição
  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);
    
    if (difference.inMinutes < 60) {
      return '${difference.inMinutes} min atrás';
    } else if (difference.inHours < 24) {
      return '${difference.inHours} h atrás';
    } else if (difference.inDays < 30) {
      return '${difference.inDays} dias atrás';
    } else {
      return DateFormat('dd/MM/yyyy').format(date);
    }
  }

  /// Retorna a cor adequada para o progresso
  Color _getProgressColor() {
    if (progress < 0.3) {
      return AppColors.error;
    } else if (progress < 0.7) {
      return AppColors.warning;
    } else {
      return AppColors.success;
    }
  }

  /// Formata a porcentagem de progresso
  String _getProgressText() {
    return '${(progress * 100).toInt()}%';
  }
} 