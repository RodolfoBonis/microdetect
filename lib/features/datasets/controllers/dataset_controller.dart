import 'package:get/get.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/features/datasets/models/class_distribution.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';
import 'package:microdetect/features/datasets/services/dataset_service.dart';
import 'package:microdetect/features/shared/events/event_manager.dart';
import 'package:microdetect/features/shared/events/screen_events.dart';
import 'package:microdetect/design_system/app_toast.dart';

class DatasetController extends GetxController {
  // Injeções de dependência
  final DatasetService _datasetService = Get.find<DatasetService>();

  // Estado observável
  final RxList<Dataset> _datasets = <Dataset>[].obs;
  final RxBool _isLoading = false.obs;
  final RxString _errorMessage = ''.obs;
  final RxBool _isGridView = true.obs;
  final RxString _searchQuery = ''.obs;

  // Lista de tipos de eventos registrados para limpeza
  final List<String> _registeredEvents = [];

  // Getters para estado observável
  List<Dataset> get datasets => _datasets;
  bool get isLoading => _isLoading.value;
  String get errorMessage => _errorMessage.value;
  bool get isGridView => _isGridView.value;
  String get searchQuery => _searchQuery.value;

  @override
  void onInit() {
    super.onInit();
    _setupEventListeners();
    fetchDatasets();
  }

  @override
  void onClose() {
    _unregisterEventListeners();
    super.onClose();
  }

  // Configurar escuta de eventos
  void _setupEventListeners() {
    _registerEventListener(ScreenEvents.refreshDatasets, _handleRefreshEvent);
  }

  // Registrar um listener e armazenar o tipo para limpeza futura
  void _registerEventListener(String eventType, Function(ScreenEvent) handler) {
    Get.events.addListener(eventType, handler);
    _registeredEvents.add(eventType);
  }

  // Cancelar todos os listeners registrados
  void _unregisterEventListeners() {
    for (final eventType in _registeredEvents) {
      Get.events.removeAllListenersForType(eventType);
    }
    _registeredEvents.clear();
  }

  // Handler para o evento de atualização
  void _handleRefreshEvent(ScreenEvent event) {
    fetchDatasets();
  }

  // Buscar todos os datasets
  Future<void> fetchDatasets() async {
    _isLoading.value = true;
    _errorMessage.value = '';

    try {
      final fetchedDatasets = await _datasetService.getDatasets();

      // Ordenar por data de atualização (mais recente primeiro)
      fetchedDatasets.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
      
      _datasets.assignAll(fetchedDatasets);
    } catch (e) {
      _errorMessage.value = 'Erro ao carregar datasets: $e';
      LoggerUtil.error(_errorMessage.value, e);
    } finally {
      _isLoading.value = false;
    }
  }

  // Criar um novo dataset
  Future<Dataset?> createDataset({
    required String name, 
    String? description,
    List<String> classes = const [],
  }) async {
    _isLoading.value = true;
    _errorMessage.value = '';

    try {
      final newDataset = await _datasetService.createDataset(
        name: name,
        description: description,
        classes: classes,
      );
      
      if (newDataset != null) {
        // Atualizar a lista de datasets
        await fetchDatasets();
        
        // Notificar sucesso
        AppToast.success(
          'Sucesso',
          description: 'Dataset criado com sucesso!',
        );
        
        return newDataset;
      } else {
        _errorMessage.value = 'Erro ao criar dataset';
        LoggerUtil.error(_errorMessage.value);
        
        AppToast.error(
          'Erro',
          description: 'Não foi possível criar o dataset',
        );
        
        return null;
      }
    } catch (e) {
      _errorMessage.value = 'Erro ao criar dataset: $e';
      LoggerUtil.error(_errorMessage.value, e);

      AppToast.error(
        'Erro',
        description: 'Ocorreu um erro ao criar o dataset',
      );
      
      return null;
    } finally {
      _isLoading.value = false;
    }
  }

  // Atualizar um dataset existente
  Future<Dataset?> updateDataset({
    required int id,
    String? name,
    String? description,
    List<String>? classes,
  }) async {
    _isLoading.value = true;
    _errorMessage.value = '';

    try {
      final updatedDataset = await _datasetService.updateDataset(
        id: id,
        name: name,
        description: description,
        classes: classes,
      );
      
      if (updatedDataset != null) {
        // Atualizar a lista de datasets
        await fetchDatasets();
        
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

  // Excluir um dataset
  Future<bool> deleteDataset(int id) async {
    _isLoading.value = true;
    _errorMessage.value = '';

    try {
      final success = await _datasetService.deleteDataset(id);
      
      if (success) {
        // Atualizar a lista de datasets
        await fetchDatasets();
        
        // Notificar sucesso
        AppToast.success(
          'Sucesso',
          description: 'Dataset excluído com sucesso!',
        );
        
        return true;
      } else {
        _errorMessage.value = 'Erro ao excluir dataset';
        LoggerUtil.error(_errorMessage.value);
        
        AppToast.error(
          'Erro',
          description: 'Não foi possível excluir o dataset',
        );
        
        return false;
      }
    } catch (e) {
      _errorMessage.value = 'Erro ao excluir dataset: $e';
      LoggerUtil.error(_errorMessage.value, e);

      AppToast.error(
        'Erro',
        description: 'Ocorreu um erro ao excluir o dataset',
      );
      
      return false;
    } finally {
      _isLoading.value = false;
    }
  }

  // Adicionar classe a um dataset
  Future<bool> addClass(int datasetId, String className) async {
    _isLoading.value = true;
    _errorMessage.value = '';

    try {
      final success = await _datasetService.addClass(datasetId, className);
      
      if (success) {
        // Atualizar a lista de datasets
        await fetchDatasets();
        
        // Notificar sucesso
        AppToast.success(
          'Sucesso',
          description: 'Classe adicionada com sucesso!',
        );
        
        return true;
      } else {
        _errorMessage.value = 'Erro ao adicionar classe';
        LoggerUtil.error(_errorMessage.value);
        
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
      _isLoading.value = false;
    }
  }

  // Remover classe de um dataset
  Future<bool> removeClass(int datasetId, String className) async {
    _isLoading.value = true;
    _errorMessage.value = '';

    try {
      final success = await _datasetService.removeClass(datasetId, className);
      
      if (success) {
        // Atualizar a lista de datasets
        await fetchDatasets();
        
        // Notificar sucesso
        AppToast.success(
          'Sucesso',
          description: 'Classe removida com sucesso!',
        );
        
        return true;
      } else {
        _errorMessage.value = 'Erro ao remover classe';
        LoggerUtil.error(_errorMessage.value);
        
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
    } finally {
      _isLoading.value = false;
    }
  }

  // Alternar entre visualização em grade e lista
  void toggleViewMode() {
    _isGridView.value = !_isGridView.value;
  }

  // Definir consulta de pesquisa
  void setSearchQuery(String query) {
    _searchQuery.value = query.toLowerCase();
  }

  // Obter datasets filtrados pela consulta de pesquisa
  List<Dataset> getFilteredDatasets() {
    if (_searchQuery.isEmpty) {
      return _datasets;
    }
    
    return _datasets.where((dataset) {
      final nameMatch = dataset.name.toLowerCase().contains(_searchQuery.value);
      final descMatch = dataset.description?.toLowerCase().contains(_searchQuery.value) ?? false;
      final classMatch = dataset.classes.any((cls) => cls.toLowerCase().contains(_searchQuery.value));
      
      return nameMatch || descMatch || classMatch;
    }).toList();
  }

  // Limpar consulta de pesquisa
  void clearSearchQuery() {
    _searchQuery.value = '';
  }
} 