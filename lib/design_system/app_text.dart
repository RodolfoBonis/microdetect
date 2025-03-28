import 'package:flutter/material.dart';
import 'app_colors.dart';

/// Tipografia da aplicação
class AppText {
  /// Fonte padrão da aplicação
  static const String fontFamily = 'Inter';
  
  /* Textos de Display */
  
  /// Display grande
  static const TextStyle displayLarge = TextStyle(
    fontFamily: fontFamily,
    fontSize: 57,
    fontWeight: FontWeight.w700,
    letterSpacing: -0.25,
    height: 1.12,
    color: AppColors.neutralDarkest,
  );
  
  /// Display médio
  static const TextStyle displayMedium = TextStyle(
    fontFamily: fontFamily,
    fontSize: 45,
    fontWeight: FontWeight.w700,
    letterSpacing: 0,
    height: 1.15,
    color: AppColors.neutralDarkest,
  );
  
  /// Display pequeno
  static const TextStyle displaySmall = TextStyle(
    fontFamily: fontFamily,
    fontSize: 36,
    fontWeight: FontWeight.w700,
    letterSpacing: 0,
    height: 1.22,
    color: AppColors.neutralDarkest,
  );
  
  /* Títulos */
  
  /// Título grande
  static const TextStyle titleLarge = TextStyle(
    fontFamily: fontFamily,
    fontSize: 32,
    fontWeight: FontWeight.w700,
    letterSpacing: 0,
    height: 1.25,
    color: AppColors.neutralDarkest,
  );
  
  /// Título médio
  static const TextStyle titleMedium = TextStyle(
    fontFamily: fontFamily,
    fontSize: 24,
    fontWeight: FontWeight.w700,
    letterSpacing: 0,
    height: 1.33,
    color: AppColors.neutralDarkest,
  );
  
  /// Título pequeno
  static const TextStyle titleSmall = TextStyle(
    fontFamily: fontFamily,
    fontSize: 20,
    fontWeight: FontWeight.w700,
    letterSpacing: 0,
    height: 1.4,
    color: AppColors.neutralDarkest,
  );
  
  /* Textos de corpo */
  
  /// Corpo grande
  static const TextStyle bodyLarge = TextStyle(
    fontFamily: fontFamily,
    fontSize: 18,
    fontWeight: FontWeight.w400,
    letterSpacing: 0.5,
    height: 1.55,
    color: AppColors.neutralDarkest,
  );
  
  /// Corpo médio (texto padrão da aplicação)
  static const TextStyle bodyMedium = TextStyle(
    fontFamily: fontFamily,
    fontSize: 16,
    fontWeight: FontWeight.w400,
    letterSpacing: 0.25,
    height: 1.5,
    color: AppColors.neutralDarkest,
  );
  
  /// Corpo pequeno
  static const TextStyle bodySmall = TextStyle(
    fontFamily: fontFamily,
    fontSize: 14,
    fontWeight: FontWeight.w400,
    letterSpacing: 0.4,
    height: 1.42,
    color: AppColors.neutralDarkest,
  );
  
  /* Rótulos e elementos de interface */
  
  /// Rótulo grande
  static const TextStyle labelLarge = TextStyle(
    fontFamily: fontFamily,
    fontSize: 16,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.1,
    height: 1.5,
    color: AppColors.neutralDarkest,
  );
  
  /// Rótulo médio
  static const TextStyle labelMedium = TextStyle(
    fontFamily: fontFamily,
    fontSize: 14,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.5,
    height: 1.42,
    color: AppColors.neutralDarkest,
  );
  
  /// Rótulo pequeno
  static const TextStyle labelSmall = TextStyle(
    fontFamily: fontFamily,
    fontSize: 12,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.5,
    height: 1.33,
    color: AppColors.neutralDarkest,
  );
  
  /* Variações de estilo */
  
  /// Retorna a variação de negrito de um estilo de texto
  static TextStyle bold(TextStyle style) {
    return style.copyWith(fontWeight: FontWeight.w700);
  }
  
  /// Retorna a variação de itálico de um estilo de texto
  static TextStyle italic(TextStyle style) {
    return style.copyWith(fontStyle: FontStyle.italic);
  }
  
  /// Cria um tema de texto para a aplicação
  static TextTheme createTextTheme({bool isDark = false}) {
    final Color textColor = isDark ? AppColors.white : AppColors.neutralDarkest;
    
    return TextTheme(
      displayLarge: displayLarge.copyWith(color: textColor),
      displayMedium: displayMedium.copyWith(color: textColor),
      displaySmall: displaySmall.copyWith(color: textColor),
      
      titleLarge: titleLarge.copyWith(color: textColor),
      titleMedium: titleMedium.copyWith(color: textColor),
      titleSmall: titleSmall.copyWith(color: textColor),
      
      bodyLarge: bodyLarge.copyWith(color: textColor),
      bodyMedium: bodyMedium.copyWith(color: textColor),
      bodySmall: bodySmall.copyWith(color: textColor),
      
      labelLarge: labelLarge.copyWith(color: textColor),
      labelMedium: labelMedium.copyWith(color: textColor),
      labelSmall: labelSmall.copyWith(color: textColor),
    );
  }
} 