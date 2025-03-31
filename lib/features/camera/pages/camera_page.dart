import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/camera_controller.dart';
import '../widgets/camera_preview_widget.dart';
import '../widgets/camera_controls_widget.dart';
import '../widgets/camera_sidebar.dart';
import '../enums/sidebar_content_enum.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/routes/app_pages.dart';

class CameraPage extends StatelessWidget {
  const CameraPage({
    Key? key,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Verificar se o controlador está registrado
    if (!Get.isRegistered<CameraController>()) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('Câmera do Microscópio'),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, color: AppColors.error, size: 64),
              const SizedBox(height: 24),
              const Text(
                'Controlador da câmera não disponível',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              const Text(
                'Ocorreu um erro ao inicializar o módulo de câmera',
                style: TextStyle(fontSize: 16, color: Colors.grey),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: () => Get.offAllNamed(AppRoutes.home),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
                child: const Text('Voltar para o início'),
              ),
            ],
          ),
        ),
      );
    }

    final controller = Get.find<CameraController>();

    return Scaffold(
      appBar: controller.datasetId != null
          ? AppBar(
              title: const Text('Câmera do Microscópio'),
              actions: [
                IconButton(
                  icon: const Icon(Icons.help_outline),
                  onPressed: () {
                    // Implementar ajuda específica da câmera
                  },
                ),
              ],
            )
          : null,
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
            return AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              width: controller.activeSidebarContent == SidebarContent.none
                  ? 0
                  : 320,
              curve: Curves.easeInOut,
              child: controller.activeSidebarContent != SidebarContent.none
                  ? const CameraSidebar()
                  : const SizedBox.shrink(),
            );
          }),
        ],
      ),
    );
  }
}
