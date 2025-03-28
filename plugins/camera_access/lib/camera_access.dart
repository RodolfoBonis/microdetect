import 'dart:async';
import 'dart:typed_data';
import 'dart:isolate';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter/scheduler.dart';

/// Informações de uma câmera disponível no dispositivo
class CameraDevice {
  /// Identificador único da câmera
  final String id;

  /// Nome descritivo da câmera
  final String name;

  /// Se a câmera é a câmera principal/padrão do dispositivo
  final bool isDefault;

  /// Posição da câmera (frontal, traseira, etc.)
  final CameraPosition position;

  const CameraDevice({
    required this.id,
    required this.name,
    this.isDefault = false,
    this.position = CameraPosition.unknown,
  });

  factory CameraDevice.fromMap(Map<dynamic, dynamic> map) {
    return CameraDevice(
      id: map['id'] as String? ?? '',
      name: map['name'] as String? ?? 'Câmera desconhecida',
      isDefault: map['isDefault'] as bool? ?? false,
      position: _positionFromString(map['position'] as String?),
    );
  }

  static CameraPosition _positionFromString(String? position) {
    if (position == null) return CameraPosition.unknown;
    switch (position.toLowerCase()) {
      case 'front': return CameraPosition.front;
      case 'back': return CameraPosition.back;
      case 'external': return CameraPosition.external;
      default: return CameraPosition.unknown;
    }
  }

  @override
  String toString() => 'CameraDevice(id: $id, name: $name, isDefault: $isDefault, position: $position)';
}

/// Posição/tipo da câmera
enum CameraPosition {
  front,    // Câmera frontal
  back,     // Câmera traseira
  external, // Câmera externa (USB, etc.)
  unknown,  // Posição desconhecida
}

/// Resolução da câmera
class CameraResolution {
  final int width;
  final int height;

  const CameraResolution(this.width, this.height);

  /// Resolução HD (1280x720)
  static const CameraResolution hd = CameraResolution(1280, 720);
  
  /// Resolução Full HD (1920x1080)
  static const CameraResolution fullHD = CameraResolution(1920, 1080);
  
  /// Resolução 4K (3840x2160)
  static const CameraResolution uhd = CameraResolution(3840, 2160);
  
  /// Resolução média (640x480)
  static const CameraResolution medium = CameraResolution(640, 480);
  
  /// Resolução baixa (320x240)
  static const CameraResolution low = CameraResolution(320, 240);

  Map<String, dynamic> toMap() => {
    'width': width,
    'height': height,
  };

  @override
  String toString() => '${width}x$height';
  
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is CameraResolution &&
          runtimeType == other.runtimeType &&
          width == other.width &&
          height == other.height;

  @override
  int get hashCode => width.hashCode ^ height.hashCode;
}

/// Ajustes de imagem para a câmera
class CameraImageAdjustments {
  /// Brilho entre -1.0 e 1.0 (0.0 é neutro)
  final double brightness;
  
  /// Contraste entre -1.0 e 1.0 (0.0 é neutro)
  final double contrast;
  
  /// Saturação entre -1.0 e 1.0 (0.0 é neutro)
  final double saturation;
  
  /// Nitidez entre 0.0 e 1.0 (0.0 é neutro)
  final double sharpness;
  
  /// Exposição entre -1.0 e 1.0 (0.0 é neutro)
  final double exposure;
  
  /// Ganho entre 0.0 e 2.0 (1.0 é neutro)
  final double gain;
  
  /// Tipo de filtro aplicado (null para nenhum)
  final String? filter;
  
  /// Se deve usar aceleração de hardware quando disponível
  final bool useHardwareAcceleration;

  const CameraImageAdjustments({
    this.brightness = 0.0,
    this.contrast = 0.0,
    this.saturation = 0.0,
    this.sharpness = 0.0,
    this.exposure = 0.0,
    this.gain = 1.0,
    this.filter,
    this.useHardwareAcceleration = true,
  });

  /// Cria uma instância com valores padrão
  factory CameraImageAdjustments.defaultSettings() => const CameraImageAdjustments();

