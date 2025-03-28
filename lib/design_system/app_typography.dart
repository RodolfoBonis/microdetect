import 'package:flutter/material.dart';
import 'app_colors.dart';

/// Tipografia inspirada no design system do Airbnb
class AppTypography {
  static const String fontFamily = 'Cereal';  // Font do Airbnb
  static const String fallbackFontFamily = 'Inter';  // Alternativa

  // Text Theme para o tema claro
  static TextTheme get lightTextTheme {
    return _getBaseTextTheme(
      displayColor: AppColors.darkGrey,
      bodyColor: AppColors.darkGrey,
      labelColor: AppColors.darkGrey,
    );
  }

  // Text Theme para o tema escuro
  static TextTheme get darkTextTheme {
    return _getBaseTextTheme(
      displayColor: AppColors.white,
      bodyColor: AppColors.white,
      labelColor: AppColors.white,
    );
  }

  // Text Theme base para reuso
  static TextTheme get textTheme => lightTextTheme;

  // Gera o text theme com as cores corretas
  static TextTheme _getBaseTextTheme({
    required Color displayColor,
    required Color bodyColor,
    required Color labelColor,
  }) {
    return TextTheme(
      // Display - Grande, Bold
      displayLarge: TextStyle(
        fontFamily: fontFamily,
        fontSize: 32.0,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.5,
        color: displayColor,
      ),
      displayMedium: TextStyle(
        fontFamily: fontFamily,
        fontSize: 28.0,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.5,
        color: displayColor,
      ),
      displaySmall: TextStyle(
        fontFamily: fontFamily,
        fontSize: 24.0,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.25,
        color: displayColor,
      ),

      // Title - Medium-large, SemiBold
      titleLarge: TextStyle(
        fontFamily: fontFamily,
        fontSize: 20.0,
        fontWeight: FontWeight.w600,
        letterSpacing: 0,
        color: displayColor,
      ),
      titleMedium: TextStyle(
        fontFamily: fontFamily,
        fontSize: 16.0,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.15,
        color: displayColor,
      ),
      titleSmall: TextStyle(
        fontFamily: fontFamily,
        fontSize: 14.0,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.1,
        color: displayColor,
      ),

      // Headline - Médio, Semibold
      headlineLarge: TextStyle(
        fontFamily: fontFamily,
        fontSize: 22.0,
        fontWeight: FontWeight.w600,
        letterSpacing: -0.25,
        color: displayColor,
      ),
      headlineMedium: TextStyle(
        fontFamily: fontFamily,
        fontSize: 20.0,
        fontWeight: FontWeight.w600,
        letterSpacing: -0.25,
        color: displayColor,
      ),
      headlineSmall: TextStyle(
        fontFamily: fontFamily,
        fontSize: 18.0,
        fontWeight: FontWeight.w600,
        letterSpacing: -0.25,
        color: displayColor,
      ),

      // Body - Normal, Regular
      bodyLarge: TextStyle(
        fontFamily: fontFamily,
        fontSize: 16.0,
        fontWeight: FontWeight.w400,
        letterSpacing: 0,
        color: bodyColor,
      ),
      bodyMedium: TextStyle(
        fontFamily: fontFamily,
        fontSize: 14.0,
        fontWeight: FontWeight.w400,
        letterSpacing: 0,
        color: bodyColor,
      ),
      bodySmall: TextStyle(
        fontFamily: fontFamily,
        fontSize: 12.0,
        fontWeight: FontWeight.w400,
        letterSpacing: 0,
        color: bodyColor,
      ),

      // Label - Pequeno, Semibold
      labelLarge: TextStyle(
        fontFamily: fontFamily,
        fontSize: 14.0,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.75,
        color: labelColor,
      ),
      labelMedium: TextStyle(
        fontFamily: fontFamily,
        fontSize: 12.0,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.5,
        color: labelColor,
      ),
      labelSmall: TextStyle(
        fontFamily: fontFamily,
        fontSize: 10.0,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.5,
        color: labelColor,
      ),
    );
  }
  
  /// Retorna o TextTheme adaptativo com base no tema atual
  static TextTheme getTheme(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? darkTextTheme
        : lightTextTheme;
  }
  
  /// Retorna estilo de texto displayLarge adaptativo ao tema atual
  static TextStyle displayLarge(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 32.0,
      fontWeight: FontWeight.w700,
      letterSpacing: -0.5,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto displayMedium adaptativo ao tema atual
  static TextStyle displayMedium(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 28.0,
      fontWeight: FontWeight.w700,
      letterSpacing: -0.5,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto displaySmall adaptativo ao tema atual
  static TextStyle displaySmall(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 24.0,
      fontWeight: FontWeight.w700,
      letterSpacing: -0.25,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto titleLarge adaptativo ao tema atual
  static TextStyle titleLarge(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 20.0,
      fontWeight: FontWeight.w600,
      letterSpacing: 0,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto titleMedium adaptativo ao tema atual
  static TextStyle titleMedium(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 16.0,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.15,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto titleSmall adaptativo ao tema atual
  static TextStyle titleSmall(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 14.0,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.1,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto headlineLarge adaptativo ao tema atual
  static TextStyle headlineLarge(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 22.0,
      fontWeight: FontWeight.w600,
      letterSpacing: -0.25,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto headlineMedium adaptativo ao tema atual
  static TextStyle headlineMedium(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 20.0,
      fontWeight: FontWeight.w600,
      letterSpacing: -0.25,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto headlineSmall adaptativo ao tema atual
  static TextStyle headlineSmall(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 18.0,
      fontWeight: FontWeight.w600,
      letterSpacing: -0.25,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto bodyLarge adaptativo ao tema atual
  static TextStyle bodyLarge(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 16.0,
      fontWeight: FontWeight.w400,
      letterSpacing: 0,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto bodyMedium adaptativo ao tema atual
  static TextStyle bodyMedium(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 14.0,
      fontWeight: FontWeight.w400,
      letterSpacing: 0,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto bodySmall adaptativo ao tema atual
  static TextStyle bodySmall(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 12.0,
      fontWeight: FontWeight.w400,
      letterSpacing: 0,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto labelLarge adaptativo ao tema atual
  static TextStyle labelLarge(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 14.0,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.75,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto labelMedium adaptativo ao tema atual
  static TextStyle labelMedium(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 12.0,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.5,
      color: textColor,
    );
  }
  
  /// Retorna estilo de texto labelSmall adaptativo ao tema atual
  static TextStyle labelSmall(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? AppColors.white : AppColors.darkGrey;
    
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: 10.0,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.5,
      color: textColor,
    );
  }
} 