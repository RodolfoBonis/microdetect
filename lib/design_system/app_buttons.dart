import 'package:flutter/material.dart';
import 'app_colors.dart';
import 'app_borders.dart';
import 'app_spacing.dart';
import 'app_typography.dart';

/// Tipo de botão
enum AppButtonType {
  /// Botão primário com cor de destaque
  primary,
  
  /// Botão secundário com borda e sem preenchimento
  secondary,
  
  /// Botão terciário com aparência mínima
  tertiary,

  /// Botão de sucesso com cor verde
  success,
}

/// Tamanho de botão
enum AppButtonSize {
  /// Botão pequeno
  small,
  
  /// Botão médio (padrão)
  medium,
  
  /// Botão grande
  large,
}

/// Botão padrão da aplicação
class AppButton extends StatelessWidget {
  /// Texto do botão
  final String label;

  /// Função chamada ao pressionar o botão
  final VoidCallback? onPressed;

  /// Indica se o botão está em estado de carregamento
  final bool isLoading;

  /// Indica se o botão deve ocupar a largura total
  final bool isFullWidth;

  /// Tipo do botão
  final AppButtonType type;

  /// Tamanho do botão
  final AppButtonSize size;

  /// Ícone exibido antes do texto
  final IconData? prefixIcon;

  /// Ícone exibido depois do texto
  final IconData? suffixIcon;

  /// Construtor padrão
  const AppButton({
    Key? key,
    required this.label,
    this.onPressed,
    this.isLoading = false,
    this.isFullWidth = false,
    this.type = AppButtonType.primary,
    this.size = AppButtonSize.medium,
    this.prefixIcon,
    this.suffixIcon,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Verificar o tema atual
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    // Determinar as cores com base no tipo e tema
    final Color backgroundColor = _getBackgroundColor(context);
    final Color textColor = _getTextColor(context);

    // Determinar o padding com base no tamanho
    final EdgeInsets padding = _getPadding();

    // Determinar altura com base no tamanho
    final double height = _getHeight();

    // Determinar estilo de texto com base no tamanho
    final TextStyle textStyle = _getTextStyle(context);

    // Construir o botão com base no tipo
    return SizedBox(
      width: isFullWidth ? double.infinity : null,
      height: height,
      child: _buildButton(
        context: context,
        backgroundColor: backgroundColor,
        textColor: textColor,
        padding: padding,
        textStyle: textStyle,
      ),
    );
  }

  /// Constrói o botão correto com base no tipo
  Widget _buildButton({
    required BuildContext context,
    required Color backgroundColor,
    required Color textColor,
    required EdgeInsets padding,
    required TextStyle textStyle,
  }) {
    // Verificar o tema atual
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    // Cor do botão desabilitado
    final disabledBackgroundColor = isDark 
        ? AppColors.neutralDark 
        : AppColors.neutralLight;
    
    final disabledForegroundColor = isDark 
        ? AppColors.neutralLight 
        : AppColors.neutralDark;
    
    // Conteúdo interno do botão
    final Widget content = _buildButtonContent(context, textColor, textStyle);

    switch (type) {
      case AppButtonType.primary:
        return ElevatedButton(
          onPressed: isLoading ? null : onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: backgroundColor,
            foregroundColor: textColor,
            disabledBackgroundColor: disabledBackgroundColor,
            disabledForegroundColor: disabledForegroundColor,
            elevation: 0,
            padding: padding,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
            ),
            textStyle: textStyle.copyWith(inherit: true),
          ),
          child: content,
        );

      case AppButtonType.secondary:
        final borderColor = isDark 
            ? AppColors.primary 
            : AppColors.primary;
            
        final disabledBorderColor = isDark 
            ? AppColors.neutralDark 
            : AppColors.neutralLight;
            
        return OutlinedButton(
          onPressed: isLoading ? null : onPressed,
          style: OutlinedButton.styleFrom(
            foregroundColor: textColor,
            padding: padding,
            side: BorderSide(
              color: onPressed == null ? disabledBorderColor : borderColor,
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
            ),
            textStyle: textStyle.copyWith(inherit: true),
          ),
          child: content,
        );

      case AppButtonType.tertiary:
        return TextButton(
          onPressed: isLoading ? null : onPressed,
          style: TextButton.styleFrom(
            foregroundColor: textColor,
            padding: padding,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
            ),
            textStyle: textStyle.copyWith(inherit: true),
          ),
          child: content,
        );
        
