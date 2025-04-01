import 'dart:async';

import 'package:get/get.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/design_system/app_toast.dart';

import '../models/hyperparameter_search.dart';
import '../services/training_service.dart';
import 'training_controller.dart';

/// Controller para gerenciar busca de hiperparâmetros
class HyperparameterSearchController extends GetxController {
  /// Serviço de treinamento
  final TrainingService _trainingService = Get.find<TrainingService>();

  /// Controller de treinamento
  final TrainingController _trainingController = Get.find<TrainingController>();

  /// Lista de buscas de hiperparâmetros
  final RxList<HyperparamSearch> searches = <HyperparamSearch>[].obs;

  /// Busca selecionada
  final Rx<HyperparamSearch?> selectedSearch = Rx<HyperparamSearch?>(null);

  /// Indicador de carregamento
  final RxBool isLoading = false.obs;

  /// Indicador de erro
  final RxString errorMessage = ''.obs;

  /// Dados atuais de progresso via WebSocket
  final Rx<Map<String, dynamic>> currentProgress = Rx<Map<String, dynamic>>({});

  /// Status da busca atual
  final RxString searchStatus = ''.obs;

  /// Tentativas realizadas
  final RxInt currentIteration = 0.obs;

  /// Total de iterações
  final RxInt totalIterations = 0.obs;

  /// Melhores parâmetros encontrados
  final Rx<Map<String, dynamic>?> bestParams = Rx<Map<String, dynamic>?>(null);

  /// Melhores métricas encontradas
  final Rx<Map<String, dynamic>?> bestMetrics = Rx<Map<String, dynamic>?>(null);

  /// Lista de tentativas com parâmetros e métricas
  final RxList<Map<String, dynamic>> trialsList = <Map<String, dynamic>>[].obs;

  /// ID da sessão de treinamento final (após busca concluída)
  final RxInt finalModelId = 0.obs;

  /// Cancellable das streams
  StreamSubscription? _progressSubscription;

  /// Dataset ID para filtrar
  final Rx<int?> filterDatasetId = Rx<int?>(null);

  /// Status para filtrar
  final RxString filterStatus = ''.obs;

  /// Indicador de renovação automática
  final RxBool autoRefresh = true.obs;

  /// Timer para auto-refresh
  Timer? _refreshTimer;

  /// Obtém uma instância global (singleton)
  static HyperparameterSearchController get to => Get.find<HyperparameterSearchController>();

  @override
  void onInit() {
    super.onInit();

    // Iniciar temporizador para atualização automática
    _startRefreshTimer();

    // Carregar dados iniciais
    fetchHyperparamSearches();
  }

  @override
  void onClose() {
    _disposeStreams();
    _refreshTimer?.cancel();
    super.onClose();
  }

  /// Limpa as streams e inscrições
  void _disposeStreams() {
    _progressSubscription?.cancel();
    _progressSubscription = null;
    _trainingService.disconnectFromHyperparamSearchWebSocket();
  }

