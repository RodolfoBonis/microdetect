import 'package:get/get.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/design_system/app_toast.dart';
import 'package:microdetect/features/camera/models/gallery_image.dart';
import 'package:microdetect/features/camera/services/camera_service.dart';
import 'package:microdetect/features/datasets/models/class_distribution.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';
import 'package:microdetect/features/datasets/models/dataset_statistics.dart';
import 'package:microdetect/features/datasets/services/dataset_service.dart';

class DatasetDetailController extends GetxController {
  // Injeções de dependência
  final DatasetService _datasetService = Get.find<DatasetService>(tag: 'datasetService');
  final CameraService _cameraService = Get.find<CameraService>();

  // Estado observável
  final Rx<Dataset?> _dataset = Rx<Dataset?>(null);
  final RxBool _isLoading = false.obs;
  final RxString _errorMessage = ''.obs;
  final RxList<ClassDistribution> _classDistribution =
      <ClassDistribution>[].obs;
  final RxBool _isClassDistributionLoading = false.obs;
  final RxBool _isAddingClass = false.obs;
  final RxString _newClassName = ''.obs;
  final Rx<DatasetStatistics?> _statistics = Rx<DatasetStatistics?>(null);
  final RxList<GalleryImage> _datasetImages = <GalleryImage>[].obs;

  // Parâmetros
  final int datasetId;

  // Construtor
  DatasetDetailController({required this.datasetId});

  // Getters para estado observável
  Dataset? get dataset => _dataset.value;

  bool get isLoading => _isLoading.value;

  String get errorMessage => _errorMessage.value;

  List<ClassDistribution> get classDistribution => _classDistribution;

  bool get isClassDistributionLoading => _isClassDistributionLoading.value;

  bool get isAddingClass => _isAddingClass.value;

  String get newClassName => _newClassName.value;

  DatasetStatistics? get statistics => _statistics.value;

  List<GalleryImage> get datasetImages => _datasetImages;

  @override
  void onInit() {
    super.onInit();
    loadDataset();
  }


  // Carregar dados do dataset
  Future<void> loadDataset() async {
    _isLoading.value = true;
    _errorMessage.value = '';

    try {
      final datasetData = await _datasetService.getDataset(datasetId);
      if (datasetData != null) {
        _dataset.value = datasetData;
        _newClassName.value = datasetData.name;

        // Carregar distribuição de classes e estatísticas em paralelo
        await loadClassDistribution();
        await loadStatistics();
        await loadImages();
      } else {
        _errorMessage.value = 'Dataset não encontrado';
        LoggerUtil.error(_errorMessage.value);
      }
    } catch (e) {
      _errorMessage.value = 'Erro ao carregar dataset: $e';
      LoggerUtil.error(_errorMessage.value, e);
    } finally {
      _isLoading.value = false;
    }
  }

  // Buscar distribuição de classes
  Future<void> loadClassDistribution() async {
    if (_isClassDistributionLoading.value) return;

    _isClassDistributionLoading.value = true;

    try {
      final response = await _datasetService.getClassDistribution(datasetId);

      if (response.isNotEmpty) {
        final List<ClassDistribution> distributions =
            response.map((json) => ClassDistribution.fromJson(json)).toList();

        _classDistribution.assignAll(distributions);
        LoggerUtil.info(
            'Distribuição de classes carregada: ${distributions.length} classes');
      } else {
        _classDistribution.clear();
        LoggerUtil.info('Nenhuma distribuição de classe encontrada');
      }
    } catch (e) {
      _errorMessage.value = 'Erro ao buscar distribuição de classes: $e';
      LoggerUtil.error(_errorMessage.value, e);
    } finally {
      _isClassDistributionLoading.value = false;
    }
  }

  // Carregar estatísticas
  Future<void> loadStatistics() async {
    try {
      final stats = await _datasetService.getDatasetStatistics(datasetId);
      _statistics.value = stats;
    } catch (e) {
      LoggerUtil.error('Erro ao carregar estatísticas', e);
    }
  }

  // Carregar imagens do dataset
  Future<void> loadImages({bool reset = false}) async {
    _isLoading.value = true;

    try {
      if (reset) {
        _datasetImages.clear();
        _datasetImages.value = [];
      }

      final images = await _cameraService.loadGalleryImages(
        datasetId: datasetId,
      );

      _datasetImages.value = images;
    } catch (e) {
      _errorMessage.value = 'Erro ao carregar imagens do dataset: $e';
      LoggerUtil.error(_errorMessage.value, e);
    } finally {
      _isLoading.value = false;
    }
  }

