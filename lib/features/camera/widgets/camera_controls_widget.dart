import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/camera_controller.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';

class CameraControlsWidget extends GetWidget<CameraController> {
  const CameraControlsWidget({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      // Mostrar diferentes controles com base no estado
      if (controller.isImageCaptured) {
        return _buildCaptureControls();
      } else {
        return _buildCameraControls();
      }
    });
  }
  
  Widget _buildCameraControls() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 16.0),
      color: Colors.black.withOpacity(0.4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Controle de zoom (-)
          IconButton(
            onPressed: controller.isInitialized 
                ? () => controller.handleZoom(false)
                : null,
            icon: const Icon(Icons.zoom_out),
            color: Colors.white,
            tooltip: 'Diminuir zoom',
          ),
          
          const Spacer(),
          
          // Botão de captura principal
          Obx(() => FilledButton(
            onPressed: controller.isInitialized && !controller.isCapturing
                ? controller.captureImage
                : null,
            style: FilledButton.styleFrom(
              shape: const CircleBorder(),
              minimumSize: const Size(64, 64),
              backgroundColor: AppColors.secondary,
            ),
            child: controller.isCapturing
                ? const CircularProgressIndicator(color: Colors.white)
                : const Icon(Icons.camera_alt, size: 32, color: Colors.white),
          )),
          
          const Spacer(),
          
          // Controle de zoom (+)
          IconButton(
            onPressed: controller.isInitialized 
                ? () => controller.handleZoom(true)
                : null,
            icon: const Icon(Icons.zoom_in),
            color: Colors.white,
            tooltip: 'Aumentar zoom',
          ),
        ],
      ),
    );
  }
  
  Widget _buildCaptureControls() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 16.0),
      color: Colors.black.withOpacity(0.4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Botão para descartar imagem
          FilledButton.tonal(
            onPressed: controller.discardCapturedImage,
            style: FilledButton.styleFrom(
              shape: const CircleBorder(),
              padding: const EdgeInsets.all(12),
              backgroundColor: Colors.grey.shade800,
              foregroundColor: Colors.white,
            ),
            child: const Icon(Icons.clear, size: 24),
          ),
          
          const SizedBox(width: 32),
          
          // Botão para salvar imagem
          Obx(() => FilledButton(
            onPressed: controller.isSaving 
                ? null 
                : () {
                    final cameraImage = controller.createCameraImageFromCapturedFrame();
                    controller.saveImage(cameraImage);
                  },
            style: FilledButton.styleFrom(
              shape: const CircleBorder(),
              padding: const EdgeInsets.all(16),
              backgroundColor: AppColors.success,
            ),
            child: controller.isSaving
                ? const CircularProgressIndicator(color: Colors.white)
                : const Icon(Icons.check, size: 32, color: Colors.white),
          )),
        ],
      ),
    );
  }
} 