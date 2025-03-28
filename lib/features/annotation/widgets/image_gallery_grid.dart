import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/annotation/controllers/annotation_controller.dart';
import 'package:microdetect/features/annotation/models/annotation.dart';
import 'package:microdetect/features/camera/models/gallery_image.dart';

/// Widget para exibir uma grade de imagens do dataset para seleção
class ImageGalleryGrid extends StatelessWidget {
  /// Altura desejada dos itens da grade
  final double itemHeight;
  
  /// Quantidade de colunas na grade
  final int crossAxisCount;

  const ImageGalleryGrid({
    Key? key,
    this.itemHeight = 150,
    this.crossAxisCount = 3,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final AnnotationController controller = Get.find<AnnotationController>();
    
    return Obx(() {
      if (controller.isLoading.value) {
        return const Center(
          child: CircularProgressIndicator(),
        );
      }
      
      if (controller.selectedDataset.value == null) {
        return Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.photo_library_outlined,
                size: 64,
                color: AppColors.grey,
              ),
              const SizedBox(height: AppSpacing.medium),
              Text(
                'Selecione um dataset para visualizar suas imagens',
                style: AppTypography.bodyLarge(context),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        );
      }
      
      if (controller.images.isEmpty) {
        return Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.image_not_supported_outlined,
                size: 64,
                color: AppColors.grey,
              ),
              const SizedBox(height: AppSpacing.medium),
              Text(
                'Não há imagens disponíveis neste dataset',
                style: AppTypography.bodyLarge(context),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        );
      }
      
      return GridView.builder(
        padding: const EdgeInsets.all(AppSpacing.small),
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: crossAxisCount,
          childAspectRatio: 1,
          crossAxisSpacing: AppSpacing.small,
          mainAxisSpacing: AppSpacing.small,
        ),
        itemCount: controller.images.length,
        itemBuilder: (context, index) {
          final image = controller.images[index];
          final isSelected = controller.selectedImage.value?.id == image.id;
          
          return ImageGalleryItem(
            image: image,
            isSelected: isSelected,
            onTap: () => controller.selectImage(image),
          );
        },
      );
    });
  }
}

/// Widget para exibir um item na galeria de imagens
class ImageGalleryItem extends StatelessWidget {
  /// Imagem a ser exibida
  final AnnotatedImage image;
  
  /// Indica se esta imagem está selecionada
  final bool isSelected;
  
  /// Callback quando o item é clicado
  final VoidCallback onTap;

  const ImageGalleryItem({
    Key? key,
    required this.image,
    this.isSelected = false,
    required this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.circular(AppSpacing.small),
          border: Border.all(
            color: isSelected ? AppColors.primary : AppColors.surfaceDark,
            width: isSelected ? 3 : 1,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: AppColors.primary.withOpacity(0.5),
                    blurRadius: 8,
                    spreadRadius: 2,
                  )
                ]
              : null,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Imagem (com overlay de contagem de anotações)
            Expanded(
              child: Stack(
                fit: StackFit.expand,
                children: [
                  // Imagem
                  ClipRRect(
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(AppSpacing.small - 1),
                      topRight: Radius.circular(AppSpacing.small - 1),
                    ),
                    child: CachedNetworkImage(
                      imageUrl: image.url,
                      fit: BoxFit.cover,
                      progressIndicatorBuilder: (context, str, progress) {
                        return Center(
                          child: CircularProgressIndicator(
                            value: progress.progress,
                            valueColor: const AlwaysStoppedAnimation(AppColors.primary),
                          ),
                        );
                      },
                    ),
                  ),
                  
                  // Badge com contagem de anotações
                  if (image.annotations.isNotEmpty)
                    Positioned(
                      top: AppSpacing.xSmall,
                      right: AppSpacing.xSmall,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.small,
                          vertical: AppSpacing.xxSmall,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.primary,
                          borderRadius: BorderRadius.circular(AppSpacing.xSmall),
                        ),
                        child: Text(
                          '${image.annotations.length}',
                          style: AppTypography.labelMedium(context).copyWith(
                            color: AppColors.white,
                          ),
                        ),
                      ),
                    ),
                  
                  // Seleção
                  if (isSelected)
                    Positioned(
                      top: AppSpacing.xSmall,
                      left: AppSpacing.xSmall,
                      child: Container(
                        padding: const EdgeInsets.all(AppSpacing.xxSmall),
                        decoration: const BoxDecoration(
                          color: AppColors.primary,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.check,
                          color: AppColors.white,
                          size: 16,
                        ),
                      ),
                    ),
                ],
              ),
            ),
            
            // Nome do arquivo
            Container(
              padding: const EdgeInsets.all(AppSpacing.small),
              decoration: const BoxDecoration(
                color: AppColors.surfaceLight,
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(AppSpacing.small - 1),
                  bottomRight: Radius.circular(AppSpacing.small - 1),
                ),
              ),
              child: Text(
                image.fileName,
                style: AppTypography.bodySmall(context),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
} 