  // Adicionar uma nova classe
  Future<bool> addClass() async {
    final className = _newClassName.value.trim();

    if (className.isEmpty) {
      AppToast.warning(
        'Aviso',
        description: 'O nome da classe não pode estar vazio',
      );
      return false;
    }

    if (dataset?.classes.contains(className) ?? false) {
      AppToast.warning(
        'Aviso',
        description: 'Esta classe já existe no dataset',
      );
      return false;
    }

    _isAddingClass.value = true;

    try {
      final success = await _datasetService.addClass(datasetId, className);

      if (success) {
        _newClassName.value = '';

        // Atualizar o dataset e a distribuição de classes
        await loadDataset();

        // Notificar sucesso
        AppToast.success(
          'Sucesso',
          description: 'Classe "$className" adicionada com sucesso!',
        );

        return true;
      } else {
        AppToast.error(
          'Erro',
          description: 'Não foi possível adicionar a classe',
        );
        return false;
      }
    } catch (e) {
      _errorMessage.value = 'Erro ao adicionar classe: $e';
      LoggerUtil.error(_errorMessage.value, e);

      AppToast.error(
        'Erro',
        description: 'Ocorreu um erro ao adicionar a classe',
      );

      return false;
    } finally {
      _isAddingClass.value = false;
    }
  }

  // Remover uma classe
  Future<bool> removeClass(String className) async {
    try {
      final success = await _datasetService.removeClass(datasetId, className);

      if (success) {
        // Atualizar o dataset e a distribuição de classes
        await loadDataset();

        // Notificar sucesso
        AppToast.success(
          'Sucesso',
          description: 'Classe "$className" removida com sucesso!',
        );

        return true;
      } else {
        AppToast.error(
          'Erro',
          description: 'Não foi possível remover a classe',
        );
        return false;
      }
    } catch (e) {
      _errorMessage.value = 'Erro ao remover classe: $e';
      LoggerUtil.error(_errorMessage.value, e);

      AppToast.error(
        'Erro',
        description: 'Ocorreu um erro ao remover a classe',
      );

      return false;
    }
  }

  // Atualizar o dataset
  Future<Dataset?> updateDataset() async {
    if (_newClassName.value.trim().isEmpty) {
      AppToast.warning(
        'Aviso',
        description: 'O nome do dataset não pode estar vazio',
      );
      return null;
    }

    _isLoading.value = true;
    _errorMessage.value = '';

    try {
      final updatedDataset = await _datasetService.updateDataset(
        id: datasetId,
        name: _newClassName.value.trim(),
      );

      if (updatedDataset != null) {
        // Atualizar o dataset local
        _dataset.value = updatedDataset;

        // Atualizar a distribuição de classes
        await loadClassDistribution();

        // Notificar sucesso
        AppToast.success(
          'Sucesso',
          description: 'Dataset atualizado com sucesso!',
        );

        return updatedDataset;
      } else {
        _errorMessage.value = 'Erro ao atualizar dataset';
        LoggerUtil.error(_errorMessage.value);

        AppToast.error(
          'Erro',
          description: 'Não foi possível atualizar o dataset',
        );

        return null;
      }
    } catch (e) {
      _errorMessage.value = 'Erro ao atualizar dataset: $e';
      LoggerUtil.error(_errorMessage.value, e);

      AppToast.error(
        'Erro',
        description: 'Ocorreu um erro ao atualizar o dataset',
      );

      return null;
    } finally {
      _isLoading.value = false;
    }
  }

  // Definir o nome da nova classe
  void setNewClassName(String value) {
    _newClassName.value = value;
  }

  // Alternar estado de adição de classe
  void toggleAddingClass() {
    _isAddingClass.value = !_isAddingClass.value;

    if (!_isAddingClass.value) {
      // Limpar o campo quando fechamos o formulário
      _newClassName.value = '';
    }
  }

  // Refresh de todas as informações
  Future<void> refreshDataset() async {
    await loadDataset();
  }

  // Refresh apenas das imagens
  Future<void> refreshImages() async {
    await loadImages(reset: true);
  }

  // Remover uma imagem do dataset
  Future<bool> removeImage(int imageId) async {
    try {
      final success =
          await _datasetService.removeImageFromDataset(datasetId, imageId);

      if (success) {
        AppToast.success(
          'Sucesso',
          description: 'Imagem removida do dataset com sucesso!',
        );

        // Atualizar lista de imagens e estatísticas
        refreshImages();
        loadStatistics();

        return true;
      } else {
        AppToast.error(
          'Erro',
          description: 'Não foi possível remover a imagem do dataset',
        );
        return false;
      }
    } catch (e) {
      LoggerUtil.error('Erro ao remover imagem do dataset', e);
      AppToast.error(
        'Erro',
        description: 'Ocorreu um erro ao remover a imagem',
      );
      return false;
    }
  }

  // Callback após vincular imagens da galeria ao dataset
  void onImagesLinkedFromGallery(int count) {
    // Atualizar contagens e estatísticas
    refreshImages();
    loadStatistics();
    loadClassDistribution();
  }
}