      case AppButtonType.success:
        return ElevatedButton(
          onPressed: isLoading ? null : onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: backgroundColor,
            foregroundColor: textColor,
            disabledBackgroundColor: disabledBackgroundColor,
            disabledForegroundColor: disabledForegroundColor,
            elevation: 0,
            padding: padding,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
            ),
            textStyle: textStyle.copyWith(inherit: true),
          ),
          child: content,
        );
    }
  }

  /// Constrói o conteúdo interno do botão (ícone + texto + spinner)
  Widget _buildButtonContent(BuildContext context, Color textColor, TextStyle textStyle) {
    if (isLoading) {
      return Center(
        child: SizedBox(
          width: _getLoaderSize(),
          height: _getLoaderSize(),
          child: CircularProgressIndicator(
            strokeWidth: 2.5,
            valueColor: AlwaysStoppedAnimation<Color>(textColor),
          ),
        ),
      );
    }

    final List<Widget> children = [];

    if (prefixIcon != null) {
      children.add(Icon(prefixIcon, size: _getIconSize()));
      children.add(SizedBox(width: AppSpacing.xSmall));
    }

    // Garantir que o estilo de texto mantenha o inherit consistente
    final TextStyle safeTextStyle = textStyle.copyWith(inherit: true);
    children.add(Text(label, style: safeTextStyle));

    if (suffixIcon != null) {
      children.add(SizedBox(width: AppSpacing.xSmall));
      children.add(Icon(suffixIcon, size: _getIconSize()));
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: children,
    );
  }

  /// Retorna a cor de fundo com base no tipo
  Color _getBackgroundColor(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    if (onPressed == null) {
      return isDark ? AppColors.neutralDark : AppColors.lightGrey;
    }

    switch (type) {
      case AppButtonType.primary:
        return AppColors.primary;
      case AppButtonType.secondary:
        return Colors.transparent;
      case AppButtonType.tertiary:
        return Colors.transparent;
      case AppButtonType.success:
        return AppColors.success;
    }
  }

  /// Retorna a cor do texto com base no tipo
  Color _getTextColor(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    if (onPressed == null) {
      return isDark ? AppColors.neutralLight : AppColors.grey;
    }

    switch (type) {
      case AppButtonType.primary:
        return Colors.white;
      case AppButtonType.secondary:
        return AppColors.primary;
      case AppButtonType.tertiary:
        return AppColors.primary;
      case AppButtonType.success:
        return Colors.white;
    }
  }

  /// Retorna o padding com base no tamanho
  EdgeInsets _getPadding() {
    switch (size) {
      case AppButtonSize.small:
        return const EdgeInsets.symmetric(horizontal: 16, vertical: 8);
      case AppButtonSize.medium:
        return const EdgeInsets.symmetric(horizontal: 24, vertical: 12);
      case AppButtonSize.large:
        return const EdgeInsets.symmetric(horizontal: 32, vertical: 16);
    }
  }

  /// Retorna a altura do botão com base no tamanho
  double _getHeight() {
    switch (size) {
      case AppButtonSize.small:
        return 36;
      case AppButtonSize.medium:
        return 48;
      case AppButtonSize.large:
        return 56;
    }
  }

  /// Retorna o estilo de texto com base no tamanho
  TextStyle _getTextStyle(BuildContext context) {
    switch (size) {
      case AppButtonSize.small:
        return AppTypography.labelSmall(context).copyWith(inherit: true);
      case AppButtonSize.medium:
        return AppTypography.labelLarge(context).copyWith(inherit: true);
      case AppButtonSize.large:
        return AppTypography.labelLarge(context).copyWith(
          fontSize: 16,
          letterSpacing: 0.5,
          inherit: true,
        );
    }
  }

  /// Retorna o tamanho do indicador de carregamento
  double _getLoaderSize() {
    switch (size) {
      case AppButtonSize.small:
        return 16;
      case AppButtonSize.medium:
        return 20;
      case AppButtonSize.large:
        return 24;
    }
  }

  /// Retorna o tamanho dos ícones
  double _getIconSize() {
    switch (size) {
      case AppButtonSize.small:
        return 16;
      case AppButtonSize.medium:
        return 20;
      case AppButtonSize.large:
        return 24;
    }
  }
}

/// Botão de ícone para a aplicação
class AppIconButton extends StatelessWidget {
  /// Ícone exibido no botão
  final IconData icon;
  