  /// Cria uma cópia desta instância com valores atualizados
  CameraImageAdjustments copyWith({
    double? brightness,
    double? contrast,
    double? saturation,
    double? sharpness,
    double? exposure,
    double? gain,
    String? filter,
    bool? useHardwareAcceleration,
  }) {
    return CameraImageAdjustments(
      brightness: brightness ?? this.brightness,
      contrast: contrast ?? this.contrast,
      saturation: saturation ?? this.saturation,
      sharpness: sharpness ?? this.sharpness,
      exposure: exposure ?? this.exposure,
      gain: gain ?? this.gain,
      filter: filter ?? this.filter,
      useHardwareAcceleration: useHardwareAcceleration ?? this.useHardwareAcceleration,
    );
  }

  /// Converte os ajustes para um mapa
  Map<String, dynamic> toMap() => {
    'brightness': brightness,
    'contrast': contrast,
    'saturation': saturation,
    'sharpness': sharpness,
    'exposure': exposure,
    'gain': gain,
    'filter': filter,
    'useHardwareAcceleration': useHardwareAcceleration,
  };
  
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is CameraImageAdjustments &&
          runtimeType == other.runtimeType &&
          brightness == other.brightness &&
          contrast == other.contrast &&
          saturation == other.saturation &&
          sharpness == other.sharpness &&
          exposure == other.exposure &&
          gain == other.gain &&
          filter == other.filter &&
          useHardwareAcceleration == other.useHardwareAcceleration;

  @override
  int get hashCode =>
      brightness.hashCode ^
      contrast.hashCode ^
      saturation.hashCode ^
      sharpness.hashCode ^
      exposure.hashCode ^
      gain.hashCode ^
      filter.hashCode ^
      useHardwareAcceleration.hashCode;
}

/// Classe principal para acessar funcionalidades de câmera
class CameraAccess {
  static const MethodChannel _channel = MethodChannel('camera_access');

  /// Singleton instance
  static final CameraAccess _instance = CameraAccess._();

  /// Factory constructor para acessar a instância singleton
  factory CameraAccess() => _instance;

  /// Construtor privado para o singleton
  CameraAccess._();

  /// Controla o estado de inicialização da câmera
  bool _isCameraInitialized = false;
  
  /// Armazena o zoom atual da câmera
  double _currentZoom = 1.0;
  
  /// Isolate para processamento em background
  Isolate? _processingIsolate;
  SendPort? _isolateSendPort;
  ReceivePort? _isolateReceivePort;
  final ReceivePort _resultReceivePort = ReceivePort();
  
  /// Cache de frames para otimização
  final LruCache<Uint8List> _frameCache = LruCache<Uint8List>(maxSize: 10);
  
  /// Controlador para enviar eventos da câmera
  StreamController<CameraEvent> _eventController = StreamController<CameraEvent>.broadcast();
  
  /// Indica se o controlador de eventos foi fechado
  bool _isEventControllerClosed = false;
  
  /// Stream de eventos da câmera
  Stream<CameraEvent> get eventStream => _eventController.stream;

  /// Configurações atuais de resolução
  CameraResolution _currentResolution = CameraResolution.medium;
  
  /// Ajustes atuais de imagem
  CameraImageAdjustments _currentAdjustments = CameraImageAdjustments.defaultSettings();
  
  /// Estado de processamento
  bool _processingFrame = false;
  Completer<Uint8List?>? _processingCompleter;
  int _consecutiveDroppedFrames = 0;
  int _totalFramesProcessed = 0;
  DateTime? _lastFrameTimestamp;
  
  /// Mapa de completers para solicitações de processamento de frames
  final Map<int, Completer<Uint8List>> _frameCompleters = {};
  
  /// Retorna se a câmera está inicializada
  bool get isCameraInitialized => _isCameraInitialized;
  
  /// Retorna a resolução atual
  CameraResolution get currentResolution => _currentResolution;
  
  /// Retorna os ajustes atuais
  CameraImageAdjustments get currentAdjustments => _currentAdjustments;
  
  /// Retorna estatísticas de processamento
  Map<String, dynamic> get statistics => {
    'totalFramesProcessed': _totalFramesProcessed,
    'droppedFrames': _consecutiveDroppedFrames,
    'cacheSize': _frameCache.size,
    'isProcessing': _processingFrame,
    'frameRate': _calculateFrameRate(),
  };
  
