import 'package:flutter/material.dart';
import 'app_colors.dart';
import 'app_borders.dart';
import 'app_typography.dart';

/// Tema da aplicação MicroDetect
class AppTheme {
  /// Cria o tema claro para a aplicação
  static ThemeData get lightTheme {
    final base = ThemeData.light();
    
    return base.copyWith(
      colorScheme: ColorScheme.light(
        primary: AppColors.primary,
        secondary: AppColors.secondary,
        tertiary: AppColors.tertiary,
        error: AppColors.error,
        background: AppColors.background,
        surface: AppColors.neutralLightest,
        onPrimary: AppColors.white,
        onSecondary: AppColors.white,
        onTertiary: AppColors.white,
        onError: AppColors.white,
        onBackground: AppColors.darkGrey,
        onSurface: AppColors.darkGrey,
        // Cores adicionais para o Material 3
        surfaceTint: AppColors.primary,
        primaryContainer: AppColors.primary.withOpacity(0.1),
        onPrimaryContainer: AppColors.primary,
        secondaryContainer: AppColors.secondary.withOpacity(0.1),
        onSecondaryContainer: AppColors.secondary,
        tertiaryContainer: AppColors.tertiary.withOpacity(0.1),
        onTertiaryContainer: AppColors.tertiary,
      ),
      textTheme: AppTypography.lightTextTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.white,
        centerTitle: false,
        elevation: 0,
        iconTheme: IconThemeData(color: AppColors.darkGrey),
        titleTextStyle: AppTypography.textTheme.headlineSmall?.copyWith(
          color: AppColors.darkGrey,
        ),
      ),
      cardTheme: CardTheme(
        color: AppColors.white,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
        ),
        margin: const EdgeInsets.all(8),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          ),
          backgroundColor: AppColors.primary,
          foregroundColor: AppColors.white,
          elevation: 0,
          minimumSize: const Size(100, 48),
          textStyle: AppTypography.textTheme.labelLarge,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          ),
          foregroundColor: AppColors.primary,
          side: BorderSide(color: AppColors.primary),
          minimumSize: const Size(100, 48),
          textStyle: AppTypography.textTheme.labelLarge,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          ),
          foregroundColor: AppColors.primary,
          textStyle: AppTypography.textTheme.labelLarge?.copyWith(
            inherit: true,
            color: AppColors.primary,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.neutralLightest,
        hintStyle: AppTypography.textTheme.bodyMedium?.copyWith(
          color: AppColors.grey,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          borderSide: BorderSide(color: AppColors.primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          borderSide: BorderSide(color: AppColors.error, width: 1),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          borderSide: BorderSide(color: AppColors.error, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      ),
      checkboxTheme: CheckboxThemeData(
        fillColor: MaterialStateProperty.resolveWith<Color>((states) {
          if (states.contains(MaterialState.selected)) {
            return AppColors.primary;
          }
          return AppColors.lightGrey;
        }),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
        ),
      ),
      radioTheme: RadioThemeData(
        fillColor: MaterialStateProperty.resolveWith<Color>((states) {
          if (states.contains(MaterialState.selected)) {
            return AppColors.primary;
          }
          return AppColors.lightGrey;
        }),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: MaterialStateProperty.resolveWith<Color>((states) {
          if (states.contains(MaterialState.selected)) {
            return AppColors.primary;
          }
          return AppColors.white;
        }),
        trackColor: MaterialStateProperty.resolveWith<Color>((states) {
          if (states.contains(MaterialState.selected)) {
            return AppColors.primary.withOpacity(0.5);
          }
          return AppColors.lightGrey;
        }),
      ),
      tabBarTheme: TabBarTheme(
        labelColor: AppColors.primary,
        unselectedLabelColor: AppColors.grey,
        indicatorColor: AppColors.primary,
        labelStyle: AppTypography.textTheme.labelLarge,
        unselectedLabelStyle: AppTypography.textTheme.labelLarge,
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: AppColors.white,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.grey,
        selectedLabelStyle: AppTypography.textTheme.labelSmall,
        unselectedLabelStyle: AppTypography.textTheme.labelSmall,
        type: BottomNavigationBarType.fixed,
      ),
      dialogTheme: DialogTheme(
        backgroundColor: AppColors.white,
        elevation: 16,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
        ),
      ),
    );
  }
  
  /// Cria o tema escuro para a aplicação
  static ThemeData get darkTheme {
    final base = ThemeData.dark();
    
    return base.copyWith(
      colorScheme: ColorScheme.dark(
        primary: AppColors.primary,
        secondary: AppColors.secondary,
        tertiary: AppColors.tertiary,
        error: AppColors.error,
        background: AppColors.backgroundDark,
        surface: AppColors.surfaceDark,
        onPrimary: AppColors.white,
        onSecondary: AppColors.white,
        onTertiary: AppColors.white,
        onError: AppColors.white,
        onBackground: AppColors.white,
        onSurface: AppColors.white,
        // Cores adicionais para o Material 3
        surfaceTint: AppColors.primary,
        primaryContainer: AppColors.primary.withOpacity(0.2),
        onPrimaryContainer: AppColors.primary,
        secondaryContainer: AppColors.secondary.withOpacity(0.2),
        onSecondaryContainer: AppColors.secondary,
        tertiaryContainer: AppColors.tertiary.withOpacity(0.2),
        onTertiaryContainer: AppColors.tertiary,
      ),
      scaffoldBackgroundColor: AppColors.backgroundDark,
      textTheme: AppTypography.darkTextTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.surfaceDark,
        centerTitle: false,
        elevation: 0,
        iconTheme: IconThemeData(color: AppColors.white),
        titleTextStyle: AppTypography.darkTextTheme.headlineSmall?.copyWith(
          color: AppColors.white,
        ),
      ),
      cardTheme: CardTheme(
        color: AppColors.surfaceDark,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
        ),
        margin: const EdgeInsets.all(8),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          ),
          backgroundColor: AppColors.primary,
          foregroundColor: AppColors.white,
          elevation: 0,
          minimumSize: const Size(100, 48),
          textStyle: AppTypography.darkTextTheme.labelLarge,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          ),
          foregroundColor: AppColors.primary,
          side: BorderSide(color: AppColors.primary),
          minimumSize: const Size(100, 48),
          textStyle: AppTypography.darkTextTheme.labelLarge,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          ),
          foregroundColor: AppColors.primary,
          textStyle: AppTypography.darkTextTheme.labelLarge?.copyWith(
            inherit: true,
            color: AppColors.primary,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.surfaceDark,
        hintStyle: AppTypography.darkTextTheme.bodyMedium?.copyWith(
          color: AppColors.neutralLight,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          borderSide: BorderSide(color: AppColors.neutralDark, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          borderSide: BorderSide(color: AppColors.primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          borderSide: BorderSide(color: AppColors.error, width: 1),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          borderSide: BorderSide(color: AppColors.error, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      ),
      checkboxTheme: CheckboxThemeData(
        fillColor: MaterialStateProperty.resolveWith<Color>((states) {
          if (states.contains(MaterialState.selected)) {
            return AppColors.primary;
          }
          return AppColors.neutralDark;
        }),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
        ),
      ),
      radioTheme: RadioThemeData(
        fillColor: MaterialStateProperty.resolveWith<Color>((states) {
          if (states.contains(MaterialState.selected)) {
            return AppColors.primary;
          }
          return AppColors.neutralLight;
        }),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: MaterialStateProperty.resolveWith<Color>((states) {
          if (states.contains(MaterialState.selected)) {
            return AppColors.primary;
          }
          return AppColors.neutralLight;
        }),
        trackColor: MaterialStateProperty.resolveWith<Color>((states) {
          if (states.contains(MaterialState.selected)) {
            return AppColors.primary.withOpacity(0.5);
          }
          return AppColors.neutralDark;
        }),
      ),
      tabBarTheme: TabBarTheme(
        labelColor: AppColors.primary,
        unselectedLabelColor: AppColors.neutralLight,
        indicatorColor: AppColors.primary,
        labelStyle: AppTypography.darkTextTheme.labelLarge,
        unselectedLabelStyle: AppTypography.darkTextTheme.labelLarge,
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: AppColors.surfaceDark,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.neutralLight,
        selectedLabelStyle: AppTypography.darkTextTheme.labelSmall,
        unselectedLabelStyle: AppTypography.darkTextTheme.labelSmall,
        type: BottomNavigationBarType.fixed,
      ),
      dialogTheme: DialogTheme(
        backgroundColor: AppColors.surfaceDark,
        elevation: 16,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
        ),
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: AppColors.primary,
        inactiveTrackColor: AppColors.neutralDark,
        thumbColor: AppColors.primary,
        overlayColor: AppColors.primary.withOpacity(0.2),
      ),
      dividerTheme: DividerThemeData(
        color: AppColors.neutralDark,
        thickness: 1,
        space: 1,
      ),
      iconTheme: IconThemeData(
        color: AppColors.white,
        size: 24,
      ),
      tooltipTheme: TooltipThemeData(
        decoration: BoxDecoration(
          color: AppColors.neutralDarkest,
          borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
        ),
        textStyle: TextStyle(color: AppColors.white),
      ),
    );
  }
} 