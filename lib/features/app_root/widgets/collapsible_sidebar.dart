import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/routes/app_pages.dart';

/// Menu lateral colapsável para a navegação principal
class CollapsibleSidebar extends StatelessWidget {
  /// Se o menu está expandido
  final bool isExpanded;
  
  /// Callback quando o estado expandido/colapsado muda
  final ValueChanged<bool> onExpandedChanged;
  
  /// Rota atual selecionada
  final String selectedRoute;
  
  /// Callback quando uma rota é selecionada
  final ValueChanged<String> onRouteSelected;

  const CollapsibleSidebar({
    Key? key,
    required this.isExpanded,
    required this.onExpandedChanged,
    required this.selectedRoute,
    required this.onRouteSelected,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Obter o tema atual
    final isDarkMode = Theme.of(context).brightness == Brightness.dark;
    
    // Adaptar cores para o tema atual
    final backgroundColor = isDarkMode ? AppColors.surfaceDark : AppColors.white;
    final shadowColor = isDarkMode ? Colors.black.withValues(alpha: 0.3) : Colors.black.withValues(alpha: 0.1);
    final iconColor = isDarkMode ? AppColors.white : AppColors.primary;
    final textColor = isDarkMode ? AppColors.white : AppColors.neutralDarkest;
    final dividerColor = isDarkMode ? AppColors.neutralDark : AppColors.neutralLight;
    
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      width: isExpanded ? 240 : 72,
      decoration: BoxDecoration(
        color: backgroundColor,
        boxShadow: [
          BoxShadow(
            color: shadowColor,
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          _buildHeader(AppColors.primary, textColor, isDarkMode),
          Divider(height: 1, thickness: 1, color: dividerColor),
          Expanded(
            child: _buildNavigation(iconColor, textColor, isDarkMode),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(Color iconColor, Color textColor, bool isDarkMode) {
    return Padding(
      padding: EdgeInsets.symmetric(
        horizontal: isExpanded ? AppSpacing.medium : AppSpacing.small,
        vertical: AppSpacing.medium,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.start,
        mainAxisSize: MainAxisSize.min, // Take only needed space
        children: [
          Icon(
            Icons.biotech,
            size: isExpanded ? 32 : 24, // Smaller icon when collapsed
            color: iconColor,
          ),
          if (isExpanded) ...[
            const SizedBox(width: AppSpacing.small),
            Expanded(  // Prevent text overflow
              child: Text(
                'MicroDetect',
                overflow: TextOverflow.ellipsis,
                style: AppTypography.textTheme.titleLarge?.copyWith(
                  color: textColor,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ]
        ],
      ),
    );
  }

  Widget _buildNavigation(Color iconColor, Color textColor, bool isDarkMode) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Main navigation items that can scroll
        Expanded(
          child: ListView(
            padding: EdgeInsets.symmetric(
              vertical: AppSpacing.small,
              horizontal: isExpanded ? AppSpacing.xSmall : 0,
            ),
            children: [
              _buildNavItem(
                icon: Icons.home,
                label: 'Início',
                route: AppRoutes.home,
                iconColor: iconColor,
                textColor: textColor,
                isDarkMode: isDarkMode,
              ),
              _buildNavItem(
                icon: Icons.folder,
                label: 'Datasets',
                route: AppRoutes.datasets,
                iconColor: iconColor,
                textColor: textColor,
                isDarkMode: isDarkMode,
              ),
              _buildNavItem(
                icon: Icons.edit,
                label: 'Anotação',
                route: AppRoutes.annotations,
                iconColor: iconColor,
                textColor: textColor,
                isDarkMode: isDarkMode,
              ),
              _buildNavItem(
                icon: Icons.fitness_center,
                label: 'Treinamento',
                route: AppRoutes.training,
                iconColor: iconColor,
                textColor: textColor,
                isDarkMode: isDarkMode,
              ),
              _buildNavItem(
                icon: Icons.insights,
                label: 'Inferência',
                route: AppRoutes.inference,
                iconColor: iconColor,
                textColor: textColor,
                isDarkMode: isDarkMode,
              ),
              _buildNavItem(
                icon: Icons.analytics,
                label: 'Análise',
                route: AppRoutes.analysis,
                iconColor: iconColor,
                textColor: textColor,
                isDarkMode: isDarkMode,
              ),
              _buildNavItem(
                icon: Icons.camera_alt,
                label: 'Câmera',
                route: AppRoutes.camera,
                iconColor: iconColor,
                textColor: textColor,
                isDarkMode: isDarkMode,
              ),
            ],
          ),
        ),

        // Fixed bottom section
        Padding(
          padding: EdgeInsets.symmetric(
            horizontal: isExpanded ? AppSpacing.xSmall : 0,
          ),
          child: Column(
            children: [
              Divider(
                height: 1,
                thickness: 1,
                color: isDarkMode ? AppColors.neutralDark : AppColors.neutralLight,
                indent: 8,
                endIndent: 8,
              ),
              const SizedBox(height: AppSpacing.small),
              _buildNavItem(
                icon: Icons.settings,
                label: 'Configurações',
                route: AppRoutes.settings,
                iconColor: iconColor,
                textColor: textColor,
                isDarkMode: isDarkMode,
              ),
              _buildNavItem(
                icon: isExpanded ? Icons.arrow_back_ios_rounded : Icons.arrow_forward_ios_rounded,
                label: 'Recolher',
                route: '',
                iconColor: iconColor,
                textColor: textColor,
                isDarkMode: isDarkMode,
                onTap: () => onExpandedChanged(!isExpanded),
              ),
              const SizedBox(height: AppSpacing.small), // Bottom padding
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildNavItem({
    required IconData icon,
    required String label,
    required String route,
    required Color iconColor,
    required Color textColor,
    required bool isDarkMode,
    VoidCallback? onTap,
  }) {
    // Verificar se a rota atual corresponde à rota deste item
    final bool isSelected = _isRouteSelected(selectedRoute, route);
    const selectedColor = AppColors.primary;
    final selectedBgColor = isDarkMode
        ? AppColors.primary.withValues(alpha: 0.2)
        : AppColors.primary.withValues(alpha: 0.1);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: InkWell(
        onTap: onTap ?? () => onRouteSelected(route),
        borderRadius: BorderRadius.circular(8),
        child: Container(
          width: double.infinity,
          decoration: BoxDecoration(
            color: isSelected ? selectedBgColor : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
          ),
          padding: EdgeInsets.symmetric(
            horizontal: isExpanded ? AppSpacing.small : AppSpacing.xxSmall,
            vertical: AppSpacing.small,
          ),
          child: Row(
            mainAxisAlignment: isExpanded ? MainAxisAlignment.start : MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                color: isSelected ? selectedColor : iconColor,
                size: 20,
              ),
              if (isExpanded) ...[
                const SizedBox(width: AppSpacing.small),
                Expanded(
                  child: Text(
                    label,
                    style: AppTypography.textTheme.bodyLarge?.copyWith(
                      color: isSelected ? selectedColor : textColor,
                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
  
  // Verifica se uma rota está selecionada, considerando rotas aninhadas
  bool _isRouteSelected(String currentRoute, String route) {
    // Casos especiais para botões que não são rotas
    if (route.isEmpty) return false;
    
    // Correspondência exata
    if (currentRoute == route) return true;
    
    // Verificar se a rota atual é uma rota filha
    if (route == '/home' && currentRoute.endsWith('/home')) return true;
    if (route == '/settings' && currentRoute.endsWith('/settings')) return true;
    if (route == '/datasets' && currentRoute.endsWith('/datasets')) return true;
    if (route == '/camera' && currentRoute.endsWith('/camera')) return true;
    if (route == '/annotation' && currentRoute.endsWith('/annotation')) return true;
    if (route == '/training' && currentRoute.endsWith('/training')) return true;
    if (route == '/inference' && currentRoute.endsWith('/inference')) return true;
    if (route == '/analysis' && currentRoute.endsWith('/analysis')) return true;
    
    return false;
  }
} 