  /// Função chamada ao pressionar o botão
  final VoidCallback? onPressed;
  
  /// Indica se o botão está em estado de carregamento
  final bool isLoading;
  
  /// Tipo do botão
  final AppButtonType type;
  
  /// Tamanho do botão
  final AppButtonSize size;
  
  /// Indica se o botão deve ser circular
  final bool isCircular;
  
  /// Texto de tooltip
  final String? tooltip;
  
  /// Construtor padrão
  const AppIconButton({
    Key? key,
    required this.icon,
    this.onPressed,
    this.isLoading = false,
    this.type = AppButtonType.primary,
    this.size = AppButtonSize.medium,
    this.isCircular = true,
    this.tooltip,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    // Verificar o tema atual
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    // Determinar as cores com base no tipo e tema
    final Color backgroundColor = _getBackgroundColor(context);
    final Color iconColor = _getIconColor(context);
    
    // Determinar tamanho com base no tamanho
    final double buttonSize = _getButtonSize();
    final double iconSize = _getIconSize();
    
    // Construir botão com base no formato
    final Widget button = _buildButton(
      context: context,
      backgroundColor: backgroundColor,
      iconColor: iconColor,
      buttonSize: buttonSize,
      iconSize: iconSize,
    );
    
    // Adicionar tooltip se fornecido
    if (tooltip != null) {
      return Tooltip(
        message: tooltip!,
        child: button,
      );
    }
    
    return button;
  }
  
  /// Constrói o botão correto com base no tipo
  Widget _buildButton({
    required BuildContext context,
    required Color backgroundColor,
    required Color iconColor,
    required double buttonSize,
    required double iconSize,
  }) {
    // Verificar o tema atual
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    // Cor do botão desabilitado
    final disabledBackgroundColor = isDark 
        ? AppColors.neutralDark 
        : AppColors.neutralLight;
    
    final disabledForegroundColor = isDark 
        ? AppColors.neutralLight 
        : AppColors.neutralDark;
    
    // Determinar a forma do botão
    final OutlinedBorder shape = isCircular
        ? const CircleBorder()
        : RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
    );
    
    // Conteúdo interno do botão
    final Widget content = _buildButtonContent(context, iconColor, iconSize);
    
    // Construir com base no tipo
    switch (type) {
      case AppButtonType.primary:
        return SizedBox(
          width: buttonSize,
          height: buttonSize,
          child: ElevatedButton(
            onPressed: isLoading ? null : onPressed,
            style: ElevatedButton.styleFrom(
              backgroundColor: backgroundColor,
              disabledBackgroundColor: disabledBackgroundColor,
              disabledForegroundColor: disabledForegroundColor,
              padding: EdgeInsets.zero,
              shape: shape,
              minimumSize: Size.zero,
            ),
            child: content,
          ),
        );
        
      case AppButtonType.secondary:
        final borderColor = isDark 
            ? AppColors.primary 
            : AppColors.primary;
            
        final disabledBorderColor = isDark 
            ? AppColors.neutralDark 
            : AppColors.neutralLight;
            
        return SizedBox(
          width: buttonSize,
          height: buttonSize,
          child: OutlinedButton(
            onPressed: isLoading ? null : onPressed,
            style: OutlinedButton.styleFrom(
              foregroundColor: iconColor,
              side: BorderSide(
                color: onPressed == null ? disabledBorderColor : borderColor,
              ),
              padding: EdgeInsets.zero,
              shape: shape,
              minimumSize: Size.zero,
            ),
            child: content,
          ),
        );
        
      case AppButtonType.tertiary:
        return SizedBox(
          width: buttonSize,
          height: buttonSize,
          child: TextButton(
            onPressed: isLoading ? null : onPressed,
            style: TextButton.styleFrom(
              foregroundColor: iconColor,
              padding: EdgeInsets.zero,
              shape: shape,
              minimumSize: Size.zero,
            ),
            child: content,
          ),
        );
        
      case AppButtonType.success:
        return SizedBox(
          width: buttonSize,
          height: buttonSize,
          child: ElevatedButton(
            onPressed: isLoading ? null : onPressed,
            style: ElevatedButton.styleFrom(
              backgroundColor: backgroundColor,
              disabledBackgroundColor: disabledBackgroundColor,
              disabledForegroundColor: disabledForegroundColor,
              padding: EdgeInsets.zero,
              shape: shape,
              minimumSize: Size.zero,
            ),
            child: content,
          ),
        );
    }
  }
  
