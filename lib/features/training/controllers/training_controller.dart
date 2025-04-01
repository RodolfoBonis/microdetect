import 'dart:async';

import 'package:get/get.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/design_system/app_toast.dart';

import '../models/training_report.dart';
import '../models/training_session.dart';
import '../services/training_service.dart';

/// Controller para gerenciar treinamento de modelos
class TrainingController extends GetxController {
  /// Serviço de treinamento
  final TrainingService _trainingService = Get.find<TrainingService>();

  /// Lista de sessões de treinamento
  final RxList<TrainingSession> trainingSessions = <TrainingSession>[].obs;

  /// Sessão de treinamento selecionada
  final Rx<TrainingSession?> selectedSession = Rx<TrainingSession?>(null);

  /// Relatório de treinamento
  final Rx<TrainingReport?> trainingReport = Rx<TrainingReport?>(null);

  /// Indicador de carregamento
  final RxBool isLoading = false.obs;

  /// Indicador de erro
  final RxString errorMessage = ''.obs;

  /// Métricas atuais de treinamento (para WebSocket)
  final Rx<Map<String, dynamic>> currentMetrics = Rx<Map<String, dynamic>>({});

  /// Status do treinamento em execução
  final RxString trainingStatus = ''.obs;

  /// Época atual
  final RxInt currentEpoch = 0.obs;

  /// Total de épocas
  final RxInt totalEpochs = 0.obs;

  /// Histórico de loss
  final RxList<double> lossHistory = <double>[].obs;

  /// Histórico de map50
  final RxList<double> map50History = <double>[].obs;

  /// Histórico de precisão
  final RxList<double> precisionHistory = <double>[].obs;

  /// Histórico de recall
  final RxList<double> recallHistory = <double>[].obs;

  /// Uso de CPU
  final RxDouble cpuUsage = 0.0.obs;

  /// Uso de memória
  final RxDouble memoryUsage = 0.0.obs;

  /// Uso de GPU
  final RxDouble gpuUsage = 0.0.obs;

  /// Cancellable das streams
  StreamSubscription? _progressSubscription;

  /// Dataset ID para filtrar
  final Rx<int?> filterDatasetId = Rx<int?>(null);

  /// Seletor de status para filtrar
  final RxString filterStatus = ''.obs;

  /// Indicador de renovação automática
  final RxBool autoRefresh = true.obs;

  /// Timer para auto-refresh
  Timer? _refreshTimer;

  /// Obtém uma instância global (singleton)
  static TrainingController get to => Get.find<TrainingController>();

  @override
  void onInit() {
    super.onInit();

    // Iniciar temporizador para atualização automática
    _startRefreshTimer();

    // Carregar dados iniciais
    fetchTrainingSessions();
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
    _trainingService.disconnectFromTrainingWebSocket();
  }

