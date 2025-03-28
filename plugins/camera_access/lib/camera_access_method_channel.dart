import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import 'camera_access_platform_interface.dart';
import 'camera_access.dart';

/// Implementação do Method Channel para o plugin de acesso à câmera
class MethodChannelCameraAccess extends CameraAccessPlatform {
  /// Method Channel usado para comunicação com código nativo
  @visibleForTesting
  final methodChannel = const MethodChannel('camera_access');
  
  /// Stream controller para eventos de frame
  final StreamController<Uint8List> _frameStreamController = 
      StreamController<Uint8List>.broadcast();
  
  /// Stream de frames capturados pela câmera
  Stream<Uint8List> get frameStream => _frameStreamController.stream;
  
  /// Construtor que registra os handlers de eventos
  MethodChannelCameraAccess() {
    methodChannel.setMethodCallHandler(_handleMethodCall);
  }
  
  /// Manipula chamadas de método que vêm da plataforma nativa
  Future<dynamic> _handleMethodCall(MethodCall call) async {
    switch (call.method) {
      case 'onCameraFrame':
        final Uint8List frameData = call.arguments;
        _frameStreamController.add(frameData);
        break;
      case 'onCameraError':
        // Propagar erro
        final String errorMessage = call.arguments;
        debugPrint('Camera Error: $errorMessage');
        break;
      default:
        debugPrint('Method not implemented: ${call.method}');
    }
  }
  
  @override
  Future<String?> getPlatformVersion() async {
    try {
      final version = await methodChannel.invokeMethod<String>('getPlatformVersion');
      return version;
    } catch (e) {
      debugPrint('Error getting platform version: $e');
      return null;
    }
  }

  @override
  Future<List<Map<String, dynamic>>> getAvailableCameras() async {
    try {
      final cameras = await methodChannel.invokeListMethod<Map<dynamic, dynamic>>('getAvailableCameras');
      if (cameras == null) {
        return [];
      }
      
      return cameras.map((camera) {
        return Map<String, dynamic>.from(camera);
      }).toList();
    } catch (e) {
      debugPrint('Error getting available cameras: $e');
      return [];
    }
  }

  @override
  Future<bool> checkPermission() async {
    try {
      final hasPermission = await methodChannel.invokeMethod<bool>('checkPermission');
      return hasPermission ?? false;
    } catch (e) {
      debugPrint('Error checking camera permission: $e');
      return false;
    }
  }

  @override
  Future<bool> requestPermission() async {
    try {
      final hasPermission = await methodChannel.invokeMethod<bool>('requestPermission');
      return hasPermission ?? false;
    } catch (e) {
      debugPrint('Error requesting camera permission: $e');
      return false;
    }
  }

  @override
  Future<bool> startCameraSession(String cameraId) async {
    try {
      final result = await methodChannel.invokeMethod<bool>(
        'startCameraSession',
        {'cameraId': cameraId},
      );
      return result ?? false;
    } catch (e) {
      debugPrint('Error starting camera session: $e');
      return false;
    }
  }
  
  @override
  Future<bool> startCameraSessionWithConfig({
    required String cameraId,
    CameraResolution? resolution,
    CameraImageAdjustments? adjustments,
  }) async {
    try {
      final Map<String, dynamic> arguments = {
        'cameraId': cameraId,
      };
      
      if (resolution != null) {
        arguments['resolution'] = {
          'width': resolution.width,
          'height': resolution.height,
        };
      }
      
      if (adjustments != null) {
        arguments['adjustments'] = {
          'brightness': adjustments.brightness,
          'contrast': adjustments.contrast,
          'saturation': adjustments.saturation,
          'sharpness': adjustments.sharpness,
          'filter': adjustments.filter,
        };
      }
      
      final result = await methodChannel.invokeMethod<bool>(
        'startCameraSessionWithConfig',
        arguments,
      );
      
      return result ?? false;
    } catch (e) {
      debugPrint('Error starting camera session with config: $e');
      return false;
    }
  }

  @override
  Future<bool> stopCameraSession() async {
    try {
      final result = await methodChannel.invokeMethod<bool>('stopCameraSession');
      return result ?? false;
    } catch (e) {
      debugPrint('Error stopping camera session: $e');
      return false;
    }
  }

  @override
  Future<Uint8List?> captureFrame({bool forceCapture = false}) async {
    try {
      final frameData = await methodChannel.invokeMethod<Uint8List>(
        'captureFrame',
        {'forceCapture': forceCapture},
      );
      return frameData;
    } catch (e) {
      debugPrint('Error capturing frame: $e');
      return null;
    }
  }
  
