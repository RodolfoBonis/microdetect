import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_toast.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/annotation/controllers/annotation_controller.dart';
import 'package:microdetect/features/annotation/widgets/annotation_canvas.dart';
import 'package:microdetect/features/annotation/widgets/annotation_sidebar.dart';
import 'package:microdetect/features/annotation/widgets/dataset_selector.dart';
import 'package:microdetect/features/annotation/widgets/image_gallery_grid.dart';

class AnnotationScreen extends StatefulWidget {
  const AnnotationScreen({Key? key}) : super(key: key);

  @override
  State<AnnotationScreen> createState() => _AnnotationScreenState();
}

class _AnnotationScreenState extends State<AnnotationScreen> {
  final AnnotationController controller = Get.find<AnnotationController>();

  @override
  void initState() {
    super.initState();
    _setupErrorListener();
  }

  void _setupErrorListener() {
    ever(controller.errorMessage, (String? message) {
      if (message != null && message.isNotEmpty) {
        AppToast.error(message);
        controller.errorMessage.value = '';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: Obx(() {
        if (controller.isLoading.value && controller.datasets.isEmpty) {
          return const Center(
            child: CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation(AppColors.primary),
            ),
          );
        }
        
        return Column(
          children: [
            // Seletor de Dataset
            const DatasetSelector(),
            
            // Área de conteúdo principal
            Expanded(
              child: _buildMainContent(),
            ),
          ],
        );
      }),
      floatingActionButton: controller.hasUnsavedChanges.value 
        ? FloatingActionButton.extended(
            onPressed: () => controller.saveAllAnnotations(),
            label: const Text('Salvar anotações'),
            icon: const Icon(Icons.save),
            backgroundColor: Colors.green,
          )
        : null,
    );
  }

  Widget _buildMainContent() {
    return Obx(() {
      // Se não houver dataset selecionado, exiba uma mensagem para selecionar
      if (controller.selectedDataset.value == null) {
        return _buildEmptyState(
          icon: Icons.folder_outlined,
          title: 'Selecione um dataset',
          message: 'Escolha um dataset para iniciar a anotação de imagens',
        );
      }
      
      // Se houver um dataset selecionado, mas não houver uma imagem selecionada, 
      // exiba a galeria de imagens
      if (controller.selectedImage.value == null) {
        return _buildImageGalleryView();
      }
      
      // Se houver uma imagem selecionada, exiba a tela de anotação
      return _buildAnnotationView();
    });
  }

  Widget _buildImageGalleryView() {
    return Column(
      children: [
        // Cabeçalho da galeria
        Container(
          padding: const EdgeInsets.all(AppSpacing.medium),
          color: AppColors.white,
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Imagens do Dataset',
                      style: AppTypography.titleMedium(context),
                    ),
                    Obx(() {
                      final count = controller.images.length;
                      return Text(
                        '$count ${count == 1 ? 'imagem' : 'imagens'} encontradas',
                        style: AppTypography.bodyMedium(context).copyWith(
                          color: AppColors.grey,
                        ),
                      );
                    }),
                  ],
                ),
              ),
            ],
          ),
        ),
        
        // Galeria de imagens
        const Expanded(
          child: ImageGalleryGrid(),
        ),
      ],
    );
  }

  Widget _buildAnnotationView() {
    return Column(
      children: [
        // Botões de navegação entre imagens
        Padding(
          padding: const EdgeInsets.all(AppSpacing.small),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              IconButton(
                onPressed: controller.hasPreviousImage() 
                    ? () => controller.previousImage() 
                    : null,
                icon: const Icon(Icons.arrow_back),
                tooltip: 'Imagem anterior',
                color: AppColors.primary,
              ),
              const SizedBox(width: 16),
              Obx(() {
                final image = controller.selectedImage.value;
                return Text(
                  image != null ? image.fileName : 'Imagem',
                  style: AppTypography.bodyMedium(context),
                );
              }),
              const SizedBox(width: 16),
              IconButton(
                onPressed: controller.hasNextImage() 
                    ? () => controller.nextImage() 
                    : null,
                icon: const Icon(Icons.arrow_forward),
                tooltip: 'Próxima imagem',
                color: AppColors.primary,
              ),
            ],
          ),
        ),
        
        // Área principal de anotação
        Expanded(
          child: Row(
            children: [
              // Sidebar para gerenciar anotações e classes
              const SizedBox(
                width: 300,
                child: AnnotationSidebar(),
              ),
              
              // Área de anotação com o canvas
              Expanded(
                child: Obx(() {
                  final image = controller.selectedImage.value;
                  
                  if (image == null) {
                    return const SizedBox.shrink();
                  }
                  
                  // Usar filePath se disponível, caso contrário usar url
                  final String imagePath = image.url;
                  
                  return AnnotationCanvas(
                    imageUrl: imagePath,
                    size: Size(
                      MediaQuery.of(context).size.width - 300,
                      MediaQuery.of(context).size.height - 170, // Ajustado para acomodar os botões de navegação
                    ),
                    editable: !controller.isLoading.value && !controller.isSaving.value,
                  );
                }),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildEmptyState({
    required IconData icon,
    required String title,
    required String message,
  }) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            icon,
            size: 64,
            color: AppColors.grey,
          ),
          const SizedBox(height: AppSpacing.medium),
          Text(
            title,
            style: AppTypography.titleLarge(context),
          ),
          const SizedBox(height: AppSpacing.small),
          Text(
            message,
            style: AppTypography.bodyMedium(context).copyWith(
              color: AppColors.grey,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
} 