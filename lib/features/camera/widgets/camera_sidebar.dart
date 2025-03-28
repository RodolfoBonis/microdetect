import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera_access/camera_access.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/camera/models/gallery_image.dart';
import 'package:microdetect/features/camera/widgets/adjustment_panel.dart';
import 'package:microdetect/features/camera/widgets/gallery_panel.dart';
import 'package:microdetect/features/camera/widgets/settings_panel.dart';
import 'package:get/get.dart';
import 'package:cached_network_image/cached_network_image.dart';

import '../controllers/camera_controller.dart';
import '../enums/sidebar_content_enum.dart';

/// Tipo de conteúdo exibido na barra lateral


/// Barra lateral para o módulo de câmera
class CameraSidebar extends StatefulWidget {
  /// Largura da barra lateral
  final double width;

  /// Tipo de conteúdo atual
  final SidebarContent activeContent;

  /// Callback para quando o conteúdo muda
  final Function(SidebarContent)? onContentChanged;

  /// Callback quando a barra lateral é fechada
  final VoidCallback? onClose;

  /// Câmeras e configurações de câmera
  final List<CameraDevice> cameras;
  final String selectedCameraId;
  final VoidCallback onRefreshCameras;
  final ValueChanged<String> onCameraSelected;
  final List<String> resolutions;
  final String? selectedResolution;
  final List<String> whiteBalances;
  final String? selectedWhiteBalance;

  /// Callback quando uma configuração é alterada
  final ValueChanged<String>? onResolutionChanged;
  final ValueChanged<String>? onWhiteBalanceChanged;
  final ValueChanged<String>? onFilterChanged;

  /// Valores atuais dos ajustes
  final double brightness;
  final double contrast;
  final double saturation;
  final double sharpness;
  final String selectedFilter;

  /// Callbacks para mudanças nos ajustes
  final ValueChanged<double> onBrightnessChanged;
  final ValueChanged<double> onContrastChanged;
  final ValueChanged<double> onSaturationChanged;
  final ValueChanged<double> onSharpnessChanged;

  /// Lista de imagens para a galeria
  final List<GalleryImage> images;
  final ValueChanged<GalleryImage>? onImageSelected;

  /// ID do dataset atual (quando aberto de um dataset)
  final int? datasetId;

  /// Callback quando um dataset é selecionado
  final ValueChanged<int>? onDatasetSelected;

  const CameraSidebar({
    Key? key,
    this.width = 320,
    required this.activeContent,
    this.onContentChanged,
    this.onClose,
    required this.cameras,
    required this.selectedCameraId,
    required this.onRefreshCameras,
    required this.onCameraSelected,
    required this.brightness,
    required this.contrast,
    required this.saturation,
    required this.sharpness,
    required this.onBrightnessChanged,
    required this.onContrastChanged,
    required this.onSaturationChanged,
    required this.onSharpnessChanged,
    this.selectedFilter = 'normal',
    this.onFilterChanged,
    this.resolutions = const ['sd', 'hd', 'fullhd'],
    this.selectedResolution,
    this.whiteBalances = const ['auto', 'sunny', 'cloudy', 'tungsten', 'fluorescent'],
    this.selectedWhiteBalance,
    this.onResolutionChanged,
    this.onWhiteBalanceChanged,
    this.images = const [],
    this.onImageSelected,
    this.datasetId,
    this.onDatasetSelected,
  }) : super(key: key);

  @override
  State<CameraSidebar> createState() => _CameraSidebarState();
}

class _CameraSidebarState extends State<CameraSidebar> with SingleTickerProviderStateMixin {
  // Controlador para animação do conteúdo
  late TabController _tabController;

  @override
  void initState() {
    super.initState();

    // Inicializar controlador de tabs
    _tabController = TabController(
      length: 3,
      vsync: this,
      initialIndex: _getTabIndexFromContent(widget.activeContent),
    );

    _tabController.addListener(() {
      if (!_tabController.indexIsChanging) {
        final newContent = _getContentFromTabIndex(_tabController.index);
        if (newContent != widget.activeContent) {
          widget.onContentChanged?.call(newContent);
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
  void didUpdateWidget(CameraSidebar oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.activeContent != widget.activeContent) {
      _tabController.animateTo(_getTabIndexFromContent(widget.activeContent));
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
              if (widget.onClose != null)
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: widget.onClose,
                  color: unselectedTabColor,
                ),
            ],
          ),
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              // Configurações da câmera
              SettingsPanel(
                cameras: widget.cameras,
                selectedCameraId: widget.selectedCameraId,
                resolution: widget.selectedResolution ?? 'hd',
                whiteBalance: widget.selectedWhiteBalance ?? 'auto',
                filter: widget.selectedFilter,
                onCameraSelected: widget.onCameraSelected,
                onRefreshCameras: widget.onRefreshCameras,
                onResolutionChanged: widget.onResolutionChanged,
                onWhiteBalanceChanged: widget.onWhiteBalanceChanged,
                onFilterChanged: widget.onFilterChanged,
                datasetId: widget.datasetId,
                onDatasetSelected: widget.onDatasetSelected,
              ),

              // Ajustes de imagem
              AdjustmentPanel(
                brightness: widget.brightness,
                contrast: widget.contrast,
                saturation: widget.saturation,
                sharpness: widget.sharpness,
                selectedFilter: widget.selectedFilter,
                onBrightnessChanged: widget.onBrightnessChanged,
                onContrastChanged: widget.onContrastChanged,
                onSaturationChanged: widget.onSaturationChanged,
                onSharpnessChanged: widget.onSharpnessChanged,
                onFilterChanged: widget.onFilterChanged,
              ),

              // Galeria de imagens
              GalleryPanel(
                images: widget.images,
                onImageSelected: widget.onImageSelected,
                datasetId: widget.datasetId,
              ),
            ],
          ),
        ),
      ],
    );
  }
}