import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';

/// Widget base para páginas da aplicação
///
/// Fornece um scaffold consistente com AppBar, Drawer (opcional) e
/// estrutura padrão para todas as páginas.
class BasePageScaffold extends StatelessWidget {
  /// Título da página
  final String title;

  /// Corpo da página
  final Widget body;

  /// Botão de ação flutuante (opcional)
  final Widget? floatingActionButton;

  /// Botões de ação da AppBar (opcional)
  final List<Widget>? actions;

  /// Leading widget da AppBar (opcional)
  final Widget? leading;

  /// Chave de scaffold para acesso ao drawer (opcional)
  final GlobalKey<ScaffoldState>? scaffoldKey;

  /// Drawer (opcional)
  final Widget? drawer;

  /// Se deve mostrar o botão de voltar
  final bool showBackButton;

  /// Se deve usar padding horizontal nas bordas do conteúdo
  final bool useSafeArea;

  /// Widget na parte inferior da tela
  final Widget? bottomNavigationBar;

  /// Widget abaixo da AppBar
  final PreferredSizeWidget? bottom;

  /// TabBar para a AppBar (opcional)
  final TabBar? tabBar;

  /// Construtor
  const BasePageScaffold({
    Key? key,
    required this.title,
    required this.body,
    this.floatingActionButton,
    this.actions,
    this.leading,
    this.scaffoldKey,
    this.drawer,
    this.showBackButton = true,
    this.useSafeArea = true,
    this.bottomNavigationBar,
    this.bottom,
    this.tabBar,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // Configurar AppBar
    final appBar = AppBar(
      title: Text(
        title,
        style: AppTypography.titleMedium(context),
      ),
      backgroundColor: isDark ? AppColors.surfaceDark : AppColors.white,
      elevation: 0,
      centerTitle: false,
      leading: leading ?? (showBackButton && Navigator.of(context).canPop()
          ? IconButton(
        icon: const Icon(Icons.arrow_back),
        onPressed: () => Navigator.of(context).pop(),
      )
          : null),
      actions: actions,
      bottom: bottom ?? (tabBar != null
          ? PreferredSize(
        preferredSize: const Size.fromHeight(48),
        child: tabBar!,
      )
          : null),
    );

    // Conteúdo principal
    final Widget content = useSafeArea
        ? SafeArea(
      child: body,
    )
        : body;

    // Scaffold completo
    return Scaffold(
      key: scaffoldKey,
      appBar: appBar,
      body: content,
      drawer: drawer,
      floatingActionButton: floatingActionButton,
      bottomNavigationBar: bottomNavigationBar,
      backgroundColor: isDark ? AppColors.backgroundDark : AppColors.background,
    );
  }
}