  /// Inicia o timer de atualização automática
  void _startRefreshTimer() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
      if (autoRefresh.value) {
        LoggerUtil.debug('Auto-refresh das sessões de treinamento');
        fetchTrainingSessions();
      }
    });
  }

  /// Busca a lista de sessões de treinamento
  Future<void> fetchTrainingSessions() async {
    try {
      isLoading.value = true;
      errorMessage.value = '';

      final sessions = await _trainingService.getTrainingSessions(
        datasetId: filterDatasetId.value,
        status: filterStatus.value.isNotEmpty ? filterStatus.value : null,
      );

      // Ordenar por data de criação (mais recentes primeiro)
      sessions.sort((a, b) => b.createdAt.compareTo(a.createdAt));

      trainingSessions.assignAll(sessions);
    } catch (e) {
      errorMessage.value = 'Erro ao carregar sessões: $e';
      LoggerUtil.error('Erro ao carregar sessões de treinamento: $e');
    } finally {
      isLoading.value = false;
    }
  }

  /// Define o filtro de dataset
  void setDatasetFilter(int? datasetId) {
    if (filterDatasetId.value != datasetId) {
      filterDatasetId.value = datasetId;
      fetchTrainingSessions();
    }
  }

  /// Define o filtro de status
  void setStatusFilter(String status) {
    if (filterStatus.value != status) {
      filterStatus.value = status;
      fetchTrainingSessions();
    }
  }

  /// Limpa todos os filtros
  void clearFilters() {
    filterDatasetId.value = null;
    filterStatus.value = '';
    fetchTrainingSessions();
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

  /// Seleciona uma sessão de treinamento
  Future<void> selectTrainingSession(int sessionId) async {
    try {
      isLoading.value = true;

      // Primeiro tenta encontrar na lista atual
      final session = trainingSessions.firstWhereOrNull((s) => s.id == sessionId);

      // Se não encontrar, busca do servidor
      final trainingSession = session ?? await _trainingService.getTrainingSession(sessionId);

      if (trainingSession != null) {
        selectedSession.value = trainingSession;

        // Se estiver em execução, conectar ao WebSocket
        if (trainingSession.status == 'running') {
          connectToTrainingWebSocket(sessionId);
        }

        // Se estiver concluído, carregar relatório
        if (trainingSession.status == 'completed') {
          await fetchTrainingReport(sessionId);
        }
      } else {
        AppToast.error('Sessão não encontrada');
      }
    } catch (e) {
      errorMessage.value = 'Erro ao carregar sessão: $e';
      LoggerUtil.error('Erro ao carregar detalhes da sessão: $e');
    } finally {
      isLoading.value = false;
    }
  }

  /// Busca o relatório de treinamento
  Future<void> fetchTrainingReport(int sessionId) async {
    try {
      isLoading.value = true;

      final report = await _trainingService.getTrainingReport(sessionId);

      if (report != null) {
        trainingReport.value = report;
      } else {
        trainingReport.value = null;
        AppToast.warning('Relatório não disponível');
      }
    } catch (e) {
      trainingReport.value = null;
      errorMessage.value = 'Erro ao carregar relatório: $e';
      LoggerUtil.error('Erro ao carregar relatório de treinamento: $e');
    } finally {
      isLoading.value = false;
    }
  }

  /// Inicia um novo treinamento
  Future<TrainingSession?> startTraining(Map<String, dynamic> data) async {
    try {
      isLoading.value = true;

      final session = await _trainingService.startTraining(data);

      // Adicionar à lista e atualizar
      trainingSessions.insert(0, session);

      // Selecionar a sessão criada
      selectedSession.value = session;

      // Conectar ao WebSocket para monitorar progresso
      connectToTrainingWebSocket(session.id);

      AppToast.success('Treinamento iniciado com sucesso');

      return session;
    } catch (e) {
      errorMessage.value = 'Erro ao iniciar treinamento: $e';
      LoggerUtil.error('Erro ao iniciar treinamento: $e');
      AppToast.error('Falha ao iniciar treinamento', description: e.toString());
      return null;
    } finally {
      isLoading.value = false;
    }
  }

  /// Conecta ao WebSocket para monitorar progresso
  void connectToTrainingWebSocket(int sessionId) {
    try {
      // Limpar históricos
      _resetTrainingMetrics();

      // Fechar conexão anterior
      _disposeStreams();

      // Conectar ao WebSocket
      _trainingService.connectToTrainingWebSocket(sessionId);

      // Inscrever-se para atualizações
      _progressSubscription = _trainingService.trainingProgressStream.listen(
        _handleTrainingProgress,
        onError: (error) {
          LoggerUtil.error('Erro na stream de progresso de treinamento: $error');
        },
      );

      LoggerUtil.info('Conectado ao WebSocket para sessão $sessionId');
    } catch (e) {
      LoggerUtil.error('Erro ao conectar ao WebSocket: $e');
    }
  }

  /// Processa dados de progresso do WebSocket
  void _handleTrainingProgress(Map<String, dynamic> data) {
    try {
      // Verificar se é um relatório final
      if (data['type'] == 'final_report') {
        LoggerUtil.info('Relatório final recebido');

        // Atualizar relatório
        if (data['data'] != null) {
          trainingReport.value = TrainingReport.fromJson(data['data']);
        }

        // Atualizar status da sessão
        if (selectedSession.value != null) {
          selectedSession.value = selectedSession.value!.copyWith(
            status: 'completed',
            completedAt: DateTime.now(),
          );
        }

        // Desconectar do WebSocket
        _disposeStreams();

        // Mostrar notificação
        AppToast.success('Treinamento concluído');

        return;
      }

      // Atualizar métricas de progresso
      currentMetrics.value = data;

      // Atualizar status
      if (data['status'] != null) {
        trainingStatus.value = data['status'];
      }

      // Processar métricas
      if (data['metrics'] != null) {
        _processTrainingMetrics(data);
      }

      // Atualizar sessão selecionada com as métricas atuais
      if (selectedSession.value != null) {
        selectedSession.value = selectedSession.value!.copyWith(
          metrics: data,
          status: data['status'] ?? selectedSession.value!.status,
        );
      }
    } catch (e) {
      LoggerUtil.error('Erro ao processar dados do WebSocket: $e');
    }
  }

  /// Processa métricas específicas de treinamento
  void _processTrainingMetrics(Map<String, dynamic> data) {
    if (data['current_epoch'] != null && data['total_epochs'] != null) {
      currentEpoch.value = data['current_epoch'];
      totalEpochs.value = data['total_epochs'];
    }

    // Processar métricas
    final metrics = data['metrics'];
    if (metrics != null) {
      // Loss
      if (metrics['loss'] != null) {
        final loss = metrics['loss'] as double;
        lossHistory.add(loss);
      }

      // mAP50
      if (metrics['map50'] != null) {
        final map50 = metrics['map50'] as double;
        map50History.add(map50);
      }

      // Precisão
      if (metrics['precision'] != null) {
        final precision = metrics['precision'] as double;
        precisionHistory.add(precision);
      }

      // Recall
      if (metrics['recall'] != null) {
        final recall = metrics['recall'] as double;
        recallHistory.add(recall);
      }

      // Uso de recursos
      if (metrics['resources'] != null) {
        final resources = metrics['resources'];

        if (resources['cpu_percent'] != null) {
          cpuUsage.value = resources['cpu_percent'];
        }

        if (resources['memory_percent'] != null) {
          memoryUsage.value = resources['memory_percent'];
        }

        if (resources['gpu_percent'] != null) {
          gpuUsage.value = resources['gpu_percent'];
        }
      }
    }
  }

  /// Reinicia as métricas de treinamento
  void _resetTrainingMetrics() {
    currentMetrics.value = {};
    trainingStatus.value = '';
    currentEpoch.value = 0;
    totalEpochs.value = 0;
    lossHistory.clear();
    map50History.clear();
    precisionHistory.clear();
    recallHistory.clear();
    cpuUsage.value = 0.0;
    memoryUsage.value = 0.0;
    gpuUsage.value = 0.0;
  }

  /// Cancela um treinamento em andamento
  Future<bool> cancelTraining(int sessionId) async {
    try {
      isLoading.value = true;

      final success = await _trainingService.cancelTraining(sessionId);

      if (success) {
        // Atualizar sessão na lista
        final index = trainingSessions.indexWhere((s) => s.id == sessionId);
        if (index >= 0) {
          trainingSessions[index] = trainingSessions[index].copyWith(
            status: 'cancelled',
          );
        }

        // Atualizar sessão selecionada
        if (selectedSession.value?.id == sessionId) {
          selectedSession.value = selectedSession.value!.copyWith(
            status: 'cancelled',
          );
        }

        AppToast.success('Treinamento cancelado');
      } else {
        AppToast.error('Falha ao cancelar treinamento');
      }

      return success;
    } catch (e) {
      LoggerUtil.error('Erro ao cancelar treinamento: $e');
      AppToast.error('Erro ao cancelar treinamento', description: e.toString());
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  /// Pausa um treinamento em andamento
  Future<bool> pauseTraining(int sessionId) async {
    try {
      isLoading.value = true;

      final success = await _trainingService.pauseTraining(sessionId);

      if (success) {
        // Atualizar sessão na lista
        final index = trainingSessions.indexWhere((s) => s.id == sessionId);
        if (index >= 0) {
          trainingSessions[index] = trainingSessions[index].copyWith(
            status: 'paused',
          );
        }

        // Atualizar sessão selecionada
        if (selectedSession.value?.id == sessionId) {
          selectedSession.value = selectedSession.value!.copyWith(
            status: 'paused',
          );
        }

        AppToast.success('Treinamento pausado');
      } else {
        AppToast.error('Falha ao pausar treinamento');
      }

      return success;
    } catch (e) {
      LoggerUtil.error('Erro ao pausar treinamento: $e');
      AppToast.error('Erro ao pausar treinamento', description: e.toString());
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  /// Retoma um treinamento pausado
  Future<bool> resumeTraining(int sessionId) async {
    try {
      isLoading.value = true;

      final success = await _trainingService.resumeTraining(sessionId);

      if (success) {
        // Atualizar sessão na lista
        final index = trainingSessions.indexWhere((s) => s.id == sessionId);
        if (index >= 0) {
          trainingSessions[index] = trainingSessions[index].copyWith(
            status: 'running',
          );
        }

        // Atualizar sessão selecionada
        if (selectedSession.value?.id == sessionId) {
          selectedSession.value = selectedSession.value!.copyWith(
            status: 'running',
          );

          // Reconectar ao WebSocket
          connectToTrainingWebSocket(sessionId);
        }

        AppToast.success('Treinamento retomado');
      } else {
        AppToast.error('Falha ao retomar treinamento');
      }

      return success;
    } catch (e) {
      LoggerUtil.error('Erro ao retomar treinamento: $e');
      AppToast.error('Erro ao retomar treinamento', description: e.toString());
      return false;
    } finally {
      isLoading.value = false;
    }
  }
}