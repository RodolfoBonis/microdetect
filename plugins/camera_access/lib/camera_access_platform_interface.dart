import 'dart:typed_data';

import 'package:plugin_platform_interface/plugin_platform_interface.dart';

import 'camera_access.dart';
import 'camera_access_method_channel.dart';

abstract class CameraAccessPlatform extends PlatformInterface {
  /// Constructs a CameraAccessPlatform.
  CameraAccessPlatform() : super(token: _token);

  static final Object _token = Object();

  static CameraAccessPlatform _instance = MethodChannelCameraAccess();

  /// The default instance of [CameraAccessPlatform] to use.
  ///
  /// Defaults to [MethodChannelCameraAccess].
  static CameraAccessPlatform get instance => _instance;

  /// Platform-specific implementations should set this with their own
  /// platform-specific class that extends [CameraAccessPlatform] when
  /// they register themselves.
  static set instance(CameraAccessPlatform instance) {
    PlatformInterface.verifyToken(instance, _token);
    _instance = instance;
  }

  Future<String?> getPlatformVersion() {
    throw UnimplementedError('platformVersion() has not been implemented.');
  }

  Future<List<Map<String, dynamic>>> getAvailableCameras() {
    throw UnimplementedError('getAvailableCameras() has not been implemented.');
  }

  Future<bool> checkPermission() {
    throw UnimplementedError('checkPermission() has not been implemented.');
  }

  Future<bool> requestPermission() {
    throw UnimplementedError('requestPermission() has not been implemented.');
  }

  Future<bool> startCameraSession(String cameraId) {
    throw UnimplementedError('startCameraSession() has not been implemented.');
  }
  
  Future<bool> startCameraSessionWithConfig({
    required String cameraId,
    CameraResolution? resolution,
    CameraImageAdjustments? adjustments,
  }) {
    throw UnimplementedError('startCameraSessionWithConfig() has not been implemented.');
  }

  Future<bool> stopCameraSession() {
    throw UnimplementedError('stopCameraSession() has not been implemented.');
  }

  Future<Uint8List?> captureFrame({bool forceCapture = false}) {
    throw UnimplementedError('captureFrame() has not been implemented.');
  }
  
  Future<Uint8List?> captureFrameWithAdjustments({
    required bool forceCapture,
    required CameraImageAdjustments adjustments,
  }) {
    throw UnimplementedError('captureFrameWithAdjustments() has not been implemented.');
  }

  Future<Uint8List?> captureFrameAlternative({bool highQuality = false}) {
    throw UnimplementedError('captureFrameAlternative() has not been implemented.');
  }
  
  Future<bool> setResolution(CameraResolution resolution) {
    throw UnimplementedError('setResolution() has not been implemented.');
  }
  
  Future<CameraResolution> getCurrentResolution() {
    throw UnimplementedError('getCurrentResolution() has not been implemented.');
  }
  
  Future<List<CameraResolution>> getAvailableResolutions() {
    throw UnimplementedError('getAvailableResolutions() has not been implemented.');
  }
  
  Future<bool> setImageAdjustments(CameraImageAdjustments adjustments) {
    throw UnimplementedError('setImageAdjustments() has not been implemented.');
  }
  
  Future<CameraImageAdjustments> getCurrentImageAdjustments() {
    throw UnimplementedError('getCurrentImageAdjustments() has not been implemented.');
  }

  Future<Uint8List?> getLastFrameFromBuffer() {
    throw UnimplementedError('getLastFrameFromBuffer() has not been implemented.');
  }
  
  Future<bool> setWhiteBalance(String mode) {
    throw UnimplementedError('setWhiteBalance() has not been implemented.');
  }
} 