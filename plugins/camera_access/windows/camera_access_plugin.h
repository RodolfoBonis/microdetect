#ifndef FLUTTER_PLUGIN_CAMERA_ACCESS_PLUGIN_H_
#define FLUTTER_PLUGIN_CAMERA_ACCESS_PLUGIN_H_

#include <flutter/method_channel.h>
#include <flutter/plugin_registrar_windows.h>
#include <memory>
#include "camera_manager.h"

namespace camera_access {

class CameraAccessPlugin : public flutter::Plugin {
 public:
  static void RegisterWithRegistrar(flutter::PluginRegistrarWindows *registrar);

  CameraAccessPlugin(flutter::PluginRegistrarWindows* registrar);

  virtual ~CameraAccessPlugin();

  // Disallow copy and assign.
  CameraAccessPlugin(const CameraAccessPlugin&) = delete;
  CameraAccessPlugin& operator=(const CameraAccessPlugin&) = delete;

 private:
  // Called when a method is called on this plugin's channel from Dart.
  void HandleMethodCall(
      const flutter::MethodCall<flutter::EncodableValue> &method_call,
      std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);

  // Métodos para manipular chamadas específicas
  void CheckPermission(std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);
  void RequestPermission(std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);
  void GetAvailableCameras(std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);
  void StartCameraSession(const flutter::EncodableMap& args,
                          std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);
  void StopCameraSession(std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);
  void CaptureFrame(const flutter::EncodableMap* args,
                   std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);
  void CaptureFrameAlternative(const flutter::EncodableMap* args,
                             std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);
  void GetLastFrameFromBuffer(std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);
  void GetZoomLevel(std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);
  void GetMaxZoomLevel(std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);
  void SetZoomLevel(const flutter::EncodableMap& args,
                   std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);
  void SetWhiteBalance(const flutter::EncodableMap& args,
                      std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result);

  // Gerenciador de câmeras
  std::unique_ptr<CameraManager> camera_manager_;
  flutter::PluginRegistrarWindows* registrar_;
};

}  // namespace camera_access

#endif  // FLUTTER_PLUGIN_CAMERA_ACCESS_PLUGIN_H_