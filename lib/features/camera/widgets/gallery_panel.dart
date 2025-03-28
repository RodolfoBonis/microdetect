import 'dart:io';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/services/backend_service.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/features/camera/controllers/camera_controller.dart';
import 'package:microdetect/features/camera/models/gallery_image.dart';
import 'package:microdetect/features/camera/services/camera_service.dart';
import 'package:microdetect/core/services/api_service.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';

/// Painel que exibe a galeria de imagens capturadas pelo usuário
class GalleryPanel extends StatefulWidget {
  /// Lista de imagens da galeria (opcional, se não fornecida, será carregada do serviço)
  final List<GalleryImage>? images;

  /// Callback quando uma imagem é selecionada
  final ValueChanged<GalleryImage>? onImageSelected;

  /// Callback quando o botão de fechar é pressionado
  final VoidCallback? onClose;

  /// Dataset ID para filtrar imagens
  final int? datasetId;

  const GalleryPanel({
    Key? key,
    this.images,
    this.onImageSelected,
    this.onClose,
    this.datasetId,
  }) : super(key: key);

  @override
  State<GalleryPanel> createState() => _GalleryPanelState();
}

class _GalleryPanelState extends State<GalleryPanel> {
  final CameraController _cameraController = Get.find();

  @override
  void initState() {
    super.initState();
    _loadImages();
  }

  /// Carrega as imagens da galeria
  Future<void> _loadImages() async {
    await _cameraController.loadSavedImages();
  }

  @override
  Widget build(BuildContext context) {
    // Obter o tema atual
    final theme = Theme.of(context);
    final isDarkMode = theme.brightness == Brightness.dark;

    // Adaptar cores com base no tema
    final backgroundColor =
        isDarkMode ? AppColors.backgroundDark : AppColors.white;
    final textColor = isDarkMode ? AppColors.white : AppColors.neutralDarkest;
    final emptyStateColor =
        isDarkMode ? AppColors.neutralLight : AppColors.neutralDark;

    return Container(
      color: backgroundColor,
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.medium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Galeria de Imagens',
                  style: AppTypography.textTheme.headlineSmall?.copyWith(
                    color: isDarkMode ? AppColors.white : AppColors.primary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.refresh),
                  tooltip: 'Atualizar',
                  onPressed: _loadImages,
                  color: AppColors.primary,
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.small),

            // Envolver todo o conteúdo dinâmico em um único Obx
            Expanded(
              child: Obx(() {
                final isLoading = _cameraController.isLoadingImages;
                final images = _cameraController.galleryImages;
                final imageCount = images.length;

                // Informações sobre o número de imagens
                final countInfo = Text(
                  '$imageCount imagens capturadas',
                  style: AppTypography.textTheme.bodyMedium?.copyWith(
                    color: textColor,
                  ),
                );

                if (isLoading) {
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      countInfo,
                      const SizedBox(height: AppSpacing.medium),
                      Expanded(child: _buildLoadingState()),
                    ],
                  );
                } else if (images.isEmpty) {
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      countInfo,
                      const SizedBox(height: AppSpacing.medium),
                      Expanded(child: _buildEmptyState(emptyStateColor)),
                    ],
                  );
                } else {
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      countInfo,
                      const SizedBox(height: AppSpacing.medium),
                      Expanded(child: _buildImageGrid(isDarkMode, images)),
                    ],
                  );
                }
              }),
            ),
          ],
        ),
      ),
    );
  }

  /// Exibe estado de carregamento
  Widget _buildLoadingState() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: AppSpacing.medium),
          Text('Carregando imagens...'),
        ],
      ),
    );
  }

  /// Constrói o grid de imagens da galeria
  Widget _buildImageGrid(bool isDarkMode, List<GalleryImage> images) {
    final borderColor =
        isDarkMode ? AppColors.neutralDark : AppColors.neutralLight;

    return RefreshIndicator(
      onRefresh: () => _loadImages(),
      child: GridView.builder(
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          mainAxisSpacing: AppSpacing.small,
          crossAxisSpacing: AppSpacing.small,
          childAspectRatio: 1.0,
        ),
        itemCount: images.length,
        itemBuilder: (context, index) {
          final image = images[index];

          return Card(
            margin: EdgeInsets.zero,
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
              side: BorderSide(color: borderColor),
            ),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: () => widget.onImageSelected?.call(image),
              child: Stack(
                fit: StackFit.expand,
                children: [
                  // Imagem
                  _buildImagePreview(image),

                  // Sobreposição com o nome da imagem
                  Positioned(
                    bottom: 0,
                    left: 0,
                    right: 0,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.small,
                        vertical: AppSpacing.xxSmall,
                      ),
                      decoration: BoxDecoration(
                        color: isDarkMode
                            ? AppColors.black.withValues(alpha: 0.7)
                            : AppColors.white.withValues(alpha: 0.8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            image.fileName,
                            style: AppTypography.textTheme.bodySmall?.copyWith(
                              color: isDarkMode
                                  ? AppColors.white
                                  : AppColors.neutralDarkest,
                              overflow: TextOverflow.ellipsis,
                            ),
                            maxLines: 1,
                          ),
                        ],
                      ),
                    ),
                  ),

                  // Badge com número de datasets associados
                  if (image.hasDatasets)
                    Positioned(
                      top: 8,
                      right: 8,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 6,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.primary,
                          borderRadius:
                              BorderRadius.circular(AppBorders.radiusSmall),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.folder,
                              color: AppColors.white,
                              size: 12,
                            ),
                            const SizedBox(width: 2),
                            Text(
                              '${image.datasets.length}',
                              style: const TextStyle(
                                color: AppColors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  /// Constrói a pré-visualização da imagem (carregando do servidor se necessário)
  Widget _buildImagePreview(GalleryImage image) {
    // Caso contrário, carregar sob demanda
    return CachedNetworkImage(
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
    );
  }

  /// Constrói o estado vazio (sem imagens)
  Widget _buildEmptyState(Color textColor) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.photo_library_outlined,
            size: 64,
            color: textColor,
          ),
          const SizedBox(height: AppSpacing.small),
          Text(
            'Nenhuma imagem capturada',
            style: AppTypography.textTheme.bodyLarge?.copyWith(
              color: textColor,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: AppSpacing.small),
          Text(
            'Capture imagens usando a câmera para vê-las aqui',
            style: AppTypography.textTheme.bodyMedium?.copyWith(
              color: textColor,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: AppSpacing.medium),
          ElevatedButton.icon(
            onPressed: _loadImages,
            icon: const Icon(Icons.refresh),
            label: const Text('Atualizar'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    );
  }
}
