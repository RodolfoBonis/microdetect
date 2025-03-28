import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/camera/models/gallery_image.dart';
import 'package:microdetect/features/camera/services/camera_service.dart';
import 'package:microdetect/features/datasets/services/dataset_service.dart';

class GallerySelectorWidget extends StatefulWidget {
  /// ID do dataset ao qual as imagens serão vinculadas
  final int datasetId;


  /// Callback chamado após vincular imagens com sucesso
  final Function(int count)? onImagesLinked;

  /// Número máximo de imagens que podem ser selecionadas
  final int maxImages;

  const GallerySelectorWidget({
    Key? key,
    required this.datasetId,
    this.onImagesLinked,
    this.maxImages = 50,
  }) : super(key: key);

  @override
  State<GallerySelectorWidget> createState() => _GallerySelectorWidgetState();
}

class _GallerySelectorWidgetState extends State<GallerySelectorWidget> {
  final DatasetService _datasetService = Get.find<DatasetService>();
  final CameraService _galleryService = Get.find<CameraService>();

  final RxList<GalleryImage> _galleryImages = <GalleryImage>[].obs;
  final RxList<GalleryImage> _selectedImages = <GalleryImage>[].obs;
  final RxBool _isLoading = false.obs;
  final RxBool _isLinking = false.obs;
  final RxString _searchQuery = ''.obs;
  final RxInt _currentPage = 0.obs;
  final int _imagesPerPage = 20;
  final RxBool _hasMoreImages = true.obs;

  @override
  void initState() {
    super.initState();
    _loadGalleryImages();
  }

  Future<void> _loadGalleryImages() async {
    if (_isLoading.value || !_hasMoreImages.value) return;

    try {
      _isLoading.value = true;

      final images = await _galleryService.loadGalleryImages(
        limit: _imagesPerPage,
        skip: _currentPage.value * _imagesPerPage
      );

      images.removeWhere((image) => image.datasetId == widget.datasetId);

      if (images.isEmpty || images.length < _imagesPerPage) {
        _hasMoreImages.value = false;
      }

      if (_currentPage.value == 0) {
        _galleryImages.value = images;
      } else {
        _galleryImages.addAll(images);
      }

      _currentPage.value++;
    } catch (e) {
      _showErrorSnackbar('Erro ao carregar imagens da galeria: $e');
    } finally {
      _isLoading.value = false;
    }
  }

  Future<void> _searchImages(String query) async {
    _searchQuery.value = query;
    _currentPage.value = 0;
    _hasMoreImages.value = true;
    _galleryImages.clear();
    await _loadGalleryImages();
  }

  Future<void> _linkSelectedImagesToDataset() async {
    if (_selectedImages.isEmpty) {
      _showInfoSnackbar('Selecione pelo menos uma imagem para vincular ao dataset');
      return;
    }

    try {
      _isLinking.value = true;

      final imageIds = _selectedImages.map((image) => image.id).toList();
      final successCount = await _datasetService.linkExistingImagesToDataset(
        datasetId: widget.datasetId,
        imageIds: imageIds,
      );

      if (successCount > 0) {
        _showSuccessSnackbar(
          'Vinculadas $successCount ${successCount == 1 ? 'imagem' : 'imagens'} ao dataset'
        );

        if (widget.onImagesLinked != null) {
          widget.onImagesLinked!(successCount);
        }

        _selectedImages.clear();
      } else {
        _showErrorSnackbar('Não foi possível vincular as imagens ao dataset');
      }
    } catch (e) {
      _showErrorSnackbar('Erro ao vincular imagens ao dataset: $e');
    } finally {
      _isLinking.value = false;
    }
  }

  void _toggleImageSelection(GalleryImage image) {
    if (_isImageSelected(image)) {
      _selectedImages.remove(image);
    } else {
      if (_selectedImages.length < widget.maxImages) {
        _selectedImages.add(image);
      } else {
        _showWarningSnackbar('Você atingiu o limite de ${widget.maxImages} imagens selecionadas');
      }
    }
  }

  bool _isImageSelected(GalleryImage image) {
    return _selectedImages.any((selected) => selected.id == image.id);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: AppSpacing.small),