  /// Inicia o timer de atualização automática
  void _startRefreshTimer() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
      if (autoRefresh.value) {
        LoggerUtil.debug('Auto-refresh das buscas de hiperparâmetros');
        fetchHyperparamSearches();
      }
    });
  }

  /// Busca a lista de buscas de hiperparâmetros
  Future<void> fetchHyperparamSearches() async {
    try {
      isLoading.value = true;
      errorMessage.value = '';

      final searchResults = await _trainingService.getHyperparamSearches(
        datasetId: filterDatasetId.value,
        status: filterStatus.value.isNotEmpty ? filterStatus.value : null,
      );

      // Ordenar por data de criação (mais recentes primeiro)
      searchResults.sort((a, b) => b.createdAt.compareTo(a.createdAt));

      searches.assignAll(searchResults);
    } catch (e) {
      errorMessage.value = 'Erro ao carregar buscas: $e';
      LoggerUtil.error('Erro ao carregar buscas de hiperparâmetros: $e');
    } finally {
      isLoading.value = false;
    }
  }

  /// Define o filtro de dataset
  void setDatasetFilter(int? datasetId) {
    if (filterDatasetId.value != datasetId) {
      filterDatasetId.value = datasetId;
      fetchHyperparamSearches();
    }
  }

  /// Define o filtro de status
  void setStatusFilter(String status) {
    if (filterStatus.value != status) {
      filterStatus.value = status;
      fetchHyperparamSearches();
    }
  }

  /// Limpa todos os filtros
  void clearFilters() {
    filterDatasetId.value = null;
    filterStatus.value = '';
    fetchHyperparamSearches();
  }

  /// Alterna o auto-refresh
  void toggleAutoRefresh(bool value) {
    autoRefresh.value = value;

    if (value && _refreshTimer == null) {
      _startRefreshTimer();
    } else if (!value) {
      _refreshTimer?.cancel();
      _refreshTimer = null;
    }
  }

  /// Seleciona uma busca
  Future<void> selectHyperparamSearch(int searchId) async {
    try {
      isLoading.value = true;

      // Primeiro tenta encontrar na lista atual
      final search = searches.firstWhereOrNull((s) => s.id == searchId);

      // Se não encontrar, busca do servidor
      final hyperparamSearch = search ?? await _trainingService.getHyperparamSearch(searchId);

      if (hyperparamSearch != null) {
        selectedSearch.value = hyperparamSearch;

        // Carregar os dados de trials, se existirem
        if (hyperparamSearch.trialsData != null) {
          trialsList.assignAll(hyperparamSearch.trialsData!);
        } else {
          trialsList.clear();
        }

        // Atualizar melhores parâmetros e métricas
        bestParams.value = hyperparamSearch.bestParams;
        bestMetrics.value = hyperparamSearch.bestMetrics;

        // Atualizar contadores
        totalIterations.value = hyperparamSearch.iterations;
        currentIteration.value = hyperparamSearch.trialsData?.length ?? 0;

        // Se estiver em execução, conectar ao WebSocket
        if (hyperparamSearch.status == 'running') {
          connectToHyperparamSearchWebSocket(searchId);
        }

        // Se concluído, verificar se existe ID de sessão de treinamento
        if (hyperparamSearch.status == 'completed' && hyperparamSearch.trainingSessionId != null) {
          finalModelId.value = hyperparamSearch.trainingSessionId!;
        } else {
          finalModelId.value = 0;
        }
      } else {
        AppToast.error('Busca não encontrada');
      }
    } catch (e) {
      errorMessage.value = 'Erro ao carregar busca: $e';
      LoggerUtil.error('Erro ao carregar detalhes da busca: $e');
    } finally {
      isLoading.value = false;
    }
  }

  /// Inicia uma nova busca de hiperparâmetros
  Future<HyperparamSearch?> startHyperparamSearch(Map<String, dynamic> data) async {
    try {
      isLoading.value = true;

      final search = await _trainingService.startHyperparamSearch(data);

      // Adicionar à lista e atualizar
      searches.insert(0, search);

      // Selecionar a busca criada
      selectedSearch.value = search;

      // Conectar ao WebSocket para monitorar progresso
      connectToHyperparamSearchWebSocket(search.id);

      AppToast.success('Busca de hiperparâmetros iniciada com sucesso');

      return search;
    } catch (e) {
      errorMessage.value = 'Erro ao iniciar busca: $e';
      LoggerUtil.error('Erro ao iniciar busca de hiperparâmetros: $e');
      AppToast.error('Falha ao iniciar busca', description: e.toString());
      return null;
    } finally {
      isLoading.value = false;
    }
  }

  /// Conecta ao WebSocket para monitorar progresso
  void connectToHyperparamSearchWebSocket(int searchId) {
    try {
      // Limpar dados anteriores
      _resetHyperparamMetrics();

      // Fechar conexão anterior
      _disposeStreams();

      // Conectar ao WebSocket
      _trainingService.connectToHyperparamSearchWebSocket(searchId);

      // Inscrever-se para atualizações
      _progressSubscription = _trainingService.hyperparamProgressStream.listen(
        _handleHyperparamProgress,
        onError: (error) {
          LoggerUtil.error('Erro na stream de progresso de hiperparâmetros: $error');
        },
      );

      LoggerUtil.info('Conectado ao WebSocket para busca $searchId');
    } catch (e) {
      LoggerUtil.error('Erro ao conectar ao WebSocket: $e');
    }
  }

  /// Processa dados de progresso do WebSocket
  void _handleHyperparamProgress(Map<String, dynamic> data) {
    try {
      // Atualizar dados de progresso
      currentProgress.value = data;

      // Atualizar status
      if (data['status'] != null) {
        searchStatus.value = data['status'];
      }

      // Atualizar tentativas
      if (data['trials_data'] != null) {
        final trials = List<Map<String, dynamic>>.from(data['trials_data']);
        trialsList.assignAll(trials);
        currentIteration.value = trials.length;
      }

      // Atualizar melhores parâmetros e métricas
      if (data['best_params'] != null) {
        bestParams.value = Map<String, dynamic>.from(data['best_params']);
      }

      if (data['best_metrics'] != null) {
        bestMetrics.value = Map<String, dynamic>.from(data['best_metrics']);
      }

      // Se a busca foi concluída
      if (data['status'] == 'completed' && data['training_session_id'] != null) {
        finalModelId.value = data['training_session_id'];

        // Mostrar notificação
        AppToast.success('Busca de hiperparâmetros concluída');

        // Atualizar a busca selecionada
        if (selectedSearch.value != null) {
          selectedSearch.value = selectedSearch.value!.copyWith(
            status: 'completed',
            completedAt: DateTime.now(),
            bestParams: bestParams.value,
            bestMetrics: bestMetrics.value,
            trialsData: trialsList.toList(),
            trainingSessionId: finalModelId.value,
          );
        }
      }
    } catch (e) {
      LoggerUtil.error('Erro ao processar dados do WebSocket: $e');
    }
  }

  /// Reinicia as métricas de busca
  void _resetHyperparamMetrics() {
    currentProgress.value = {};
    searchStatus.value = '';
    currentIteration.value = 0;
    totalIterations.value = 0;
    bestParams.value = null;
    bestMetrics.value = null;
    trialsList.clear();
    finalModelId.value = 0;
  }

  /// Inicia um treinamento usando os melhores hiperparâmetros
  Future<bool> startTrainingWithBestParams() async {
    try {
      if (selectedSearch.value == null || bestParams.value == null) {
        AppToast.error('Não há parâmetros disponíveis para treinamento');
        return false;
      }

      // Preparar dados para treinamento
      final trainData = {
        'name': 'Modelo com hiperparâmetros otimizados para ${selectedSearch.value!.name}',
        'model_type': bestParams.value!['model_type'] ?? 'yolov8',
        'model_version': bestParams.value!['model_size'] ?? 'n',
        'dataset_id': selectedSearch.value!.datasetId,
        'description': 'Modelo criado a partir da busca de hiperparâmetros #${selectedSearch.value!.id}',
        'hyperparameters': Map<String, dynamic>.from(bestParams.value!),
      };

      // Iniciar treinamento
      final session = await _trainingController.startTraining(trainData);

      return session != null;
    } catch (e) {
      LoggerUtil.error('Erro ao iniciar treinamento com melhores parâmetros: $e');
      AppToast.error('Falha ao iniciar treinamento', description: e.toString());
      return false;
    }
  }

  /// Visualiza o modelo treinado
  void viewFinalModel() {
    if (finalModelId.value > 0) {
      _trainingController.selectTrainingSession(finalModelId.value);

      // Navegar para a página de detalhes do treinamento
      Get.toNamed('/root/training/details/${finalModelId.value}');
    } else {
      AppToast.warning('Modelo final não disponível');
    }
  }
}