import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/app_root/controllers/app_root_controller.dart';
import 'package:microdetect/features/app_root/widgets/collapsible_sidebar.dart';
import 'package:microdetect/routes/app_pages.dart';

/// Widget principal do aplicativo, que gerencia o layout e a navegação.
/// Contém uma barra lateral e um RouterOutlet para exibir as páginas.
class AppRootPage extends StatefulWidget {

  AppRootPage({Key? key}) : super(key: key);

  @override
  State<AppRootPage> createState() => _AppRootPageState();
}

class _AppRootPageState extends State<AppRootPage> with WidgetsBindingObserver {
  final bool isDarkMode = Get.isDarkMode;
  final AppRootController controller = Get.find();
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  Widget build(BuildContext context) {
    final surfaceColor =
        Get.isDarkMode ? AppColors.surfaceDark : AppColors.white;

    return Scaffold(
      key: _scaffoldKey,
      backgroundColor: AppColors.background,
      body: Row(
        children: [
          // Menu lateral colapsável
          Obx(() => CollapsibleSidebar(
                isExpanded: controller.isDrawerOpen.value,
                selectedRoute: controller.currentPath.value,
                onExpandedChanged: controller.changeDrawerState,
                onRouteSelected: controller.goToPage,
              )),

          // Conteúdo principal
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Barra de ferramentas superior
                _buildTopBar(context),

                // Conteúdo da página
                Expanded(
                  child: Container(
                    color: surfaceColor,
                    child: GetRouterOutlet.builder(
                      routerDelegate: Get.rootDelegate,
                      builder: (context, delegate, currentRoute) {
                        return Scaffold(
                          body: GetRouterOutlet(
                            anchorRoute: AppRoutes.root,
                            initialRoute: AppRoutes.home,
                          ),
                        );
                      },
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopBar(BuildContext context) {
    final backgroundColor =
        Get.isDarkMode ? AppColors.surfaceDark : AppColors.white;
    final textColor =
        Get.isDarkMode ? AppColors.white : AppColors.neutralDarkest;
    final iconColor =
        Get.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark;

    return Container(
      height: 60,
      decoration: BoxDecoration(
        color: backgroundColor,
        boxShadow: [
          BoxShadow(
            color: AppColors.black.withValues(alpha: 0.05),
            offset: const Offset(0, 2),
            blurRadius: 4,
          ),
        ],
      ),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Título da página atual
          Obx(() => Text(
                AppRoutes.getTitlePage(controller.currentPath.value),
                style: AppTypography.headlineMedium(context).copyWith(
                  color: textColor,
                ),
              )),

          // Ações da barra de ferramentas
          Row(
            children: [
              // Botão de tema
              IconButton(
                icon: Icon(
                  Get.isDarkMode ? Icons.wb_sunny : Icons.nightlight_round,
                  color: iconColor,
                ),
                onPressed: () => controller.toggleThemeMode(),
                tooltip: Get.isDarkMode
                    ? 'Mudar para modo claro'
                    : 'Mudar para modo escuro',
              ),

              // Botão de atualizar
              IconButton(
                icon: Icon(Icons.refresh, color: iconColor),
                onPressed: controller.refreshCurrentScreen,
                tooltip: 'Atualizar',
              ),

              // Botão de ajuda
              IconButton(
                icon: Icon(Icons.help_outline, color: iconColor),
                onPressed: () => controller.showHelp,
                tooltip: 'Ajuda',
              ),
            ],
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    Get.rootDelegate.offAndToNamed(AppRoutes.home);
    super.dispose();
  }
}
