import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:intl/intl.dart';

/// Card para exibição de atividades recentes
class ActivityCard extends StatelessWidget {
  /// Título da atividade
  final String title;
  
  /// Descrição da atividade
  final String description;
  
  /// Data/hora da atividade
  final DateTime time;
  
  /// Ícone representando o tipo de atividade
  final IconData icon;
  
  /// Cor do ícone
  final Color iconColor;
  
  /// Tempo decorrido (texto formatado)
  final String timeAgo;
  
  /// Cor de fundo personalizada (opcional)
  final Color? backgroundColor;
  
  /// Função chamada ao clicar no card
  final VoidCallback? onTap;

  const ActivityCard({
    Key? key,
    required this.title,
    required this.description,
    required this.time,
    required this.icon,
    required this.iconColor,
    required this.timeAgo,
    this.backgroundColor,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Verificar o tema atual
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    // Definir as cores baseadas no tema
    final textColor = ThemeColors.text(context);
    final secondaryTextColor = ThemeColors.textSecondary(context);
    final cardColor = backgroundColor ?? ThemeColors.surface(context);
    
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.medium),
        color: cardColor,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Ícone
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: iconColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                icon,
                color: iconColor,
                size: 16,
              ),
            ),
            
            const SizedBox(width: AppSpacing.small),
            
            // Conteúdo
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Título e tempo
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          title,
                          style: AppTypography.titleSmall(context).copyWith(
                            color: textColor,
                            fontWeight: FontWeight.w500,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.small),
                      Text(
                        timeAgo,
                        style: AppTypography.bodySmall(context).copyWith(
                          color: secondaryTextColor,
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 4),
                  
                  // Descrição
                  Text(
                    description,
                    style: AppTypography.bodySmall(context).copyWith(
                      color: secondaryTextColor,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Formata a hora para exibição
  String _formatTime(DateTime time) {
    final now = DateTime.now();
    final difference = now.difference(time);
    
    if (difference.inMinutes < 60) {
      return '${difference.inMinutes} min';
    } else if (difference.inHours < 24) {
      return '${difference.inHours} h';
    } else if (difference.inDays < 30) {
      return '${difference.inDays} d';
    } else {
      return DateFormat('dd/MM').format(time);
    }
  }
} 