  @override
  Future<Uint8List?> captureFrameWithAdjustments({
    required bool forceCapture,
    required CameraImageAdjustments adjustments,
  }) async {
    try {
      final frameData = await methodChannel.invokeMethod<Uint8List>(
        'captureFrameWithAdjustments',
        {
          'forceCapture': forceCapture,
          'adjustments': {
            'brightness': adjustments.brightness,
            'contrast': adjustments.contrast,
            'saturation': adjustments.saturation,
            'sharpness': adjustments.sharpness,
            'filter': adjustments.filter,
          },
        },
      );
      return frameData;
    } catch (e) {
      debugPrint('Error capturing frame with adjustments: $e');
      return null;
    }
  }

  @override
  Future<Uint8List?> captureFrameAlternative({bool highQuality = false}) async {
    try {
      final frameData = await methodChannel.invokeMethod<Uint8List>(
        'captureFrameAlternative',
        {'highQuality': highQuality},
      );
      return frameData;
    } catch (e) {
      debugPrint('Error capturing frame alternative: $e');
      return null;
    }
  }
  
  @override
  Future<bool> setResolution(CameraResolution resolution) async {
    try {
      final result = await methodChannel.invokeMethod<bool>(
        'setResolution',
        {
          'width': resolution.width,
          'height': resolution.height,
        },
      );
      return result ?? false;
    } catch (e) {
      debugPrint('Error setting resolution: $e');
      return false;
    }
  }
  
  @override
  Future<CameraResolution> getCurrentResolution() async {
    try {
      final resMap = await methodChannel.invokeMapMethod<String, dynamic>('getCurrentResolution');
      if (resMap == null) {
        return CameraResolution(1280, 720); // HD como padrão
      }
      
      final width = resMap['width'] as int? ?? 1280;
      final height = resMap['height'] as int? ?? 720;
      
      return CameraResolution(width, height);
    } catch (e) {
      debugPrint('Error getting current resolution: $e');
      return CameraResolution(1280, 720); // HD como padrão em caso de erro
    }
  }
  
  @override
  Future<List<CameraResolution>> getAvailableResolutions() async {
    try {
      final resList = await methodChannel.invokeListMethod<Map<dynamic, dynamic>>('getAvailableResolutions');
      if (resList == null) {
        return [
          CameraResolution(640, 480),   // VGA
          CameraResolution(1280, 720),  // HD
          CameraResolution(1920, 1080), // Full HD
        ];
      }
      
      return resList.map((resMap) {
        final map = Map<String, dynamic>.from(resMap);
        final width = map['width'] as int? ?? 1280;
        final height = map['height'] as int? ?? 720;
        return CameraResolution(width, height);
      }).toList();
    } catch (e) {
      debugPrint('Error getting available resolutions: $e');
      // Retornar resoluções padrão em caso de erro
      return [
        CameraResolution(640, 480),   // VGA
        CameraResolution(1280, 720),  // HD
        CameraResolution(1920, 1080), // Full HD
      ];
    }
  }
  
  @override
  Future<bool> setImageAdjustments(CameraImageAdjustments adjustments) async {
    try {
      final result = await methodChannel.invokeMethod<bool>(
        'setImageAdjustments',
        {
          'brightness': adjustments.brightness,
          'contrast': adjustments.contrast,
          'saturation': adjustments.saturation,
          'sharpness': adjustments.sharpness,
          'filter': adjustments.filter,
        },
      );
      return result ?? false;
    } catch (e) {
      debugPrint('Error setting image adjustments: $e');
      return false;
    }
  }
  
  @override
  Future<CameraImageAdjustments> getCurrentImageAdjustments() async {
    try {
      final adjMap = await methodChannel.invokeMapMethod<String, dynamic>('getCurrentImageAdjustments');
      if (adjMap == null) {
        return CameraImageAdjustments(); // Valores padrão
      }
      
      return CameraImageAdjustments(
        brightness: adjMap['brightness'] as double? ?? 0.0,
        contrast: adjMap['contrast'] as double? ?? 0.0,
        saturation: adjMap['saturation'] as double? ?? 0.0,
        sharpness: adjMap['sharpness'] as double? ?? 0.0,
        filter: adjMap['filter'] as String?,
      );
    } catch (e) {
      debugPrint('Error getting current image adjustments: $e');
      return CameraImageAdjustments(); // Valores padrão em caso de erro
    }
  }

  @override
  Future<Uint8List?> getLastFrameFromBuffer() async {
    try {
      final frameData = await methodChannel.invokeMethod<Uint8List>('getLastFrameFromBuffer');
      return frameData;
    } catch (e) {
      debugPrint('Error getting last frame from buffer: $e');
      return null;
    }
  }
  
  @override
  Future<bool> setWhiteBalance(String mode) async {
    try {
      final result = await methodChannel.invokeMethod<bool>(
        'setWhiteBalance',
        {'mode': mode},
      );
      return result ?? false;
    } catch (e) {
      debugPrint('Error setting white balance: $e');
      return false;
    }
  }
  
  /// Libera recursos quando não for mais necessário
  void dispose() {
    _frameStreamController.close();
  }
} 