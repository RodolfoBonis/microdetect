import 'package:flutter/material.dart';

/// Extensão para a classe Color para manipulação de componentes de cor
extension ColorExtension on Color {
  /// Retorna uma nova cor com os componentes especificados alterados
  Color withValues({int? red, int? green, int? blue, double? alpha}) {
    return Color.fromARGB(
      alpha != null ? (alpha * 255).round() : this.alpha,
      red ?? this.red,
      green ?? this.green,
      blue ?? this.blue,
    );
  }
}

/// Sistema de cores do aplicativo
class AppColors {
  /// Cores principais
  
  /// Cor primária - Coral (Airbnb)
  static const Color primary = Color(0xFFFF5A5F);
  
  /// Cor secundária - Turquesa
  static const Color secondary = Color(0xFF00A699);
  
  /// Cor terciária - Amarelo
  static const Color tertiary = Color(0xFFFFB400);
  
  /// Variações da cor primária
  static const Color primaryLight = Color(0xFFFF8589);
  static const Color primaryDark = Color(0xFFE04145);
  
  /// Variações da cor secundária
  static const Color secondaryLight = Color(0xFF4DB6AC);
  static const Color secondaryDark = Color(0xFF008F83);
  
  /// Variações da cor terciária
  static const Color tertiaryLight = Color(0xFFFFCB66);
  static const Color tertiaryDark = Color(0xFFE5A200);
  
  /// Cores de feedback
  
  /// Cor de sucesso
  static const Color success = Color(0xFF36B37E);
  
  /// Cor de erro
  static const Color error = Color(0xFFFF5630);
  
  /// Cor de alerta
  static const Color warning = Color(0xFFFFAB00);
  
  /// Cor de informação
  static const Color info = Color(0xFF2684FF);
  
  /// Variações das cores de feedback
  static const Color successLight = Color(0xFFEAFFF7);
  static const Color errorLight = Color(0xFFFFEEEB);
  static const Color warningLight = Color(0xFFFFF9E6);
  static const Color infoLight = Color(0xFFE6F2FF);
  
  /// Cores neutras
  
  /// Cor branca
  static const Color white = Color(0xFFFFFFFF);
  
  /// Cor neutra mais clara
  static const Color neutralLightest = Color(0xFFF8F8F8);
  
  /// Cor neutra clara
  static const Color neutralLight = Color(0xFFEEEEEE);
  
  /// Cor neutra média
  static const Color neutralMedium = Color(0xFFBDBDBD);
  
  /// Cor neutra escura
  static const Color neutralDark = Color(0xFF767676);
  
  /// Cor neutra mais escura
  static const Color neutralDarkest = Color(0xFF484848);
  
  /// Cor preta
  static const Color black = Color(0xFF000000);
  
  /// Aliases adicionais para compatibilidade
  
  /// Cinza escuro (alias para neutralDarkest)
  static const Color darkGrey = neutralDarkest;
  
  /// Cinza claro (alias para neutralLight)
  static const Color lightGrey = neutralLight;
  
  /// Cinza médio (alias para neutralMedium)
  static const Color grey = neutralMedium;
  
  /// Cores de fundo
  
  /// Cor de fundo principal
  static const Color background = white;
  
  /// Cor de fundo secundária (cards, modais)
  static const Color surface = white;
  
  /// Cor de fundo secundária clara (inputs, cards, etc)
  static const Color surfaceLight = neutralLightest;
  
  /// Cor de fundo em modo escuro
  static const Color backgroundDark = Color(0xFF121212);
  
  /// Cor de fundo secundária em modo escuro
  static const Color surfaceDark = Color(0xFF1E1E1E);
  
  /// Sombras
  
  /// Sombra padrão
  static List<BoxShadow> get shadow => [
    BoxShadow(
      color: black.withOpacity(0.10),
      offset: const Offset(0, 2),
      blurRadius: 6,
    ),
  ];
  
  /// Sombra média
  static List<BoxShadow> get shadowMedium => [
    BoxShadow(
      color: black.withOpacity(0.08),
      offset: const Offset(0, 4),
      blurRadius: 8,
    ),
    BoxShadow(
      color: black.withOpacity(0.12),
      offset: const Offset(0, 1),
      blurRadius: 3,
    ),
  ];
  
  /// Sombra grande
  static List<BoxShadow> get shadowLarge => [
    BoxShadow(
      color: black.withOpacity(0.15),
      offset: const Offset(0, 8),
      blurRadius: 16,
    ),
    BoxShadow(
      color: black.withOpacity(0.10),
      offset: const Offset(0, 2),
      blurRadius: 4,
    ),
  ];
  
  /// Sombra adaptativa para tema claro ou escuro
  static List<BoxShadow> adaptiveShadow(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    if (isDark) {
      return [
        BoxShadow(
          color: black.withValues(alpha: 0.3),
          offset: const Offset(0, 2),
          blurRadius: 6,
        ),
      ];
    } else {
      return shadow;
    }
  }
  
