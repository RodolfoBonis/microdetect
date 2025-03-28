import 'package:dio/dio.dart' as http;
import 'package:get/get.dart';
import 'package:get/get_connect/http/src/request/request.dart';
import '../enums/backend_status_enum.dart';
import '../utils/logger_util.dart';
import '../services/backend_service.dart';

abstract class ApiService extends GetxController {
  // Remove late keyword to initialize immediately
  final http.Dio _dio = _createDio();

  /// Base URL for API requests
  String get baseUrl => 'http://localhost:8000';

  /// Check if backend API is initialized and running
  bool get isApiInitialized => BackendService.to.status.value == BackendStatus.running;

  /// Provides access to the dio instance
  http.Dio get dio => _dio;

  // Create a static method to initialize Dio
  static http.Dio _createDio() {
    final dio = http.Dio(http.BaseOptions(
      baseUrl: 'http://localhost:8000',
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      sendTimeout: const Duration(seconds: 30),
      validateStatus: (status) => true, // Manual error handling
      followRedirects: true,             // Seguir redirecionamentos automaticamente
      maxRedirects: 5,                   // Máximo de redirecionamentos
    ));

    // Add logging interceptor
    dio.interceptors.add(http.InterceptorsWrapper(
        onRequest: (options, handler) {
          LoggerUtil.debug('ApiService - Request: ${options.method} ${options.path}');
          return handler.next(options);
        },
        onResponse: (response, handler) {
          LoggerUtil.debug('ApiService - Response: ${response.statusCode}');
          
          // Verificar se é um redirecionamento que não foi seguido automaticamente
          if (_isRedirectStatus(response.statusCode)) {
            LoggerUtil.debug('Recebido redirecionamento HTTP ${response.statusCode}');
          }
          
          return handler.next(response);
        },
        onError: (http.DioException e, handler) {
          LoggerUtil.error('ApiService - Error: ${e.message}');
          return handler.next(e);
        }
    ));

    return dio;
  }

  /// Verifica se o código de status é um redirecionamento
  static bool _isRedirectStatus(int? statusCode) {
    return statusCode != null && 
           (statusCode == 301 || statusCode == 302 || 
            statusCode == 303 || statusCode == 307 || 
            statusCode == 308);
  }

  /// Processa manualmente um redirecionamento se necessário
  Future<http.Response<T>> _handleRedirect<T>(http.Response<T> response) async {
    if (!_isRedirectStatus(response.statusCode)) {
      return response;
    }

    final location = response.headers['location'] ?? response.headers['Location'];
    if (location == null || location.isEmpty) {
      LoggerUtil.warning('Redirecionamento recebido mas sem cabeçalho Location');
      return response;
    }

    final String redirectUrl = location.first;
    LoggerUtil.debug('Seguindo redirecionamento para: $redirectUrl');
    
    // Criar uma nova requisição para o destino do redirecionamento
    final redirectResponse = await _dio.request<T>(
      redirectUrl,
      options: http.Options(
        method: response.requestOptions.method,
        headers: response.requestOptions.headers,
        contentType: response.requestOptions.contentType,
        responseType: response.requestOptions.responseType,
      ),
      data: response.requestOptions.data,
    );
    
    return redirectResponse;
  }

  @override
  void onInit() {
    // No need to initialize Dio here anymore
    super.onInit();
  }

