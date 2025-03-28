import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/features/camera/models/gallery_image.dart';

class DatasetImagesGrid extends StatelessWidget {
  /// Lista de imagens do dataset
  final List<GalleryImage> images;
  
  /// Função chamada ao tocar em uma imagem
  final Function(GalleryImage)? onImageTap;
  
  /// Função chamada para remover uma imagem
  final Function(GalleryImage)? onRemove;
  
  /// Função chamada para alterar a classe de uma imagem
  final Function(GalleryImage, String)? onClassChange;
  
  /// Lista de classes disponíveis
  final List<String> availableClasses;
  
  /// Número de colunas no grid
  final int crossAxisCount;

  const DatasetImagesGrid({
    Key? key,
    required this.images,
    this.onImageTap,
    this.onRemove,
    this.onClassChange,
    this.availableClasses = const [],
    this.crossAxisCount = 4,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: crossAxisCount,
        crossAxisSpacing: 8,
        mainAxisSpacing: 8,
        childAspectRatio: 1,
      ),
      itemCount: images.length,
      itemBuilder: (context, index) {
        final imageData = images[index];
        return _buildImageItem(context, imageData);
      },
    );
  }

  Widget _buildImageItem(BuildContext context, GalleryImage imageData) {
    // URL da miniatura ou imagem completa
    final String imageUrl = imageData.url;
    
    return GestureDetector(
      onTap: onImageTap != null ? () => onImageTap!(imageData) : null,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.grey.withOpacity(0.3)),
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Stack(
            fit: StackFit.expand,
            children: [
              // Imagem
              CachedNetworkImage(
                imageUrl: imageUrl,
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
              
              // Botão para remover
              if (onRemove != null)
                Positioned(
                  top: 4,
                  right: 4,
                  child: _buildRemoveButton(context, imageData),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRemoveButton(BuildContext context, GalleryImage imageData) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.7),
        shape: BoxShape.circle,
      ),
      child: AppIconButton(
        icon: Icons.delete_outline,
        tooltip: 'Remover imagem',
        onPressed: () => _confirmRemoveImage(context, imageData),
      ),
    );
  }

  void _confirmRemoveImage(BuildContext context, GalleryImage imageData) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remover Imagem'),
        content: const Text(
          'Tem certeza que deseja remover esta imagem do dataset?\n'
          'A imagem continuará disponível na galeria para uso em outros datasets.',
        ),
        actions: [
          AppButton(
            onPressed: () => Navigator.of(context).pop(),
            label: 'Cancelar',
            type: AppButtonType.tertiary,
          ),
          AppButton(
            onPressed: () {
              if (onRemove != null) {
                onRemove!(imageData);
              }
              Navigator.of(context).pop();
            },
            label: 'Remover',
          ),
        ],
      ),
    );
  }

} 