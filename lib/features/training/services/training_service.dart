import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:microdetect/core/services/api_service.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../models/hyperparameter_search.dart';
import '../models/training_session.dart';
import '../models/training_report.dart';

/// Serviço para gerenciar a comunicação com a API relacionada a treinamento
/// e busca de hiperparâmetros
class TrainingService extends ApiService {
  /// StreamController para o progresso de treinamento via WebSocket
  final _trainingProgressController = StreamController<Map<String, dynamic>>.broadcast();

  /// StreamController para o progresso de busca de hiperparâmetros via WebSocket
  final _hyperparamProgressController = StreamController<Map<String, dynamic>>.broadcast();

  /// Canais WebSocket ativos
  WebSocketChannel? _trainingWsChannel;
  WebSocketChannel? _hyperparamWsChannel;

  /// Stream de progresso de treinamento
  Stream<Map<String, dynamic>> get trainingProgressStream => _trainingProgressController.stream;

  /// Stream de progresso de busca de hiperparâmetros
  Stream<Map<String, dynamic>> get hyperparamProgressStream => _hyperparamProgressController.stream;

  @override
  void onInit() {
    super.onInit();
    // Log after initialization is complete, not during build
    LoggerUtil.debug('TrainingService inicializado'); // Use debug instead of info to avoid toast
  }

  @override
  void onClose() {
    _disposeWebSockets();
    _trainingProgressController.close();
    _hyperparamProgressController.close();
    super.onClose();
  }

  /// Fecha os websockets
  void _disposeWebSockets() {
    _trainingWsChannel?.sink.close();
    _hyperparamWsChannel?.sink.close();
    _trainingWsChannel = null;
    _hyperparamWsChannel = null;
  }

  /// ==========================================================================
  /// Métodos para busca de hiperparâmetros
  /// ==========================================================================

  /// Inicia uma nova busca de hiperparâmetros
  Future<HyperparamSearch> startHyperparamSearch(Map<String, dynamic> data) async {
    try {
      if (!isApiInitialized) {
        throw Exception('API não inicializada');
      }

      final response = await post<Map<String, dynamic>>(
        '/api/v1/hyperparams/',
        data: data,
        options: Options(contentType: 'application/json'),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final searchData = response.data?['data'];
        if (searchData != null) {
          return HyperparamSearch.fromJson(searchData);
        } else {
          throw Exception('Dados de retorno inválidos');
        }
      } else {
        throw Exception('Falha ao iniciar busca de hiperparâmetros: ${response.statusCode}');
      }
    } catch (e) {
      LoggerUtil.error('Erro ao iniciar busca de hiperparâmetros: $e');
      rethrow;
    }
  }

  /// Obtém a lista de buscas de hiperparâmetros
  Future<List<HyperparamSearch>> getHyperparamSearches({
    int? datasetId,
    String? status,
  }) async {
    try {
      if (!isApiInitialized) {
        return [];
      }

      final queryParams = <String, dynamic>{};
      if (datasetId != null) queryParams['dataset_id'] = datasetId.toString();
      if (status != null) queryParams['status'] = status;

      final response = await get<Map<String, dynamic>>(
        '/api/v1/hyperparams/',
        queryParameters: queryParams,
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data?['data'] ?? [];
        return data.map((json) => HyperparamSearch.fromJson(json)).toList();
      } else {
        LoggerUtil.warning('Falha ao obter lista de buscas: ${response.statusCode}');
        return [];
      }
    } catch (e) {
      LoggerUtil.error('Erro ao obter buscas de hiperparâmetros: $e');
      return [];
    }
  }

  /// Obtém detalhes de uma busca específica
  Future<HyperparamSearch?> getHyperparamSearch(int searchId) async {
    try {
      if (!isApiInitialized) {
        return null;
      }

      final response = await get<Map<String, dynamic>>(
        '/api/v1/hyperparams/$searchId/',
      );

      if (response.statusCode == 200) {
        final data = response.data?['data'];
        if (data != null) {
          return HyperparamSearch.fromJson(data);
        }
      }

      return null;
    } catch (e) {
      LoggerUtil.error('Erro ao obter detalhes da busca: $e');
      return null;
    }
  }

  /// Conecta ao WebSocket para monitorar o progresso da busca
  void connectToHyperparamSearchWebSocket(int searchId) {
    try {
      // Fechar conexão anterior se existir
      _hyperparamWsChannel?.sink.close();

      final wsUrl = 'ws://${baseUrl.replaceFirst('http://', '')}/api/v1/hyperparams/ws/$searchId';
      LoggerUtil.debug('Conectando ao WebSocket: $wsUrl');

      _hyperparamWsChannel = WebSocketChannel.connect(Uri.parse(wsUrl));

      _hyperparamWsChannel!.stream.listen(
            (message) {
          try {
            final data = jsonDecode(message);
            _hyperparamProgressController.add(data);
          } catch (e) {
            LoggerUtil.error('Erro ao processar mensagem do WebSocket: $e');
          }
        },
        onDone: () {
          LoggerUtil.info('Conexão WebSocket fechada para busca de hiperparâmetros');
        },
        onError: (error) {
          LoggerUtil.error('Erro na conexão WebSocket para busca de hiperparâmetros: $error');
        },
      );
    } catch (e) {
      LoggerUtil.error('Erro ao conectar ao WebSocket: $e');
    }
  }

  /// Desconecta do WebSocket de busca de hiperparâmetros
  void disconnectFromHyperparamSearchWebSocket() {
    _hyperparamWsChannel?.sink.close();
    _hyperparamWsChannel = null;
  }