  /// Executes a GET request with proper error handling
  Future<http.Response<T>> get<T>(
      String path, {
        Map<String, dynamic>? queryParameters,
        http.Options? options,
        http.CancelToken? cancelToken,
      }) async {
    try {
      if (!isApiInitialized) {
        throw Exception('API não inicializada');
      }

      final response = await dio.get<T>(
        path,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      
      // Tratar possível redirecionamento
      if (_isRedirectStatus(response.statusCode)) {
        return await _handleRedirect<T>(response);
      }
      
      return response;
    } catch (e) {
      LoggerUtil.error('Erro em GET $path: $e');
      rethrow;
    }
  }

  /// Executes a POST request with proper error handling
  Future<http.Response<T>> post<T>(
      String path, {
        dynamic data,
        Map<String, dynamic>? queryParameters,
        http.Options? options,
        http.CancelToken? cancelToken,
      }) async {
    try {
      if (!isApiInitialized) {
        throw Exception('API não inicializada');
      }

      final response = await dio.post<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      
      // Tratar possível redirecionamento
      if (_isRedirectStatus(response.statusCode)) {
        return await _handleRedirect<T>(response);
      }
      
      return response;
    } catch (e) {
      LoggerUtil.error('Erro em POST $path: $e');
      rethrow;
    }
  }

  /// Executes a DELETE request with proper error handling
  Future<http.Response<T>> delete<T>(
      String path, {
        dynamic data,
        Map<String, dynamic>? queryParameters,
        http.Options? options,
        http.CancelToken? cancelToken,
      }) async {
    try {
      if (!isApiInitialized) {
        throw Exception('API não inicializada');
      }

      final response = await dio.delete<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      
      // Tratar possível redirecionamento
      if (_isRedirectStatus(response.statusCode)) {
        return await _handleRedirect<T>(response);
      }
      
      return response;
    } catch (e) {
      LoggerUtil.error('Erro em DELETE $path: $e');
      rethrow;
    }
  }

  Future<http.Response<T>> put<T>(
      String path, {
        dynamic data,
        Map<String, dynamic>? queryParameters,
        http.Options? options,
        http.CancelToken? cancelToken,
      }) async {
    try {
      if (!isApiInitialized) {
        throw Exception('API não inicializada');
      }

      final response = await dio.put<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      
      // Tratar possível redirecionamento
      if (_isRedirectStatus(response.statusCode)) {
        return await _handleRedirect<T>(response);
      }
      
      return response;
    } catch (e) {
      LoggerUtil.error('Erro em PUT $path: $e');
      rethrow;
    }
  }

  Future<http.Response<T>> upload<T>(
      String path, {
        required http.FormData formData,
        Map<String, dynamic>? queryParameters,
        http.CancelToken? cancelToken,
        void Function(int, int)? onSendProgress,
      }) async {
    try {
      if (!isApiInitialized) {
        throw Exception('API não inicializada');
      }

      // Log mais detalhado para depuração
      LoggerUtil.debug('Iniciando upload para $path');
      LoggerUtil.debug('Conteúdo do FormData: ${formData.fields.length} campos, ${formData.files.length} arquivos');

      // Ajustar timeouts para uploads maiores
      final options = http.Options(
        contentType: 'multipart/form-data',
        headers: {
          'Accept': 'application/json',
          'Connection': 'keep-alive',
          'Content-Type': 'multipart/form-data',
        },
        sendTimeout: const Duration(minutes: 5),
        receiveTimeout: const Duration(minutes: 5),
      );

      try {
        final response = await dio.post<T>(
          path,
          data: formData,
          queryParameters: queryParameters,
          cancelToken: cancelToken,
          options: options,
          onSendProgress: onSendProgress,
        );

        // Verificar se há redirecionamento
        if (_isRedirectStatus(response.statusCode)) {
          LoggerUtil.debug('Redirecionamento detectado no upload (${response.statusCode})');
          
          final location = response.headers['location'] ?? response.headers['Location'];
          if (location != null && location.isNotEmpty) {
            final String redirectUrl = location.first;
            LoggerUtil.debug('Seguindo redirecionamento de upload para: $redirectUrl');
            
            // Criar uma cópia do FormData para o novo envio
            final copyFormData = http.FormData();
            
            // Copiar campos
            for (var field in formData.fields) {
              copyFormData.fields.add(field);
            }

            for (var file in formData.files) {
              try {
                if (file.value.filename != null) {
                  copyFormData.files.add(
                    MapEntry(
                      file.key,
                      http.MultipartFile.fromBytes(
                        await file.value.finalize().toBytes(),
                        filename: file.value.filename,
                        contentType: file.value.contentType,
                      ),
                    ),
                  );
                }
              } catch (e) {
                LoggerUtil.error('Erro ao recriar arquivo para redirecionamento: $e');
                // Continuar mesmo sem este arquivo
              }
            }
            
            // Fazer o novo upload para a URL de redirecionamento
            final redirectResponse = await dio.post<T>(
              redirectUrl,
              data: copyFormData,
              options: options,
              onSendProgress: (sent, total) {
                LoggerUtil.debug('Upload redirecionado progresso: $sent/$total bytes');
                onSendProgress?.call(sent, total);
              },
            );
            
            return redirectResponse;
          }
        }

        // Log detalhado da resposta
        if (response.statusCode != 200 && response.statusCode != 201) {
          LoggerUtil.warning('Upload falhou com código ${response.statusCode}');
          LoggerUtil.warning('Resposta: ${response.data}');
        } else {
          LoggerUtil.debug('Upload concluído com sucesso');
        }

        return response;
      } on http.DioException catch (dioError) {
        LoggerUtil.error('Erro Dio durante upload: ${dioError.type}');
        LoggerUtil.error('Mensagem: ${dioError.message}');

        if (dioError.response != null) {
          LoggerUtil.error('Código de status: ${dioError.response?.statusCode}');
          LoggerUtil.error('Resposta: ${dioError.response?.data}');
        }

        if (dioError.type == http.DioExceptionType.connectionTimeout) {
          throw Exception('Tempo limite de conexão excedido durante o upload');
        } else if (dioError.type == http.DioExceptionType.sendTimeout) {
          throw Exception('Tempo limite de envio excedido durante o upload');
        } else if (dioError.type == http.DioExceptionType.receiveTimeout) {
          throw Exception('Tempo limite de recebimento excedido durante o upload');
        }

        rethrow;
      }
    } catch (e) {
      LoggerUtil.error('Erro em upload $path: $e');
      rethrow;
    }
  }
}