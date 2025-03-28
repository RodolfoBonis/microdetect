import 'package:camera_access/camera_access.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/camera_controller.dart';
import 'package:microdetect/design_system/app_colors.dart';

class CameraPreviewWidget extends GetWidget<CameraController> {
  const CameraPreviewWidget({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      if (!controller.isInitialized) {
        return _buildCameraDisconnected(context);
      }
      
      if (controller.isImageCaptured) {
        return _buildCapturedImage();
      }
      
      return _buildLivePreview();
    });
  }
  
  Widget _buildCameraDisconnected(BuildContext context) {
    return Center(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.6),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.neutralLight, width: 1),
        ),
        constraints: const BoxConstraints(maxWidth: 500),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.camera_alt_outlined,
              size: 64,
              color: AppColors.neutralMedium,
            ),
            const SizedBox(height: 16),
            Obx(() => Text(
              controller.cameraStatus.isEmpty 
                  ? 'Câmera não conectada' 
                  : controller.cameraStatus,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
              textAlign: TextAlign.center,
            )),
            const SizedBox(height: 24),
            Obx(() {
              if (controller.availableCameras.isEmpty) {
                return Column(
                  children: [
                    const Text(
                      'Nenhuma câmera encontrada. Verifique se sua câmera está conectada ao computador.',
                      style: TextStyle(color: Colors.white70, fontSize: 16),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: controller.refreshCameras,
                      icon: const Icon(Icons.search),
                      label: const Text('Procurar câmeras'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                        textStyle: const TextStyle(fontSize: 16),
                      ),
                    ),
                  ],
                );
              } else {
                return Column(
                  children: [
                    Text(
                      '${controller.availableCameras.length} câmera(s) disponível(is)',
                      style: const TextStyle(color: Colors.white70, fontSize: 16),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 24),
                    SizedBox(
                      width: 200,
                      height: 48,
                      child: Builder(
                        builder: (BuildContext buttonContext) {
                          return ElevatedButton.icon(
                            onPressed: () {
                              _showCameraSelectionDialog(buttonContext);
                            },
                            icon: const Icon(Icons.camera_alt, size: 24),
                            label: const Text('Selecionar Câmera'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.success,
                              foregroundColor: Colors.white,
                              textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                          );
                        }
                      ),
                    ),
                  ],
                );
              }
            }),
          ],
        ),
      ),
    );
  }
  
  void _showCameraSelectionDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext dialogContext) {
        return AlertDialog(
          title: Row(
            children: [
              Icon(Icons.camera_alt, color: AppColors.primary),
              SizedBox(width: 8),
              Text('Selecionar Câmera', style: TextStyle(fontSize: 18)),
            ],
          ),
          content: SizedBox(
            width: 350,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Selecione a câmera que deseja utilizar:',
                  style: TextStyle(color: Colors.grey[700], fontSize: 14),
                ),
                SizedBox(height: 16),
                Container(
                  constraints: BoxConstraints(maxHeight: 250),
                  child: SingleChildScrollView(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: controller.availableCameras.map((camera) {
                        final isSelected = controller.selectedCameraId == camera.id;
                        return ListTile(
                          title: Text(
                            camera.name,
                            style: TextStyle(
                              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                            ),
                          ),
                          subtitle: Text(
                            camera.position.toString().split('.').last,
                            style: TextStyle(fontSize: 12),
                          ),
                          trailing: isSelected 
                              ? Icon(Icons.check_circle, color: AppColors.success)
                              : null,
                          selected: isSelected,
                          selectedTileColor: AppColors.success.withOpacity(0.1),
                          onTap: () {
                            Navigator.of(dialogContext).pop();
                            controller.initializeSpecificCamera(camera.id);
                          },
                        );
                      }).toList(),
                    ),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: Text('Cancelar'),
            ),
            Obx(() => controller.availableCameras.length > 1 ? TextButton(
              onPressed: () {
                Navigator.of(dialogContext).pop();
                controller.refreshCameras();
              },
              child: Text('Atualizar Lista'),
            ) : SizedBox()),
          ],
        );
      },
    );
  }
  
  Widget _buildCapturedImage() {
    return Center(
      child: Obx(() {
        final frame = controller.capturedFrame;
        if (frame == null) {
          return const Text('Erro ao carregar imagem capturada');
        }
        
        return Image.memory(
          frame,
          fit: BoxFit.contain,
          gaplessPlayback: true,
        );
      }),
    );
  }
  
  Widget _buildLivePreview() {
    return Container(
      color: Colors.black,
      child: Center(
        child: Obx(() {
          final frame = controller.capturedFrame;
          
          // Se não tivermos frame, mostrar indicador de carregamento
          if (frame == null) {
            return Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
                ),
                const SizedBox(height: 16),
                // Status da câmera
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.7),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Obx(() => Text(
                    controller.cameraStatus,
                    style: const TextStyle(color: Colors.white, fontSize: 16),
                    textAlign: TextAlign.center,
                  )),
                ),
                const SizedBox(height: 24),
                // Botão de reconexão ou indicador de inicialização
                Obx(() => controller.isCameraLoading 
                  ? Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.5),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Text(
                        'Inicializando...',
                        style: TextStyle(color: Colors.white70, fontSize: 14),
                      ),
                    )
                  : ElevatedButton.icon(
                      onPressed: controller.restartCamera,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Reconectar Câmera'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      ),
                    ),
                ),
              ],
            );
          }
          
          // Quando temos um frame, mostrar a imagem
          return RepaintBoundary(
            child: Image.memory(
              frame,
              gaplessPlayback: true,
              fit: BoxFit.contain,
            ),
          );
        }),
      ),
    );
  }
} 