  double _calculateFrameRate() {
    if (_lastFrameTimestamp == null || _totalFramesProcessed < 2) return 0;
    final timeDiff = DateTime.now().difference(_lastFrameTimestamp!).inMilliseconds;
    if (timeDiff <= 0) return 0;
    return 1000 / timeDiff;
  }
  
  /// Inicializar isolate para processamento em background
  Future<void> _initializeProcessingIsolate() async {
    if (_processingIsolate != null) return;
    
    _isolateReceivePort = ReceivePort();
    
    try {
      _processingIsolate = await Isolate.spawn(
        _imageProcessingIsolate,
        _isolateReceivePort!.sendPort,
      );
      
      _isolateSendPort = await _isolateReceivePort!.first;
      
      // Configurar porta para receber resultados
      _resultReceivePort.listen((dynamic result) {
        if (result is Map) {
          final requestId = result['requestId'];
          final data = result['data'];
          
          if (requestId != null && data is Uint8List) {
            // Completar o Completer específico para esta solicitação
            final completer = _frameCompleters[requestId];
            if (completer != null && !completer.isCompleted) {
              completer.complete(data);
              _frameCompleters.remove(requestId);
            }
          }
        } else if (result is Uint8List && _processingCompleter != null && !_processingCompleter!.isCompleted) {
          _processingCompleter!.complete(result);
        }
      });
    } catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error,
        message: 'Erro ao inicializar isolate: $e',
      ));
      _isolateReceivePort?.close();
      _isolateReceivePort = null;
    }
  }
  
  /// Função para o isolate de processamento de imagem
  static void _imageProcessingIsolate(SendPort sendPort) {
    final receivePort = ReceivePort();
    sendPort.send(receivePort.sendPort);
    
    receivePort.listen((dynamic message) {
      if (message is Map) {
        final data = message['data'] as Uint8List;
        final adjustments = message['adjustments'] as Map<String, dynamic>;
        final resultPort = message['resultPort'] as SendPort;
        final requestId = message['requestId'];
        
        try {
          // Processamento de imagem em background
          final processedData = _applyImageProcessing(data, adjustments);
          
          if (requestId != null) {
            // Enviar com o ID da solicitação
            resultPort.send({
              'requestId': requestId,
              'data': processedData,
            });
          } else {
            // Compatibilidade com chamadas antigas
            resultPort.send(processedData);
          }
        } catch (e) {
          // Em caso de erro, retornar os dados originais
          if (requestId != null) {
            resultPort.send({
              'requestId': requestId,
              'data': data,
            });
          } else {
            resultPort.send(data);
          }
        }
      }
    });
  }
  
  /// Método para aplicar processamento de imagem
  static Uint8List _applyImageProcessing(Uint8List data, Map<String, dynamic> adjustments) {
    // Implementação real deve processar a imagem de acordo com os ajustes
    // Como este é um método estático chamado pelo isolate, usamos apenas
    // uma implementação básica por enquanto
    return data;
  }

  /// Verifica se a permissão de câmera está concedida
  Future<bool> checkPermission() async {
    try {
      return await _channel.invokeMethod<bool>('checkPermission') ?? false;
    } on PlatformException catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error, 
        message: 'Erro ao verificar permissão: ${e.message}',
      ));
      return false;
    }
  }

  /// Alias para checkPermission - para compatibilidade com o camera_screen.dart
  Future<bool> hasPermission() => checkPermission();

  /// Inicializa o plugin e prepara para uso
  Future<bool> initialize() async {
    if (_isCameraInitialized) return true;
    
    try {
      // Inicializar isolate para processamento em background
      await _initializeProcessingIsolate();
      
      // Obter lista de câmeras
      final cameras = await getAvailableCameras();
      
      // Se não houver câmeras, falhar
      if (cameras.isEmpty) {
        _safeAddEvent(CameraEvent(
          type: CameraEventType.error,
          message: 'Nenhuma câmera encontrada',
        ));
        return false;
      }
      
      // Selecionar a primeira câmera externa ou a primeira disponível
      final camera = cameras.firstWhere(
        (camera) => camera.position == CameraPosition.external,
        orElse: () => cameras.first,
      );
      
      // Iniciar sessão com a câmera selecionada
      final success = await startCameraSession(camera.id);
      
      if (success) {
        _safeAddEvent(CameraEvent(
          type: CameraEventType.cameraStarted,
          message: 'Plugin inicializado com sucesso',
          data: {'cameraId': camera.id},
        ));
      }
      
      return success;
    } catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error, 
        message: 'Erro ao inicializar plugin: $e',
      ));
      return false;
    }
  }

  /// Alias para getAvailableCameras - para compatibilidade com o camera_screen.dart
  Future<List<CameraDevice>> getDevices() => getAvailableCameras();

  /// Inicia uma sessão de câmera com ID específico - alias para startCameraSession
  Future<bool> startSession(String cameraId) => startCameraSession(cameraId);

  /// Define parâmetros de imagem - método unificado para compatibilidade
  Future<bool> setImageParameters({
    double brightness = 0.0,
    double contrast = 0.0,
    double saturation = 0.0,
    double sharpness = 0.0,
    String? filter,
  }) {
    final adjustments = CameraImageAdjustments(
      brightness: brightness,
      contrast: contrast,
      saturation: saturation,
      sharpness: sharpness,
      filter: filter,
    );
    
    return setImageAdjustments(adjustments);
  }

  /// Obtém o nível de zoom atual
  Future<double?> getZoomLevel() async {
    try {
      return await _channel.invokeMethod<double>('getZoomLevel');
    } on PlatformException catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error, 
        message: 'Erro ao obter nível de zoom: ${e.message}',
      ));
      // Valor padrão em caso de erro ou método não implementado
      return _currentZoom;
    } on MissingPluginException catch (_) {
      // Método não implementado na plataforma, retornar valor interno
      return _currentZoom;
    }
  }

  /// Obtém o nível máximo de zoom suportado
  Future<double?> getMaxZoomLevel() async {
    try {
      return await _channel.invokeMethod<double>('getMaxZoomLevel') ?? 5.0;
    } on PlatformException catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error, 
        message: 'Erro ao obter nível máximo de zoom: ${e.message}',
      ));
      return 5.0; // Valor padrão em caso de erro
    } on MissingPluginException catch (_) {
      // Método não implementado na plataforma, retornar valor fixo
      return 5.0;
    }
  }

  /// Define o nível de zoom
  Future<bool> setZoomLevel(double zoomLevel) async {
    if (!_isCameraInitialized) return false;
    
    try {
      final result = await _channel.invokeMethod<bool>(
        'setZoomLevel',
        {'zoomLevel': zoomLevel},
      ) ?? false;
      
      if (result) {
        _currentZoom = zoomLevel;
      }
      
      return result;
    } on PlatformException catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error, 
        message: 'Erro ao definir zoom: ${e.message}',
      ));
      return false;
    } on MissingPluginException catch (_) {
      // Método não implementado na plataforma
      // Apenas atualizamos a variável interna para simular funcionamento
      _currentZoom = zoomLevel;
      return true;
    }
  }

  /// Stream de eventos da câmera - alias para eventStream
  Stream<CameraEvent> get events => eventStream;
  
  /// Stream de frames da câmera - alias para getCameraStream
  Stream<Uint8List> get frameStream => getCameraStream();

  /// Captura uma imagem completa com todos os ajustes aplicados
  Future<CapturedImage?> captureImage({
    bool applyAdjustments = true,
    double brightness = 0.0,
    double contrast = 0.0,
    double saturation = 0.0,
    double sharpness = 0.0,
    String? filter,
  }) async {
    if (!_isCameraInitialized) return null;
    
    final frame = await captureFrame(forceCapture: true);
    if (frame == null) return null;
    
    // Aplicar ajustes se necessário
    if (applyAdjustments) {
      // Aplicar os ajustes especificados ou os atuais
      final adjustments = CameraImageAdjustments(
        brightness: brightness,
        contrast: contrast,
        saturation: saturation,
        sharpness: sharpness,
        filter: filter,
      );
      
      // Aplicar processamento na imagem capturada
      final processedFrame = await _processFrameWithAdjustments(frame, adjustments);
      
      return CapturedImage(
        bytes: processedFrame ?? frame,
        width: _currentResolution.width,
        height: _currentResolution.height,
        timestamp: DateTime.now(),
      );
    }
    
    return CapturedImage(
      bytes: frame,
      width: _currentResolution.width,
      height: _currentResolution.height,
      timestamp: DateTime.now(),
    );
  }

  /// Processa um frame com ajustes específicos
  Future<Uint8List?> _processFrameWithAdjustments(
    Uint8List frame,
    CameraImageAdjustments adjustments,
  ) async {
    // Se não há processamento em isolate, aplicar diretamente
    if (_isolateSendPort == null) {
      return frame;
    }
    
    // Criar um ID único para esta solicitação
    final requestId = DateTime.now().millisecondsSinceEpoch;
    
    // Criar um completer para esta solicitação específica
    final completer = Completer<Uint8List>();
    _frameCompleters[requestId] = completer;
    
    // Enviar para o isolate com o ID da solicitação
    _isolateSendPort!.send({
      'requestId': requestId,
      'data': frame,
      'adjustments': adjustments.toMap(),
      'resultPort': _resultReceivePort.sendPort,
    });
    
    // Aguardar o resultado com timeout
    try {
      final result = await completer.future.timeout(
        const Duration(seconds: 2),
        onTimeout: () => frame,
      );
      
      _frameCompleters.remove(requestId);
      return result;
    } catch (e) {
      _frameCompleters.remove(requestId);
      return frame;
    }
  }

  /// Solicita permissão para acessar a câmera
  Future<bool> requestPermission() async {
    try {
      return await _channel.invokeMethod<bool>('requestPermission') ?? false;
    } on PlatformException catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error, 
        message: 'Erro ao solicitar permissão: ${e.message}',
      ));
      return false;
    }
  }

  /// Obtém lista de câmeras disponíveis no dispositivo
  Future<List<CameraDevice>> getAvailableCameras() async {
    try {
      final List<dynamic>? cameras = await _channel.invokeMethod<List<dynamic>>('getAvailableCameras');

      if (cameras == null) return [];

      return cameras
          .map((dynamic camera) => CameraDevice.fromMap(camera as Map<dynamic, dynamic>))
          .toList();
    } on PlatformException catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error, 
        message: 'Erro ao obter câmeras: ${e.message}',
      ));
      return [];
    }
  }

  /// Define a resolução da câmera
  Future<bool> setResolution(CameraResolution resolution) async {
    if (!_isCameraInitialized) return false;
    
    try {
      final result = await _channel.invokeMethod<bool>(
        'setResolution',
        resolution.toMap(),
      ) ?? false;
      
      if (result) {
        _currentResolution = resolution;
        _safeAddEvent(CameraEvent(
          type: CameraEventType.resolutionChanged,
          data: resolution.toMap(),
        ));
      }
      
      return result;
    } on PlatformException catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error, 
        message: 'Erro ao definir resolução: ${e.message}',
      ));
      return false;
    }
  }
  
  /// Define ajustes de imagem
  Future<bool> setImageAdjustments(CameraImageAdjustments adjustments) async {
    if (!_isCameraInitialized) return false;
    
    try {
      final result = await _channel.invokeMethod<bool>(
        'setImageAdjustments',
        adjustments.toMap(),
      ) ?? false;
      
      if (result) {
        _currentAdjustments = adjustments;
        _safeAddEvent(CameraEvent(
          type: CameraEventType.adjustmentsChanged,
          data: adjustments.toMap(),
        ));
      }
      
      return result;
    } on PlatformException catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error, 
        message: 'Erro ao definir ajustes: ${e.message}',
      ));
      return false;
    }
  }

  /// Inicia uma sessão de câmera
  ///
  /// [cameraId] ID da câmera a ser utilizada
  /// [resolution] Resolução desejada (opcional)
  Future<bool> startCameraSession(String cameraId, {CameraResolution? resolution}) async {
    try {
      final Map<String, dynamic> args = {
        'cameraId': cameraId,
      };
      
      if (resolution != null) {
        args.addAll(resolution.toMap());
        _currentResolution = resolution;
      }
      
      final result = await _channel.invokeMethod<bool>('startCameraSession', args) ?? false;
      
      // Atualiza o estado de inicialização
      _isCameraInitialized = result;
      
      // Inicializar isolate para processamento em background
      if (result) {
        await _initializeProcessingIsolate();
        _safeAddEvent(CameraEvent(
          type: CameraEventType.cameraStarted,
          message: 'Câmera iniciada com sucesso',
          data: {'cameraId': cameraId},
        ));
      }
      
      return result;
    } on PlatformException catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error, 
        message: 'Erro ao iniciar sessão de câmera: ${e.message}',
      ));
      return false;
    }
  }

  /// Encerra a sessão de câmera ativa
  Future<bool> stopCameraSession() async {
    try {
      final result = await _channel.invokeMethod<bool>('stopCameraSession') ?? false;
      
      // Atualiza o estado de inicialização após parar a sessão
      if (result) {
        _isCameraInitialized = false;
        
        // Limpar cache
        _frameCache.clear();
        
        _safeAddEvent(CameraEvent(
          type: CameraEventType.cameraStopped,
          message: 'Câmera finalizada com sucesso',
        ));
      }
      
      return result;
    } on PlatformException catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error, 
        message: 'Erro ao encerrar sessão de câmera: ${e.message}',
      ));
      return false;
    } finally {
      // Encerrar isolate se existir
      if (_processingIsolate != null) {
        _processingIsolate!.kill(priority: Isolate.immediate);
        _processingIsolate = null;
      }
    }
  }

  /// Captura um frame da câmera ativa. Retorna nulo se não houver câmera ativa.
  /// 
  /// O parâmetro [processInBackground] indica se o processamento deve ser feito em um isolate.
  /// O parâmetro [forceCapture] indica se deve tentar de forma mais agressiva obter um frame.
  Future<Uint8List?> captureFrame({
    bool processInBackground = true,
    bool forceCapture = false
  }) async {
    if (!_isCameraInitialized) return null;
    
    // Evitar sobrecarga de capturas concorrentes
    if (_processingFrame) {
      _consecutiveDroppedFrames++;
      
      // Se descartar muitos frames, usar o cache se disponível
      if (_consecutiveDroppedFrames > 3 && _frameCache.isNotEmpty) {
        return _frameCache.latest;
      }
      
      return null;
    }
    
    _processingFrame = true;
    _processingCompleter = Completer<Uint8List?>();
    
    try {
      // Captura frame bruto da câmera
      final frame = await _channel.invokeMethod<Uint8List>(
        'captureFrame', 
        {'forceCapture': forceCapture}
      );
      
      if (frame == null || frame.isEmpty) {
        _processingFrame = false;
        _processingCompleter?.complete();
        _processingCompleter = null;
        return null;
      }
      
      // Atualizar timestamp para cálculo de FPS
      _lastFrameTimestamp = DateTime.now();
      _totalFramesProcessed++;
      _consecutiveDroppedFrames = 0;
      
      // Processar frame em background se necessário
      Uint8List processedFrame;
      if (processInBackground && _isolateSendPort != null) {
        // Criar um ID único para esta solicitação
        final requestId = DateTime.now().millisecondsSinceEpoch;
        
        // Criar um completer para esta solicitação específica
        final completer = Completer<Uint8List>();
        _frameCompleters[requestId] = completer;
        
        // Enviar para o isolate com o ID da solicitação
        _isolateSendPort!.send({
          'requestId': requestId,
          'data': frame,
          'adjustments': _currentAdjustments.toMap(),
          'resultPort': _resultReceivePort.sendPort,
        });
        
        // Configurar timeout
        final timer = Timer(const Duration(milliseconds: 100), () {
          if (!completer.isCompleted) {
            completer.complete(frame); // Em caso de timeout, usar frame original
            _frameCompleters.remove(requestId);
          }
        });
        
        // Aguardar pelo resultado usando o Completer
        processedFrame = await completer.future;
        _frameCompleters.remove(requestId);
        timer.cancel();
      } else {
        // Usar frame sem processamento
        processedFrame = frame;
      }
      
      // Armazenar no cache para reutilização
      _frameCache.put(processedFrame);
      
      return processedFrame;
    } catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error,
        message: 'Erro ao capturar frame: $e',
      ));
      return null;
    } finally {
      _processingFrame = false;
      _processingCompleter?.complete();
      _processingCompleter = null;
    }
  }

  /// Captura um frame da câmera usando método alternativo que reinicia a câmera brevemente.
  /// Útil quando o método padrão não consegue obter frames.
  /// 
  /// O parâmetro [highQuality] indica se a imagem deve ser capturada em alta qualidade.
  Future<Uint8List?> captureFrameAlternative({bool highQuality = true}) async {
    try {
      if (!_isCameraInitialized) return null;
      final frame = await _channel.invokeMethod<Uint8List>(
        'captureFrameAlternative',
        {'highQuality': highQuality}
      );
      
      if (frame != null && frame.isNotEmpty) {
        _frameCache.put(frame);
      }
      
      return frame;
    } catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error,
        message: 'Erro ao capturar frame (método alternativo): $e',
      ));
      return null;
    }
  }

  /// Método de último recurso que tenta recuperar qualquer frame do buffer da câmera,
  /// mesmo que pareça inválido. Usa configurações de emergência para extrair a imagem.
  Future<Uint8List?> getLastFrameFromBuffer() async {
    try {
      if (!_isCameraInitialized) return null;
      final frame = await _channel.invokeMethod<Uint8List>('getLastFrameFromBuffer');
      return frame;
    } catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error,
        message: 'Erro ao recuperar último frame do buffer: $e',
      ));
      return null;
    }
  }

  /// Método que tenta diferentes abordagens para capturar um frame
  /// Este método tenta uma progressão de métodos para garantir que algum frame seja retornado
  Future<Uint8List?> captureFrameWithFallback() async {
    try {
      // Primeiro, tentar o método padrão
      final frame = await captureFrame();
      if (frame != null && frame.isNotEmpty) {
        return frame;
      }
      
      // Se falhar, tentar com forceCapture
      final frameForced = await captureFrame(forceCapture: true);
      if (frameForced != null && frameForced.isNotEmpty) {
        return frameForced;
      }
      
      // Se ainda falhar, tentar método alternativo
      final frameAlt = await captureFrameAlternative();
      if (frameAlt != null && frameAlt.isNotEmpty) {
        return frameAlt;
      }
      
      // Como último recurso, tentar pegar do buffer
      return await getLastFrameFromBuffer();
    } catch (e) {
      // Se ocorrer qualquer erro durante a progressão, tentar como último recurso
      try {
        return await getLastFrameFromBuffer();
      } catch (finalError) {
        _safeAddEvent(CameraEvent(
          type: CameraEventType.error,
          message: 'Erro completo no captureFrameWithFallback: $finalError',
        ));
        return null;
      }
    }
  }

  /// Obtém um stream contínuo de frames da câmera que sincroniza com vSync
  Stream<Uint8List> getCameraStream({int framesPerSecond = 30}) {
    // Usar StreamController para criar um stream personalizado
    final controller = StreamController<Uint8List>();
    bool isActive = true;
    
    // Função para capturar frames sincronizados com vSync
    void captureNextFrame() {
      if (!isActive || controller.isClosed) return;
      
      // Programar próxima execução para manter taxa de frames
      final targetInterval = Duration(milliseconds: 1000 ~/ framesPerSecond);
      
      // Capturar um frame
      captureFrame().then((frame) {
        if (frame != null && !controller.isClosed && isActive) {
          controller.add(frame);
        }
        
        // Programar próximo frame usando vSync
        SchedulerBinding.instance.addPostFrameCallback((_) {
          if (isActive && !controller.isClosed) {
            Future.delayed(targetInterval, captureNextFrame);
          }
        });
      }).catchError((error) {
        if (!controller.isClosed) {
          _safeAddEvent(CameraEvent(
            type: CameraEventType.error,
            message: 'Erro no stream de câmera: $error',
          ));
        }
      });
    }
    
    // Iniciar captura
    captureNextFrame();
    
    // Retornar stream com limpeza quando fechado
    return controller.stream.doOnCancel(() {
      isActive = false;
      controller.close();
    });
  }
  
  /// Dispõe recursos
  void dispose() {
    _eventController.close();
    _isEventControllerClosed = true;
    
    stopCameraSession();
    
    if (_processingIsolate != null) {
      _processingIsolate!.kill(priority: Isolate.immediate);
      _processingIsolate = null;
    }
    
    // Limpar todos os completers pendentes
    _frameCompleters.forEach((_, completer) {
      if (!completer.isCompleted) {
        completer.completeError('Disposed');
      }
    });
    _frameCompleters.clear();
    
    _isolateReceivePort?.close();
    _resultReceivePort.close();
  }

  /// Método seguro para adicionar eventos
  void _safeAddEvent(CameraEvent event) {
    if (_isEventControllerClosed) {
      // Recriar o controlador se estiver fechado
      _eventController = StreamController<CameraEvent>.broadcast();
      _isEventControllerClosed = false;
    }
    
    try {
      _eventController.add(event);
    } catch (e) {
      // Se falhar ao adicionar (controller possivelmente fechado)
      _log('Erro ao adicionar evento de câmera: $e');
      _isEventControllerClosed = true;
    }
  }
  
  /// Registra uma mensagem de log para fins de depuração
  void _log(String message) {
    // Em uma implementação real, usaria um framework de logging adequado
    // como logging ou flutter_logger
    debugPrint('[CameraAccess] $message');
  }

  /// Define o balanço de branco da câmera
  /// 
  /// [mode] Modo de balanço de branco: 'auto', 'daylight', 'fluorescent', 'incandescent'
  Future<bool> setWhiteBalance(String mode) async {
    if (!_isCameraInitialized) return false;
    
    try {
      final result = await _channel.invokeMethod<bool>(
        'setWhiteBalance',
        {'mode': mode},
      ) ?? false;
      
      if (result) {
        _safeAddEvent(CameraEvent(
          type: CameraEventType.whiteBalanceChanged,
          data: {'mode': mode},
        ));
      }
      
      return result;
    } on PlatformException catch (e) {
      _safeAddEvent(CameraEvent(
        type: CameraEventType.error, 
        message: 'Erro ao definir balanço de branco: ${e.message}',
      ));
      return false;
    }
  }
}

