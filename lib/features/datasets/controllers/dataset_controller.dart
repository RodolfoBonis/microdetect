import 'dart:async';

import 'package:get/get.dart';
import 'dart:developer' as developer;
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';
import 'package:microdetect/features/datasets/services/dataset_service.dart';
import 'package:microdetect/design_system/app_toast.dart';
import 'package:microdetect/features/shared/events/app_event.dart';
import 'package:microdetect/features/shared/events/event_bus.dart';

class DatasetController extends GetxController {
  // Injeções de dependência
  final DatasetService _datasetService = Get.find<DatasetService>(tag: 'datasetService');

  // Estado observável
  final Rx<List<Dataset>> _datasets = Rx<List<Dataset>>([]);
  final RxBool _isLoading = false.obs;
  final RxString _errorMessage = ''.obs;
  final RxString _searchQuery = ''.obs;
  late StreamSubscription<EventData> event;

  // Getters para estado observável
  List<Dataset> get datasets => _datasets.value;
  bool get isLoading => _isLoading.value;
  String get errorMessage => _errorMessage.value;
  String get searchQuery => _searchQuery.value;

  @override
  void onInit() {
    developer.log('DatasetController - onInit()', name: 'DatasetController');
    listenRefreshDashboard();
    fetchDatasets();
    super.onInit();
  }



  void listenRefreshDashboard() {
    developer.log('HomeController - listenRefreshDashboard()', name: 'HomeController');
    // Ouvir eventos de atualização do dashboard
    event = EventBus.to.on(AppEvent.refresh, (data) {
      fetchDatasets();
    });
  }

  // Buscar todos os datasets
  Future<void> fetchDatasets() async {
    developer.log('DatasetController - fetchDatasets()', name: 'DatasetController');
    _isLoading.value = true;
    _errorMessage.value = '';

    try {
      final fetchedDatasets = await _datasetService.getDatasets();

      // Ordenar por data de atualização (mais recente primeiro)
      fetchedDatasets.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
      
      _datasets.value = fetchedDatasets;
      developer.log('DatasetController - ${fetchedDatasets.length} datasets carregados', name: 'DatasetController');
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

  // Definir consulta de pesquisa
  void setSearchQuery(String query) {
    _searchQuery.value = query.toLowerCase();
  }

  // Obter datasets filtrados pela consulta de pesquisa
  List<Dataset> getFilteredDatasets() {
    final query = _searchQuery.value;
    if (query.isEmpty) {
      return datasets.toList();
    }
    
    return datasets.where((dataset) {
      final nameMatch = dataset.name.toLowerCase().contains(query);
      final descMatch = dataset.description?.toLowerCase().contains(query) ?? false;
      final classMatch = dataset.classes.any((cls) => cls.toLowerCase().contains(query));
      
      return nameMatch || descMatch || classMatch;
    }).toList();
  }

  // Limpar consulta de pesquisa
  void clearSearchQuery() {
    _searchQuery.value = '';
  }

  @override
  void onClose() {
    event.cancel();
    super.onClose();
  }
} 