        // Barra de pesquisa
        TextField(
          decoration: InputDecoration(
            hintText: 'Pesquisar imagens...',
            prefixIcon: const Icon(Icons.search),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          onChanged: (value) {
            // Adiciona um pequeno debounce para não sobrecarregar a API
            Future.delayed(const Duration(milliseconds: 500), () {
              if (value == _searchQuery.value) return;
              _searchImages(value);
            });
          },
        ),
        const SizedBox(height: AppSpacing.medium),

        // Imagens selecionadas
        Obx(() => _selectedImages.isEmpty
            ? const SizedBox.shrink()
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Imagens Selecionadas (${_selectedImages.length}/${widget.maxImages})',
                    style: AppTypography.titleMedium(context),
                  ),
                  const SizedBox(height: AppSpacing.small),
                  _buildSelectedImagesPreview(),
                  const SizedBox(height: AppSpacing.medium),
                ],
              ),
        ),

        // Grade de imagens da galeria
        Obx(() => _galleryImages.isEmpty && !_isLoading.value
            ? Center(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.large),
                  child: Text(
                    'Nenhuma imagem encontrada na galeria',
                    style: AppTypography.bodyLarge(context).copyWith(
                      color: AppColors.grey,
                    ),
                  ),
                ),
              )
            : _buildGalleryImagesGrid(),
        ),

        // Botão de carregar mais
        Obx(() => Visibility(
              visible: _hasMoreImages.value && !_isLoading.value && _galleryImages.isNotEmpty,
              child: Center(
                child: TextButton.icon(
                  onPressed: _loadGalleryImages,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Carregar mais imagens'),
                ),
              ),
            ),
        ),

        // Botão de vincular imagens selecionadas
        const SizedBox(height: AppSpacing.medium),
        Obx(() => AppButton(
              label: 'Vincular ${_selectedImages.length} ${_selectedImages.length == 1 ? 'Imagem' : 'Imagens'} ao Dataset',
              onPressed: _selectedImages.isEmpty || _isLinking.value
                  ? null
                  : _linkSelectedImagesToDataset,
              isLoading: _isLinking.value,
              isFullWidth: true,
              type: AppButtonType.primary,
            ),
        ),
      ],
    );
  }

  Widget _buildGalleryImagesGrid() {
    return Obx(() {
      // Access _selectedImages.length to make sure Obx tracks changes to this list
      final selectedCount = _selectedImages.length;

      return Expanded(
        child: ListView(
          children: [
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 4,
                crossAxisSpacing: 8,
                mainAxisSpacing: 8,
                childAspectRatio: 1,
              ),
              scrollDirection: Axis.vertical,
              itemCount: _galleryImages.length,
              itemBuilder: (context, index) {
                final image = _galleryImages[index];
                final isSelected = _isImageSelected(image);

                return GestureDetector(
                  onTap: () => _toggleImageSelection(image),
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      // Imagem
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: CachedNetworkImage(
                          imageUrl: image.url,
                          fit: BoxFit.cover,
                        ),
                      ),

                      // Overlay para imagens selecionadas
                      if (isSelected)
                        Container(
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.3),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: AppColors.primary,
                              width: 2,
                            ),
                          ),
                          child: const Center(
                            child: Icon(
                              Icons.check_circle,
                              color: Colors.white,
                              size: 40,
                            ),
                          ),
                        ),
                    ],
                  ),
                );
              },
            ),
            // Indicador de carregamento
            if (_isLoading.value)
              const Padding(
                padding: EdgeInsets.all(AppSpacing.medium),
                child: Center(child: CircularProgressIndicator()),
              ),

            const SizedBox(height: AppSpacing.large),
          ],
        ),
      );
    });
  }

  Widget _buildSelectedImagesPreview() {
    return Container(
      height: 80,
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.withValues(alpha: 0.3)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: _selectedImages.length,
        padding: const EdgeInsets.all(4),
        itemBuilder: (context, index) {
          final image = _selectedImages[index];
          return Padding(
            padding: const EdgeInsets.only(right: 4),
            child: Stack(
              children: [
                Container(
                  width: 70,
                  height: 70,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(8),
                    image: DecorationImage(
                      image: CachedNetworkImageProvider(image.url),
                      fit: BoxFit.cover,
                    ),
                  ),
                ),
                Positioned(
                  top: 0,
                  right: 0,
                  child: GestureDetector(
                    onTap: () => _selectedImages.remove(image),
                    child: Container(
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.7),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.close,
                        color: Colors.white,
                        size: 16,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  void _showSuccessSnackbar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.success,
      ),
    );
  }

  void _showErrorSnackbar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.error,
      ),
    );
  }

  void _showWarningSnackbar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.warning,
      ),
    );
  }

  void _showInfoSnackbar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.info,
      ),
    );
  }
} 