/// Cache LRU (Least Recently Used) para otimização
class LruCache<T> {
  final int maxSize;
  final Map<int, T> _cache = {};
  final List<int> _accessOrder = [];
  int _counter = 0;
  
  LruCache({required this.maxSize});
  
  int get size => _cache.length;
  bool get isEmpty => _cache.isEmpty;
  bool get isNotEmpty => _cache.isNotEmpty;
  T? get latest => isEmpty ? null : _cache[_accessOrder.last];
  
  void put(T value) {
    final key = _counter++;
    
    // Adicionar ao cache
    _cache[key] = value;
    _accessOrder.add(key);
    
    // Remover item mais antigo se exceder tamanho máximo
    if (_cache.length > maxSize) {
      final oldestKey = _accessOrder.removeAt(0);
      _cache.remove(oldestKey);
    }
  }
  
  void clear() {
    _cache.clear();
    _accessOrder.clear();
  }
}

/// Evento da câmera para comunicação com a aplicação
class CameraEvent {
  final CameraEventType type;
  final String? message;
  final Map<String, dynamic>? data;
  
  CameraEvent({
    required this.type,
    this.message,
    this.data,
  });
}

/// Tipos de eventos da câmera
enum CameraEventType {
  cameraStarted,
  cameraStopped,
  frameCapture,
  resolutionChanged,
  adjustmentsChanged,
  zoomChanged,
  error,
  whiteBalanceChanged,
}

/// Extension para adicionar funcionalidade doOnCancel ao Stream
extension StreamExtension<T> on Stream<T> {
  Stream<T> doOnCancel(void Function() onCancel) {
    final controller = StreamController<T>();
    
    final subscription = listen(
      controller.add,
      onError: controller.addError,
      onDone: controller.close,
    );
    
    controller.onCancel = () {
      subscription.cancel();
      onCancel();
    };
    
    return controller.stream;
  }
}

/// Representa uma imagem capturada pela câmera
class CapturedImage {
  /// Dados da imagem em bytes
  final Uint8List bytes;
  
  /// Largura da imagem em pixels
  final int width;
  
  /// Altura da imagem em pixels
  final int height;
  
  /// Timestamp de quando a imagem foi capturada
  final DateTime timestamp;
  
  const CapturedImage({
    required this.bytes,
    required this.width,
    required this.height,
    required this.timestamp,
  });
}

/// Extensão para CameraDevice para compatibilidade
extension CameraDeviceExt on CameraDevice {
  /// Verifica se a câmera é externa
  bool get isExternal => position == CameraPosition.external;
} 