import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_toast.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/annotation/controllers/annotation_controller.dart';
import 'package:microdetect/features/annotation/widgets/annotation_canvas.dart';
import 'package:microdetect/features/annotation/widgets/annotation_sidebar.dart';
import 'package:microdetect/features/annotation/widgets/image_gallery_grid.dart';

class AnnotationPage extends StatefulWidget {
  const AnnotationPage({Key? key}) : super(key: key);

  @override
  State<AnnotationPage> createState() => _AnnotationPageState();
}

class _AnnotationPageState extends State<AnnotationPage> {
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
    final bool isDarkmode = Get.isDarkMode;
    final backgroundColor = isDarkmode ? AppColors.surfaceDark : AppColors.white;

    return Scaffold(
      backgroundColor: backgroundColor,
      body: Row(
        children: [
          // Área principal
          Expanded(
            child: Obx(() {
              final hasDataset = controller.selectedDataset.value != null;
              final hasImage = controller.selectedImage.value != null;

              if (!hasDataset) {
                return _buildEmptyState(
                  icon: Icons.folder_outlined,
                  title: 'Selecione um dataset',
                  message: 'Escolha um dataset para iniciar a anotação de imagens',
                );
              } else if (!hasImage) {
                return _buildImageGallery();
              } else {
                return _buildAnnotationCanvas();
              }
            }),
          ),

          // Sidebar (sempre presente)
          const SizedBox(
            width: 300,
            child: AnnotationSidebar(),
          ),
        ],
      ),
    );
  }

  // Widget que exibe a galeria de imagens do dataset
  Widget _buildImageGallery() {
    final int imageCount = controller.images.length;
    final bool isDarkMode = Get.isDarkMode;

    return Column(
      children: [
        // Cabeçalho da galeria
        Container(
          padding: const EdgeInsets.all(AppSpacing.medium),
          color: isDarkMode ? AppColors.surfaceDark : AppColors.white,
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
                    Text(
                      '$imageCount ${imageCount == 1 ? 'imagem' : 'imagens'} encontradas',
                      style: AppTypography.bodyMedium(context).copyWith(
                        color: isDarkMode ? AppColors.lightGrey : AppColors.grey,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),

        // Galeria de imagens - fundo escuro para modo noturno
        Expanded(
          child: Container(
            color: isDarkMode ? Colors.black : AppColors.white,
            child: const ImageGalleryGrid(),
          ),
        ),
      ],
    );
  }

  // Widget que exibe o canvas de anotação da imagem
  Widget _buildAnnotationCanvas() {
    final image = controller.selectedImage.value;
    final String imagePath = image?.url ?? '';
    final bool hasPrevious = controller.hasPreviousImage();
    final bool hasNext = controller.hasNextImage();
    final bool isEditable = !controller.isLoading.value && !controller.isSaving.value;

    return Column(
      children: [
        // Barra de navegação de imagens
        Container(
          padding: const EdgeInsets.symmetric(
            vertical: AppSpacing.small,
            horizontal: AppSpacing.medium,
          ),
          decoration: BoxDecoration(
            color: Get.isDarkMode ? AppColors.surfaceDark : AppColors.white,
            border: const Border(
              bottom: BorderSide(
                color: AppColors.surfaceDark,
                width: 0.5,
              ),
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              IconButton(
                onPressed: hasPrevious ? () => controller.previousImage() : null,
                icon: const Icon(Icons.arrow_back),
                tooltip: 'Imagem anterior',
                color: AppColors.primary,
              ),
              const SizedBox(width: 16),
              Text(
                image != null ? image.fileName : 'Imagem',
                style: AppTypography.bodyMedium(context),
              ),
              const SizedBox(width: 16),
              IconButton(
                onPressed: hasNext ? () => controller.nextImage() : null,
                icon: const Icon(Icons.arrow_forward),
                tooltip: 'Próxima imagem',
                color: AppColors.primary,
              ),
            ],
          ),
        ),

        // Canvas de anotação
        Expanded(
          child: AnnotationCanvas(
            imageUrl: imagePath,
            size: Size(
              MediaQuery.of(context).size.width - 300, // Remover largura da sidebar
              MediaQuery.of(context).size.height - 200,
            ),
            editable: isEditable,
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
