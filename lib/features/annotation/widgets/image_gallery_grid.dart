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
    final bool isDarkMode = Get.isDarkMode;

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
              Icon(
                Icons.photo_library_outlined,
                size: 64,
                color: isDarkMode ? AppColors.lightGrey : AppColors.grey,
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
              Icon(
                Icons.image_not_supported_outlined,
                size: 64,
                color: isDarkMode ? AppColors.lightGrey : AppColors.grey,
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
    final bool isDarkMode = Get.isDarkMode;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: isDarkMode
              ? (isSelected ? AppColors.tertiaryDark : AppColors.surfaceDark)
              : (isSelected ? AppColors.tertiaryLight : AppColors.white),
          borderRadius: BorderRadius.circular(AppSpacing.small),
          border: Border.all(
            color: isDarkMode
                ? (isSelected ? AppColors.primary : Colors.black)
                : (isSelected ? AppColors.primary : AppColors.grey),
            width: isSelected ? 2 : 1,
          ),
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: image.url.isEmpty
                  ? Center(
                      child: Icon(
                        Icons.image_not_supported_outlined,
                        size: 32,
                        color:
                            isDarkMode ? AppColors.lightGrey : AppColors.grey,
                      ),
                    )
                  : Stack(
                      fit: StackFit.expand,
                      children: [
                        CachedNetworkImage(
                          imageUrl: image.url,
                          fit: BoxFit.cover,
                          progressIndicatorBuilder:
                              (context, url, downloadProgress) => Center(
                            child: CircularProgressIndicator(
                              value: downloadProgress.progress,
                              color: AppColors.primary,
                            ),
                          ),
                        ),
                        if (image.annotations.isNotEmpty)
                          Positioned(
                            top: AppSpacing.xSmall,
                            right: AppSpacing.xSmall,
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: AppSpacing.xSmall,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: AppColors.primary,
                                borderRadius: BorderRadius.circular(
                                  AppSpacing.xxSmall,
                                ),
                              ),
                              child: Text(
                                'Anotada',
                                style:
                                    AppTypography.labelSmall(context).copyWith(
                                  color: AppColors.white,
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.xSmall,
                vertical: AppSpacing.xSmall,
              ),
              color: isDarkMode
                  ? (isSelected
                      ? AppColors.tertiaryDark
                      : AppColors.surfaceDark)
                  : (isSelected
                      ? AppColors.tertiaryLight
                      : AppColors.surfaceLight),
              child: Text(
                image.fileName,
                style: AppTypography.labelSmall(context).copyWith(
                  color: isDarkMode ? AppColors.lightGrey : AppColors.darkGrey,
                ),
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
