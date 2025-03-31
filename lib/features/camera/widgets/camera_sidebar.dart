import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/features/camera/widgets/adjustment_panel.dart';
import 'package:microdetect/features/camera/widgets/gallery_panel.dart';
import 'package:microdetect/features/camera/widgets/settings_panel.dart';

import '../controllers/camera_controller.dart';
import '../enums/sidebar_content_enum.dart';

/// Tipo de conteúdo exibido na barra lateral


/// Barra lateral para o módulo de câmera
class CameraSidebar extends StatefulWidget {
  /// Largura da barra lateral
  final double width;


  const CameraSidebar({
    Key? key,
    this.width = 320,
  }) : super(key: key);

  @override
  State<CameraSidebar> createState() => _CameraSidebarState();
}

class _CameraSidebarState extends State<CameraSidebar> with SingleTickerProviderStateMixin {
  // Controlador para animação do conteúdo
  late TabController _tabController;
  final CameraController _controller = Get.find<CameraController>();

  @override
  void initState() {
    super.initState();

    // Inicializar controlador de tabs
    _tabController = TabController(
      length: 3,
      vsync: this,
      initialIndex: _getTabIndexFromContent(_controller.activeSidebarContent),
    );

    _tabController.addListener(() {
      if (!_tabController.indexIsChanging) {
        final newContent = _getContentFromTabIndex(_tabController.index);
        if (newContent != _controller.activeSidebarContent) {
          _controller.setActiveSidebarContent(newContent);
        }
      }
    });
  }

  int _getTabIndexFromContent(SidebarContent content) {
    switch (content) {
      case SidebarContent.settings:
        return 0;
      case SidebarContent.adjustments:
        return 1;
      case SidebarContent.gallery:
        return 2;
      default:
        return 0;
    }
  }

  SidebarContent _getContentFromTabIndex(int index) {
    switch (index) {
      case 0:
        return SidebarContent.settings;
      case 1:
        return SidebarContent.adjustments;
      case 2:
        return SidebarContent.gallery;
      default:
        return SidebarContent.settings;
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Obter o tema atual
    final theme = Theme.of(context);
    final isDarkMode = theme.brightness == Brightness.dark;

    // Adaptar cores para o tema atual
    final backgroundColor = isDarkMode ? AppColors.surfaceDark : AppColors.surfaceLight;
    final shadowColor = isDarkMode ? AppColors.black.withValues(alpha: 0.3) : AppColors.black.withValues(alpha: 0.15);

    return Container(
      width: widget.width,
      decoration: BoxDecoration(
        color: backgroundColor,
        boxShadow: [
          BoxShadow(
            color: shadowColor,
            blurRadius: 8,
            offset: const Offset(-3, 0),
          ),
        ],
      ),
      child: Column(
        children: [
          Expanded(
            child: _buildTabView(isDarkMode),
          ),
        ],
      ),
    );
  }

  Widget _buildTabView(bool isDarkMode) {
    // Adaptar cores para o tema atual
    final unselectedTabColor = isDarkMode ? AppColors.neutralLight : AppColors.neutralDark;
    final tabBackgroundColor = isDarkMode ? AppColors.surfaceDark : AppColors.white;

    return Column(
      children: [
        Container(
          color: tabBackgroundColor,
          child: Row(
            children: [
              Expanded(
                child: TabBar(
                  controller: _tabController,
                  labelColor: AppColors.primary,
                  unselectedLabelColor: unselectedTabColor,
                  indicatorColor: AppColors.primary,
                  indicatorSize: TabBarIndicatorSize.tab,
                  tabs: const [
                    Tab(icon: Icon(Icons.settings), text: 'Configurações'),
                    Tab(icon: Icon(Icons.tune), text: 'Ajustes'),
                    Tab(icon: Icon(Icons.photo_library), text: 'Galeria'),
                  ],
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              // Configurações da câmera
              SettingsPanel(),
              // Ajustes de imagem
              AdjustmentPanel(),
              // Galeria de imagens
              const GalleryPanel(),
            ],
          ),
        ),
      ],
    );
  }
}