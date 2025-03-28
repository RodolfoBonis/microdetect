#include "camera_access_plugin.h"

#include <flutter/method_channel.h>
#include <flutter/plugin_registrar_windows.h>
#include <flutter/standard_method_codec.h>
#include <windows.h>

#include <memory>
#include <sstream>

namespace camera_access {

// static
void CameraAccessPlugin::RegisterWithRegistrar(
    flutter::PluginRegistrarWindows *registrar) {
  auto channel =
      std::make_unique<flutter::MethodChannel<flutter::EncodableValue>>(
          registrar->messenger(), "camera_access",
          &flutter::StandardMethodCodec::GetInstance());

  auto plugin = std::make_unique<CameraAccessPlugin>(registrar);

  channel->SetMethodCallHandler(
      [plugin_pointer = plugin.get()](const auto &call, auto result) {
        plugin_pointer->HandleMethodCall(call, std::move(result));
      });

  registrar->AddPlugin(std::move(plugin));
}

CameraAccessPlugin::CameraAccessPlugin(flutter::PluginRegistrarWindows* registrar)
    : registrar_(registrar), camera_manager_(std::make_unique<CameraManager>()) {
}

CameraAccessPlugin::~CameraAccessPlugin() {
  // Certifique-se de que a sessão da câmera está encerrada
  if (camera_manager_ && camera_manager_->IsSessionActive()) {
    camera_manager_->StopCameraSession();
  }
}

void CameraAccessPlugin::HandleMethodCall(
    const flutter::MethodCall<flutter::EncodableValue> &method_call,
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  const std::string& method_name = method_call.method_name();

  if (method_name == "checkPermission") {
    CheckPermission(std::move(result));
  } else if (method_name == "requestPermission") {
    RequestPermission(std::move(result));
  } else if (method_name == "getAvailableCameras") {
    GetAvailableCameras(std::move(result));
  } else if (method_name == "startCameraSession") {
    const auto* arguments = std::get_if<flutter::EncodableMap>(method_call.arguments());
    if (arguments) {
      StartCameraSession(*arguments, std::move(result));
    } else {
      result->Error("INVALID_ARGS", "Argumentos inválidos");
    }
  } else if (method_name == "stopCameraSession") {
    StopCameraSession(std::move(result));
  } else if (method_name == "captureFrame") {
    const auto* arguments = std::get_if<flutter::EncodableMap>(method_call.arguments());
    CaptureFrame(arguments, std::move(result));
  } else if (method_name == "captureFrameAlternative") {
    const auto* arguments = std::get_if<flutter::EncodableMap>(method_call.arguments());
    CaptureFrameAlternative(arguments, std::move(result));
  } else if (method_name == "getLastFrameFromBuffer") {
    GetLastFrameFromBuffer(std::move(result));
  } else if (method_name == "getZoomLevel") {
    GetZoomLevel(std::move(result));
  } else if (method_name == "getMaxZoomLevel") {
    GetMaxZoomLevel(std::move(result));
  } else if (method_name == "setZoomLevel") {
    const auto* arguments = std::get_if<flutter::EncodableMap>(method_call.arguments());
    if (arguments) {
      SetZoomLevel(*arguments, std::move(result));
    } else {
      result->Error("INVALID_ARGS", "Argumentos inválidos");
    }
  } else if (method_name == "setWhiteBalance") {
    const auto* arguments = std::get_if<flutter::EncodableMap>(method_call.arguments());
    if (arguments) {
      SetWhiteBalance(*arguments, std::move(result));
    } else {
      result->Error("INVALID_ARGS", "Argumentos inválidos");
    }
  } else {
    result->NotImplemented();
  }
}

void CameraAccessPlugin::CheckPermission(
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  // No Windows, geralmente não precisamos de permissão explícita para acessar a câmera
  result->Success(flutter::EncodableValue(camera_manager_->CheckPermission()));
}

void CameraAccessPlugin::RequestPermission(
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  // No Windows, geralmente não precisamos de permissão explícita para acessar a câmera
  result->Success(flutter::EncodableValue(camera_manager_->RequestPermission()));
}

void CameraAccessPlugin::GetAvailableCameras(
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  result->Success(camera_manager_->GetAvailableCameras());
}

void CameraAccessPlugin::StartCameraSession(
    const flutter::EncodableMap& args,
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  auto it = args.find(flutter::EncodableValue("cameraId"));
  if (it == args.end()) {
    result->Error("INVALID_ARGS", "cameraId é obrigatório");
    return;
  }

  const std::string camera_id = std::get<std::string>(it->second);
  bool success = camera_manager_->StartCameraSession(camera_id);

  if (success) {
    result->Success(flutter::EncodableValue(true));
  } else {
    result->Error("CAMERA_ERROR", "Falha ao iniciar sessão de câmera");
  }
}

void CameraAccessPlugin::StopCameraSession(
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  bool success = camera_manager_->StopCameraSession();
  result->Success(flutter::EncodableValue(success));
}

void CameraAccessPlugin::CaptureFrame(
    const flutter::EncodableMap* args,
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  if (!camera_manager_->IsSessionActive()) {
    result->Error("CAMERA_ERROR", "Sessão de câmera não está ativa");
    return;
  }

  // Processar o argumento forceCapture
  bool force_capture = false;
  if (args != nullptr) {
    auto force_capture_it = args->find(flutter::EncodableValue("forceCapture"));
    if (force_capture_it != args->end() && 
        std::holds_alternative<bool>(force_capture_it->second)) {
      force_capture = std::get<bool>(force_capture_it->second);
    }
  }

  std::vector<uint8_t> frame_data = camera_manager_->CaptureFrame(force_capture);

  if (frame_data.empty()) {
    result->Error("CAMERA_ERROR", "Falha ao capturar frame");
    return;
  }

  std::vector<uint8_t> copy(frame_data.begin(), frame_data.end());
  result->Success(flutter::EncodableValue(copy));
}

void CameraAccessPlugin::CaptureFrameAlternative(
    const flutter::EncodableMap* args,
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  if (!camera_manager_->IsSessionActive()) {
    result->Error("CAMERA_ERROR", "Sessão de câmera não está ativa");
    return;
  }

  // Processar o argumento highQuality
  bool high_quality = false;
  if (args != nullptr) {
    auto high_quality_it = args->find(flutter::EncodableValue("highQuality"));
    if (high_quality_it != args->end() && 
        std::holds_alternative<bool>(high_quality_it->second)) {
      high_quality = std::get<bool>(high_quality_it->second);
    }
  }

  std::vector<uint8_t> frame_data = camera_manager_->CaptureFrameAlternative(high_quality);

  if (frame_data.empty()) {
    result->Error("CAMERA_ERROR", "Falha ao capturar frame com método alternativo");
    return;
  }

  std::vector<uint8_t> copy(frame_data.begin(), frame_data.end());
  result->Success(flutter::EncodableValue(copy));
}

void CameraAccessPlugin::GetLastFrameFromBuffer(
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  if (!camera_manager_->IsSessionActive()) {
    result->Error("CAMERA_ERROR", "Sessão de câmera não está ativa");
    return;
  }

  std::vector<uint8_t> frame_data = camera_manager_->GetLastFrameFromBuffer();

  if (frame_data.empty()) {
    result->Error("CAMERA_ERROR", "Nenhum frame disponível no buffer");
    return;
  }

  std::vector<uint8_t> copy(frame_data.begin(), frame_data.end());
  result->Success(flutter::EncodableValue(copy));
}

void CameraAccessPlugin::GetZoomLevel(
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  if (!camera_manager_->IsSessionActive()) {
    result->Error("CAMERA_ERROR", "Sessão de câmera não está ativa");
    return;
  }

  double zoom_level = camera_manager_->GetZoomLevel();
  result->Success(flutter::EncodableValue(zoom_level));
}

void CameraAccessPlugin::GetMaxZoomLevel(
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  if (!camera_manager_->IsSessionActive()) {
    result->Error("CAMERA_ERROR", "Sessão de câmera não está ativa");
    return;
  }

  double max_zoom_level = camera_manager_->GetMaxZoomLevel();
  result->Success(flutter::EncodableValue(max_zoom_level));
}

void CameraAccessPlugin::SetZoomLevel(
    const flutter::EncodableMap& args,
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  if (!camera_manager_->IsSessionActive()) {
    result->Error("CAMERA_ERROR", "Sessão de câmera não está ativa");
    return;
  }

  auto zoom_it = args.find(flutter::EncodableValue("zoomLevel"));
  if (zoom_it == args.end()) {
    result->Error("INVALID_ARGS", "Nível de zoom não especificado");
    return;
  }

  double zoom_level = 1.0;
  if (std::holds_alternative<double>(zoom_it->second)) {
    zoom_level = std::get<double>(zoom_it->second);
  } else if (std::holds_alternative<int>(zoom_it->second)) {
    zoom_level = static_cast<double>(std::get<int>(zoom_it->second));
  } else {
    result->Error("INVALID_ARGS", "Nível de zoom tem tipo inválido");
    return;
  }

  bool success = camera_manager_->SetZoomLevel(zoom_level);
  result->Success(flutter::EncodableValue(success));
}

void CameraAccessPlugin::SetWhiteBalance(
    const flutter::EncodableMap& args,
    std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
  if (!camera_manager_->IsSessionActive()) {
    result->Error("CAMERA_ERROR", "Sessão de câmera não está ativa");
    return;
  }

  // Extrair modo de balanço de branco
  auto mode_it = args.find(flutter::EncodableValue("mode"));
  if (mode_it == args.end() || !std::holds_alternative<std::string>(mode_it->second)) {
    result->Error("INVALID_ARGS", "Modo de balanço de branco é obrigatório");
    return;
  }

  std::string mode = std::get<std::string>(mode_it->second);
  bool success = camera_manager_->SetWhiteBalance(mode);

  if (success) {
    result->Success(flutter::EncodableValue(true));
  } else {
    result->Success(flutter::EncodableValue(false));
  }
}

}  // namespace camera_access