  /// Constrói o conteúdo interno do botão (ícone ou spinner)
  Widget _buildButtonContent(BuildContext context, Color iconColor, double iconSize) {
    if (isLoading) {
      return Center(
        child: SizedBox(
          width: iconSize * 0.8,
          height: iconSize * 0.8,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            valueColor: AlwaysStoppedAnimation<Color>(iconColor),
          ),
        ),
      );
    }
    
    return Icon(
      icon,
      size: iconSize,
      color: iconColor,
    );
  }
  
  /// Retorna a cor de fundo com base no tipo
  Color _getBackgroundColor(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    if (onPressed == null) {
      return isDark ? AppColors.neutralDark : AppColors.lightGrey;
    }
    
    switch (type) {
      case AppButtonType.primary:
        return AppColors.primary;
      case AppButtonType.secondary:
      case AppButtonType.tertiary:
        return Colors.transparent;
      case AppButtonType.success:
        return AppColors.success;
    }
  }
  
  /// Retorna a cor do ícone com base no tipo
  Color _getIconColor(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    if (onPressed == null) {
      return isDark ? AppColors.neutralLight : AppColors.grey;
    }
    
    switch (type) {
      case AppButtonType.primary:
        return AppColors.white;
      case AppButtonType.secondary:
      case AppButtonType.tertiary:
        return AppColors.primary;
      case AppButtonType.success:
        return Colors.white;
    }
  }
  
  /// Retorna o tamanho do botão com base no tamanho
  double _getButtonSize() {
    switch (size) {
      case AppButtonSize.small:
        return 32;
      case AppButtonSize.medium:
        return 44;
      case AppButtonSize.large:
        return 56;
    }
  }
  
  /// Retorna o tamanho do ícone com base no tamanho
  double _getIconSize() {
    switch (size) {
      case AppButtonSize.small:
        return 16;
      case AppButtonSize.medium:
        return 20;
      case AppButtonSize.large:
        return 24;
    }
  }
}

/// Componente de chip para seleção ou filtragem
class AppChip extends StatelessWidget {
  /// Texto do chip
  final String label;
  
  /// Ícone opcional 
  final IconData? icon;
  
  /// Se o chip está selecionado
  final bool isSelected;
  
  /// Função chamada ao pressionar o chip
  final VoidCallback? onTap;
  
  /// Se o chip está desabilitado
  final bool isDisabled;
  
  /// Construtor padrão
  const AppChip({
    Key? key,
    required this.label,
    this.icon,
    this.isSelected = false,
    this.onTap,
    this.isDisabled = false,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    final Color backgroundColor = isSelected
        ? AppColors.primary.withOpacity(0.1)
        : (isDark ? AppColors.surfaceDark : AppColors.surfaceLight);
        
    final Color borderColor = isSelected
        ? AppColors.primary
        : (isDark ? AppColors.neutralDark : AppColors.neutralLight);
        
    final Color textColor = isSelected
        ? AppColors.primary
        : (isDark ? AppColors.white : AppColors.neutralDarkest);
    
    final Color disabledTextColor = isDark 
        ? AppColors.neutralLight 
        : AppColors.neutralMedium;
        
    final Color disabledBorderColor = isDark 
        ? AppColors.neutralDark 
        : AppColors.neutralLight;
    
    final Color disabledBackgroundColor = isDark 
        ? AppColors.neutralDarkest 
        : AppColors.neutralLightest;
    
    return FilterChip(
      label: Text(
        label,
        style: AppTypography.bodySmall(context).copyWith(
          color: isDisabled ? disabledTextColor : textColor,
          fontWeight: FontWeight.w500,
        ),
      ),
      avatar: icon != null 
          ? Icon(
              icon, 
              size: 16, 
              color: isDisabled ? disabledTextColor : textColor,
            ) 
          : null,
      selected: isSelected,
      onSelected: isDisabled ? null : (bool _) => onTap?.call(),
      backgroundColor: isDisabled ? disabledBackgroundColor : backgroundColor,
      selectedColor: backgroundColor,
      disabledColor: disabledBackgroundColor,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppBorders.radiusFull),
        side: BorderSide(
          color: isDisabled ? disabledBorderColor : borderColor,
        ),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
    );
  }
} 