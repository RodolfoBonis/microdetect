import 'package:flutter/material.dart';
import 'app_colors.dart';

/// Sistema de bordas e raios
class AppBorders {
  /* Raios de borda */
  
  /// Sem raio (0px)
  static const double radiusNone = 0;
  
  /// Raio pequeno (4px)
  static const double radiusSmall = 4;
  
  /// Raio médio (8px)
  static const double radiusMedium = 8;
  
  /// Raio grande (12px)
  static const double radiusLarge = 12;
  
  /// Raio extra grande (16px)
  static const double radiusXLarge = 16;
  
  /// Raio completo (50%)
  static const double radiusFull = 50;
  
  /* Tamanhos de borda */
  
  /// Borda fina (1px)
  static const double borderThin = 1;
  
  /// Borda média (2px)
  static const double borderMedium = 2;
  
  /// Borda espessa (3px)
  static const double borderThick = 3;
  
  /* BorderRadius pré-definidos */
  
  /// Sem BorderRadius (0px)
  static final BorderRadius none = BorderRadius.circular(radiusNone);
  
  /// BorderRadius pequeno (4px)
  static final BorderRadius small = BorderRadius.circular(radiusSmall);
  
  /// BorderRadius médio (8px)
  static final BorderRadius medium = BorderRadius.circular(radiusMedium);
  
  /// BorderRadius grande (12px)
  static final BorderRadius large = BorderRadius.circular(radiusLarge);
  
  /// BorderRadius extra grande (16px)
  static final BorderRadius xLarge = BorderRadius.circular(radiusXLarge);
  
  /// BorderRadius completo (50%)
  static final BorderRadius full = BorderRadius.circular(radiusFull);
  
  /* Estilos de borda */
  
  /// Borda fina padrão
  static Border get defaultBorder => Border.all(
    color: AppColors.neutralLight,
    width: borderThin,
  );
  
  /// Borda fina com cor primária
  static Border get primaryBorder => Border.all(
    color: AppColors.primary,
    width: borderThin,
  );
  
  /// Borda fina com cor secundária
  static Border get secondaryBorder => Border.all(
    color: AppColors.secondary,
    width: borderThin,
  );
  
  /// Borda média padrão
  static Border get mediumBorder => Border.all(
    color: AppColors.neutralLight,
    width: borderMedium,
  );
  
  /// Borda média com cor primária
  static Border get primaryMediumBorder => Border.all(
    color: AppColors.primary,
    width: borderMedium,
  );
  
  /// Borda focada (usado em campos de formulário)
  static Border get focusBorder => Border.all(
    color: AppColors.primary,
    width: borderMedium,
  );
  
  /// Borda de erro (usado em campos de formulário com erro)
  static Border get errorBorder => Border.all(
    color: AppColors.error,
    width: borderMedium,
  );
  
  /* Métodos auxiliares */
  
  /// Cria uma borda personalizada com a cor e largura especificadas
  static Border createBorder({
    Color color = Colors.transparent,
    double width = borderThin,
  }) {
    return Border.all(
      color: color,
      width: width,
    );
  }
  
  /// Cria uma borda inferior com a cor e largura especificadas
  static Border createBottomBorder({
    Color color = Colors.transparent,
    double width = borderThin,
  }) {
    return Border(
      bottom: BorderSide(
        color: color,
        width: width,
      ),
    );
  }
  
  /// Cria uma decoração de caixa com borda e raio
  static BoxDecoration createBoxDecoration({
    Color color = Colors.transparent,
    Color borderColor = Colors.transparent,
    double borderWidth = borderThin,
    double borderRadius = radiusMedium,
    List<BoxShadow>? shadows,
  }) {
    return BoxDecoration(
      color: color,
      border: Border.all(
        color: borderColor,
        width: borderWidth,
      ),
      borderRadius: BorderRadius.circular(borderRadius),
      boxShadow: shadows,
    );
  }
  
  /// Cria uma decoração de caixa para cartões
  static BoxDecoration createCardDecoration({
    Color color = Colors.white,
    Color borderColor = Colors.transparent,
    double borderRadius = radiusMedium,
  }) {
    return BoxDecoration(
      color: color,
      border: Border.all(
        color: borderColor,
        width: borderThin,
      ),
      borderRadius: BorderRadius.circular(borderRadius),
      boxShadow: AppColors.shadow,
    );
  }
}

/// Decorações de contêiner pré-definidas
class _ContainerDecoration {
  const _ContainerDecoration();
  
  /// Decoração padrão sem sombra com bordas pequenas
  BoxDecoration get defaultDecoration => BoxDecoration(
    color: AppColors.white,
    borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
    border: Border.all(color: AppColors.neutralLight, width: 1),
  );
  
  /// Decoração com sombra e bordas médias
  BoxDecoration get elevated => BoxDecoration(
    color: AppColors.white,
    borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
    boxShadow: [
      BoxShadow(
        color: AppColors.black.withOpacity(0.1),
        blurRadius: 10,
        offset: const Offset(0, 4),
      ),
    ],
  );
  
  /// Decoração com bordas grandes
  BoxDecoration get large => BoxDecoration(
    color: AppColors.white,
    borderRadius: BorderRadius.circular(AppBorders.radiusLarge),
    border: Border.all(color: AppColors.neutralLight, width: 1),
  );
  
  /// Decoração com fundo colorido
  BoxDecoration coloredBackground(Color color) => BoxDecoration(
    color: color,
    borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
  );
  
  /// Decoração com fundo gradiente
  BoxDecoration gradient({
    required List<Color> colors,
    BorderRadiusGeometry? borderRadius,
  }) => BoxDecoration(
    gradient: LinearGradient(
      colors: colors,
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    ),
    borderRadius: borderRadius ?? BorderRadius.circular(AppBorders.radiusMedium),
  );
} 