  /// ==========================================================================
  /// Métodos para treinamento de modelos
  /// ==========================================================================

  /// Inicia um novo treinamento
  Future<TrainingSession> startTraining(Map<String, dynamic> data) async {
    try {
      if (!isApiInitialized) {
        throw Exception('API não inicializada');
      }

      final response = await post<Map<String, dynamic>>(
        '/api/v1/training/',
        data: data,
        options: Options(contentType: 'application/json'),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final sessionData = response.data?['data'];
        if (sessionData != null) {
          return TrainingSession.fromJson(sessionData);
        } else {
          throw Exception('Dados de retorno inválidos');
        }
      } else {
        throw Exception('Falha ao iniciar treinamento: ${response.statusCode}');
      }
    } catch (e) {
      LoggerUtil.error('Erro ao iniciar treinamento: $e');
      rethrow;
    }
  }

  /// Obtém a lista de sessões de treinamento
  Future<List<TrainingSession>> getTrainingSessions({
    int? datasetId,
    String? status,
  }) async {
    try {
      if (!isApiInitialized) {
        return [];
      }

      final queryParams = <String, dynamic>{};
      if (datasetId != null) queryParams['dataset_id'] = datasetId.toString();
      if (status != null) queryParams['status'] = status;

      final response = await get<Map<String, dynamic>>(
        '/api/v1/training/',
        queryParameters: queryParams,
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data?['data'] ?? [];
        return data.map((json) => TrainingSession.fromJson(json)).toList();
      } else {
        LoggerUtil.warning('Falha ao obter lista de sessões: ${response.statusCode}');
        return [];
      }
    } catch (e) {
      LoggerUtil.error('Erro ao obter sessões de treinamento: $e');
      return [];
    }
  }

  /// Obtém detalhes de uma sessão específica
  Future<TrainingSession?> getTrainingSession(int sessionId) async {
    try {
      if (!isApiInitialized) {
        return null;
      }

      final response = await get<Map<String, dynamic>>(
        '/api/v1/training/$sessionId/',
      );

      if (response.statusCode == 200) {
        final data = response.data?['data'];
        if (data != null) {
          return TrainingSession.fromJson(data);
        }
      }

      return null;
    } catch (e) {
      LoggerUtil.error('Erro ao obter detalhes da sessão: $e');
      return null;
    }
  }

  /// Obtém o relatório de treinamento
  Future<TrainingReport?> getTrainingReport(int sessionId) async {
    try {
      if (!isApiInitialized) {
        return null;
      }

      final response = await get<Map<String, dynamic>>(
        '/api/v1/training/$sessionId/report/',
      );

      if (response.statusCode == 200) {
        final data = response.data?['data'];
        if (data != null) {
          return TrainingReport.fromJson(data);
        }
      }

      return null;
    } catch (e) {
      LoggerUtil.error('Erro ao obter relatório de treinamento: $e');
      return null;
    }
  }

  /// Conecta ao WebSocket para monitorar o progresso do treinamento
  void connectToTrainingWebSocket(int sessionId) {
    try {
      // Fechar conexão anterior se existir
      _trainingWsChannel?.sink.close();

      final wsUrl = 'ws://${baseUrl.replaceFirst('http://', '')}/api/v1/training/ws/$sessionId';
      LoggerUtil.debug('Conectando ao WebSocket: $wsUrl');

      _trainingWsChannel = WebSocketChannel.connect(Uri.parse(wsUrl));

      _trainingWsChannel!.stream.listen(
            (message) {
          try {
            final data = jsonDecode(message);
            _trainingProgressController.add(data);
          } catch (e) {
            LoggerUtil.error('Erro ao processar mensagem do WebSocket: $e');
          }
        },
        onDone: () {
          LoggerUtil.info('Conexão WebSocket fechada para treinamento');
        },
        onError: (error) {
          LoggerUtil.error('Erro na conexão WebSocket para treinamento: $error');
        },
      );
    } catch (e) {
      LoggerUtil.error('Erro ao conectar ao WebSocket: $e');
    }
  }

  /// Desconecta do WebSocket de treinamento
  void disconnectFromTrainingWebSocket() {
    _trainingWsChannel?.sink.close();
    _trainingWsChannel = null;
  }

  /// Cancela um treinamento em andamento
  Future<bool> cancelTraining(int sessionId) async {
    try {
      if (!isApiInitialized) {
        return false;
      }

      final response = await post<Map<String, dynamic>>(
        '/api/v1/training/$sessionId/cancel/',
      );

      return response.statusCode == 200;
    } catch (e) {
      LoggerUtil.error('Erro ao cancelar treinamento: $e');
      return false;
    }
  }

  /// Pausa um treinamento em andamento
  Future<bool> pauseTraining(int sessionId) async {
    try {
      if (!isApiInitialized) {
        return false;
      }

      final response = await post<Map<String, dynamic>>(
        '/api/v1/training/$sessionId/pause/',
      );

      return response.statusCode == 200;
    } catch (e) {
      LoggerUtil.error('Erro ao pausar treinamento: $e');
      return false;
    }
  }

  /// Retoma um treinamento pausado
  Future<bool> resumeTraining(int sessionId) async {
    try {
      if (!isApiInitialized) {
        return false;
      }

      final response = await post<Map<String, dynamic>>(
        '/api/v1/training/$sessionId/resume/',
      );

      return response.statusCode == 200;
    } catch (e) {
      LoggerUtil.error('Erro ao retomar treinamento: $e');
      return false;
    }
  }
}