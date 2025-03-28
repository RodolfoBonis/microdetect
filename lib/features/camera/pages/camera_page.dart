import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/camera_controller.dart';
import '../widgets/camera_preview_widget.dart';
import '../widgets/camera_controls_widget.dart';
import '../widgets/camera_sidebar.dart';
import '../enums/sidebar_content_enum.dart';

class CameraPage extends GetView<CameraController> {
  const CameraPage({
    Key? key,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: controller.datasetId != null ? AppBar(
        title: const Text('Câmera do Microscópio'),
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline),
            onPressed: () {
              // Implementar ajuda específica da câmera
            },
          ),
        ],
      ) : null,
      body: Row(
        children: [
          // Área principal - preview da câmera e controles
          const Expanded(
            child: Stack(
              children: [
                // Preview da câmera ocupa toda a área principal
                Positioned.fill(
                  child: CameraPreviewWidget(),
                ),
                
                // Controles da câmera na parte inferior
                Positioned(
                  bottom: 0,
                  left: 0,
                  right: 0,
                  child: CameraControlsWidget(),
                ),
              ],
            ),
          ),
          
          // Painel lateral com configurações, galeria, etc.
          Obx(() {
            final activeContent = controller.activeSidebarContent;
            return AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              width: activeContent == SidebarContent.none ? 0 : 320,
              curve: Curves.easeInOut,
              child: activeContent != SidebarContent.none ? CameraSidebar(
                activeContent: activeContent,
                onContentChanged: controller.setActiveSidebarContent,
                cameras: controller.availableCameras,
                selectedCameraId: controller.selectedCameraId,
                onRefreshCameras: controller.refreshCameras,
                onCameraSelected: controller.changeCamera,
                brightness: controller.brightness,
                contrast: controller.contrast,
                saturation: controller.saturation,
                sharpness: controller.sharpness,
                onBrightnessChanged: controller.applyBrightness,
                onContrastChanged: controller.applyContrast,
                onSaturationChanged: controller.applySaturation,
                onSharpnessChanged: controller.applySharpness,
                selectedFilter: controller.selectedFilter,
                onFilterChanged: controller.handleFilterChanged,
                resolutions: controller.availableResolutions,
                selectedResolution: controller.currentResolution,
                whiteBalances: controller.availableWhiteBalances,
                selectedWhiteBalance: controller.whiteBalance,
                onResolutionChanged: controller.handleResolutionChanged,
                onWhiteBalanceChanged: controller.handleWhiteBalanceChanged,
                images: controller.galleryImages,
                onImageSelected: controller.handleImageSelected,
                datasetId: controller.selectedDatasetId,
                onDatasetSelected: controller.handleDatasetSelected,
              ) : const SizedBox.shrink(),
            );
          }),
        ],
      ),
    );
  }
} 