  /// Converte um esquema de cores para o aplicativo
  static ColorScheme toColorScheme({required bool isDark}) {
    final brightness = isDark ? Brightness.dark : Brightness.light;
    final background = isDark ? backgroundDark : AppColors.background;
    final surface = isDark ? surfaceDark : AppColors.surface;
    final onPrimary = white;
    final onSecondary = white;
    final onBackground = isDark ? white : neutralDarkest;
    final onSurface = isDark ? white : neutralDarkest;
    
    return ColorScheme(
      brightness: brightness,
      primary: primary,
      onPrimary: onPrimary,
      primaryContainer: primaryLight,
      onPrimaryContainer: neutralDarkest,
      secondary: secondary,
      onSecondary: onSecondary,
      secondaryContainer: secondaryLight,
      onSecondaryContainer: neutralDarkest,
      tertiary: tertiary,
      onTertiary: neutralDarkest,
      tertiaryContainer: tertiaryLight,
      onTertiaryContainer: neutralDarkest,
      error: error,
      onError: white,
      errorContainer: errorLight,
      onErrorContainer: neutralDarkest,
      background: background,
      onBackground: onBackground,
      surface: surface,
      onSurface: onSurface,
      surfaceVariant: isDark ? Color(0xFF2D2D2D) : neutralLightest,
      onSurfaceVariant: isDark ? neutralLight : neutralDarkest,
      outline: isDark ? neutralMedium : neutralMedium,
      outlineVariant: isDark ? neutralDark.withOpacity(0.5) : neutralLight,
      shadow: black,
      scrim: black.withOpacity(0.5),
      inverseSurface: isDark ? white : neutralDarkest,
      onInverseSurface: isDark ? neutralDarkest : white,
      inversePrimary: primaryDark,
    );
  }
}

/// Classe para obter cores adaptativas com base no tema atual
class ThemeColors {
  /// Obtém a cor de fundo adaptativa (background)
  static Color background(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? AppColors.backgroundDark
        : AppColors.background;
  }
  
  /// Obtém a cor de superfície adaptativa (cards, etc)
  static Color surface(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? AppColors.surfaceDark
        : AppColors.surface;
  }
  
  /// Obtém a cor de superfície clara adaptativa (inputs, etc)
  static Color surfaceVariant(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? Color(0xFF2D2D2D)
        : AppColors.surfaceLight;
  }
  
  /// Obtém a cor de texto primária adaptativa
  static Color text(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? AppColors.white
        : AppColors.neutralDarkest;
  }
  
  /// Obtém a cor de texto secundária adaptativa
  static Color textSecondary(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? AppColors.neutralLight
        : AppColors.neutralDark;
  }
  
  /// Obtém a cor de borda adaptativa
  static Color border(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? AppColors.neutralDark
        : AppColors.neutralLight;
  }
  
  /// Obtém a cor de sombra adaptativa
  static Color shadow(BuildContext context, {double opacity = 0.1}) {
    return Theme.of(context).brightness == Brightness.dark
        ? AppColors.black.withOpacity(opacity * 1.5)
        : AppColors.black.withOpacity(opacity);
  }
  
  /// Obtém a cor do ícone adaptativa
  static Color icon(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? AppColors.white
        : AppColors.neutralDarkest;
  }
  
  /// Obtém a cor de preenchimento adaptativa para inputs
  static Color inputFill(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? AppColors.surfaceDark
        : AppColors.surfaceLight;
  }
  
  /// Obtém sombras adaptativas com base no tema
  static List<BoxShadow> boxShadow(BuildContext context, {ShadowLevel level = ShadowLevel.medium}) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    switch (level) {
      case ShadowLevel.small:
        return [
          BoxShadow(
            color: isDark 
                ? AppColors.black.withOpacity(0.3)
                : AppColors.black.withOpacity(0.1),
            offset: const Offset(0, 2),
            blurRadius: 4,
          ),
        ];
      case ShadowLevel.medium:
        return [
          BoxShadow(
            color: isDark 
                ? AppColors.black.withOpacity(0.4)
                : AppColors.black.withOpacity(0.1),
            offset: const Offset(0, 4),
            blurRadius: 8,
          ),
          if (!isDark)
          BoxShadow(
            color: AppColors.black.withOpacity(0.05),
            offset: const Offset(0, 1),
            blurRadius: 3,
          ),
        ];
      case ShadowLevel.large:
        return [
          BoxShadow(
            color: isDark 
                ? AppColors.black.withOpacity(0.5)
                : AppColors.black.withOpacity(0.15),
            offset: const Offset(0, 8),
            blurRadius: 16,
          ),
          if (!isDark)
          BoxShadow(
            color: AppColors.black.withOpacity(0.1),
            offset: const Offset(0, 2),
            blurRadius: 4,
          ),
        ];
    }
  }
}

/// Níveis de sombra disponíveis
enum ShadowLevel {
  /// Sombra pequena
  small,
  
  /// Sombra média (padrão)
  medium,
  
  /// Sombra grande
  large,
}