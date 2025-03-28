import 'package:flutter/material.dart';

/// Sistema de espaçamento da aplicação
class AppSpacing {
  /* Valores de espaçamento básicos */
  
  /// Espaçamento super pequeno (2px)
  static const double xxxSmall = 2;
  
  /// Espaçamento extra pequeno (4px)
  static const double xxSmall = 4;
  
  /// Espaçamento muito pequeno (8px)
  static const double xSmall = 8;
  
  /// Espaçamento pequeno (12px)
  static const double small = 12;
  
  /// Espaçamento médio (16px)
  static const double medium = 16;
  
  /// Espaçamento grande (24px)
  static const double large = 24;
  
  /// Espaçamento muito grande (32px)
  static const double xLarge = 32;
  
  /// Espaçamento extra grande (48px)
  static const double xxLarge = 48;
  
  /// Espaçamento gigante (64px)
  static const double xxxLarge = 64;
  
  /* Presets de padding */
  
  /// Padding super pequeno (horizontal e vertical: 2px)
  static const EdgeInsets paddingXxxSmall = EdgeInsets.all(xxxSmall);
  
  /// Padding extra pequeno (horizontal e vertical: 4px)
  static const EdgeInsets paddingXxSmall = EdgeInsets.all(xxSmall);
  
  /// Padding muito pequeno (horizontal e vertical: 8px)
  static const EdgeInsets paddingXSmall = EdgeInsets.all(xSmall);
  
  /// Padding pequeno (horizontal e vertical: 12px)
  static const EdgeInsets paddingSmall = EdgeInsets.all(small);
  
  /// Padding médio (horizontal e vertical: 16px)
  static const EdgeInsets paddingMedium = EdgeInsets.all(medium);
  
  /// Padding grande (horizontal e vertical: 24px)
  static const EdgeInsets paddingLarge = EdgeInsets.all(large);
  
  /// Padding muito grande (horizontal e vertical: 32px)
  static const EdgeInsets paddingXLarge = EdgeInsets.all(xLarge);
  
  /// Padding extra grande (horizontal e vertical: 48px)
  static const EdgeInsets paddingXxLarge = EdgeInsets.all(xxLarge);
  
  /// Padding gigante (horizontal e vertical: 64px)
  static const EdgeInsets paddingXxxLarge = EdgeInsets.all(xxxLarge);
  
  /* Presets de padding horizontal */
  
  /// Padding horizontal super pequeno (2px)
  static const EdgeInsets paddingHorizontalXxxSmall = EdgeInsets.symmetric(horizontal: xxxSmall);
  
  /// Padding horizontal extra pequeno (4px)
  static const EdgeInsets paddingHorizontalXxSmall = EdgeInsets.symmetric(horizontal: xxSmall);
  
  /// Padding horizontal muito pequeno (8px)
  static const EdgeInsets paddingHorizontalXSmall = EdgeInsets.symmetric(horizontal: xSmall);
  
  /// Padding horizontal pequeno (12px)
  static const EdgeInsets paddingHorizontalSmall = EdgeInsets.symmetric(horizontal: small);
  
  /// Padding horizontal médio (16px)
  static const EdgeInsets paddingHorizontalMedium = EdgeInsets.symmetric(horizontal: medium);
  
  /// Padding horizontal grande (24px)
  static const EdgeInsets paddingHorizontalLarge = EdgeInsets.symmetric(horizontal: large);
  
  /// Padding horizontal muito grande (32px)
  static const EdgeInsets paddingHorizontalXLarge = EdgeInsets.symmetric(horizontal: xLarge);
  
  /// Padding horizontal extra grande (48px)
  static const EdgeInsets paddingHorizontalXxLarge = EdgeInsets.symmetric(horizontal: xxLarge);
  
  /// Padding horizontal gigante (64px)
  static const EdgeInsets paddingHorizontalXxxLarge = EdgeInsets.symmetric(horizontal: xxxLarge);
  
  /* Presets de padding vertical */
  
  /// Padding vertical super pequeno (2px)
  static const EdgeInsets paddingVerticalXxxSmall = EdgeInsets.symmetric(vertical: xxxSmall);
  
  /// Padding vertical extra pequeno (4px)
  static const EdgeInsets paddingVerticalXxSmall = EdgeInsets.symmetric(vertical: xxSmall);
  
  /// Padding vertical muito pequeno (8px)
  static const EdgeInsets paddingVerticalXSmall = EdgeInsets.symmetric(vertical: xSmall);
  
  /// Padding vertical pequeno (12px)
  static const EdgeInsets paddingVerticalSmall = EdgeInsets.symmetric(vertical: small);
  
  /// Padding vertical médio (16px)
  static const EdgeInsets paddingVerticalMedium = EdgeInsets.symmetric(vertical: medium);
  
  /// Padding vertical grande (24px)
  static const EdgeInsets paddingVerticalLarge = EdgeInsets.symmetric(vertical: large);
  
  /// Padding vertical muito grande (32px)
  static const EdgeInsets paddingVerticalXLarge = EdgeInsets.symmetric(vertical: xLarge);
  
  /// Padding vertical extra grande (48px)
  static const EdgeInsets paddingVerticalXxLarge = EdgeInsets.symmetric(vertical: xxLarge);
  
  /// Padding vertical gigante (64px)
  static const EdgeInsets paddingVerticalXxxLarge = EdgeInsets.symmetric(vertical: xxxLarge);
  
  /* Configurações para layout responsivo */
  
  /// Largura máxima para conteúdo
  static const double maxContentWidth = 1200;
  
  /// Largura máxima para conteúdo estreito (forms, dialogs)
  static const double maxNarrowContentWidth = 600;
  
  /// Quebra de layout desktop
  static const double breakpointDesktop = 1024;
  
  /// Quebra de layout tablet
  static const double breakpointTablet = 768;
  
  /// Quebra de layout mobile
  static const double breakpointMobile = 480;
  
  /// Verifica se o tamanho da tela é mobile
  static bool isMobile(BuildContext context) {
    return MediaQuery.of(context).size.width < breakpointTablet;
  }
  
  /// Verifica se o tamanho da tela é tablet
  static bool isTablet(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    return width >= breakpointTablet && width < breakpointDesktop;
  }
  
  /// Verifica se o tamanho da tela é desktop
  static bool isDesktop(BuildContext context) {
    return MediaQuery.of(context).size.width >= breakpointDesktop;
  }
  
  /// Obtém o padding horizontal apropriado com base no tamanho da tela
  static EdgeInsetsGeometry getResponsiveHorizontalPadding(BuildContext context) {
    if (isMobile(context)) {
      return paddingHorizontalMedium;
    } else if (isTablet(context)) {
      return paddingHorizontalLarge;
    } else {
      return paddingHorizontalXLarge;
    }
  }
  
  /// Obtém o padding vertical apropriado com base no tamanho da tela
  static EdgeInsetsGeometry getResponsiveVerticalPadding(BuildContext context) {
    if (isMobile(context)) {
      return paddingVerticalMedium;
    } else if (isTablet(context)) {
      return paddingVerticalLarge;
    } else {
      return paddingVerticalXLarge;
    }
  }
  
  /// Obtém o padding apropriado com base no tamanho da tela
  static EdgeInsetsGeometry getResponsivePadding(BuildContext context) {
    if (isMobile(context)) {
      return paddingMedium;
    } else if (isTablet(context)) {
      return paddingLarge;
    } else {
      return paddingXLarge;
    }
  }
} 