#ifndef FLUTTER_PLUGIN_CAMERA_MANAGER_H_
#define FLUTTER_PLUGIN_CAMERA_MANAGER_H_

#include <flutter/encodable_value.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <windows.h>
#include <d3d11.h>
#include <wincodec.h>
#include <wrl/client.h>

#include <condition_variable>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
#include <memory>
#include <atomic>
#include <deque>
#include <chrono>

// Link com DirectX e WIC
#pragma comment(lib, "d3d11.lib")
#pragma comment(lib, "windowscodecs.lib")

namespace camera_access {

// Tamanho do buffer ring para frames
constexpr size_t kRingBufferSize = 3;

// Timeout para operações em ms
constexpr DWORD kOperationTimeoutMs = 100;

// Definição da estrutura de resolução da câmera
struct CameraResolution {
  uint32_t width = 640;
  uint32_t height = 480;
  
  CameraResolution() = default;
  CameraResolution(uint32_t w, uint32_t h) : width(w), height(h) {}
  
  flutter::EncodableMap ToEncodableMap() const {
    flutter::EncodableMap map;
    map[flutter::EncodableValue("width")] = flutter::EncodableValue(static_cast<int>(width));
    map[flutter::EncodableValue("height")] = flutter::EncodableValue(static_cast<int>(height));
    return map;
  }
  
  static CameraResolution FromEncodableMap(const flutter::EncodableMap& map) {
    CameraResolution res;
    auto width_it = map.find(flutter::EncodableValue("width"));
    auto height_it = map.find(flutter::EncodableValue("height"));
    
    if (width_it != map.end() && std::holds_alternative<int>(width_it->second)) {
      res.width = static_cast<uint32_t>(std::get<int>(width_it->second));
    }
    
    if (height_it != map.end() && std::holds_alternative<int>(height_it->second)) {
      res.height = static_cast<uint32_t>(std::get<int>(height_it->second));
    }
    
    return res;
  }
  
  bool operator==(const CameraResolution& other) const {
    return width == other.width && height == other.height;
  }
  
  bool operator<(const CameraResolution& other) const {
    return (width * height) < (other.width * other.height);
  }
};

// Definição da estrutura de ajustes de imagem
struct ImageAdjustments {
  float brightness = 0.0f;
  float contrast = 0.0f;
  float saturation = 0.0f;
  float sharpness = 0.0f;
  float exposure = 0.0f;
  float gain = 1.0f;
  std::string filter;
  bool use_hardware_acceleration = true;
  
  ImageAdjustments() = default;
  
  flutter::EncodableMap ToEncodableMap() const {
    flutter::EncodableMap map;
    map[flutter::EncodableValue("brightness")] = flutter::EncodableValue(static_cast<double>(brightness));
    map[flutter::EncodableValue("contrast")] = flutter::EncodableValue(static_cast<double>(contrast));
    map[flutter::EncodableValue("saturation")] = flutter::EncodableValue(static_cast<double>(saturation));
    map[flutter::EncodableValue("sharpness")] = flutter::EncodableValue(static_cast<double>(sharpness));
    map[flutter::EncodableValue("exposure")] = flutter::EncodableValue(static_cast<double>(exposure));
    map[flutter::EncodableValue("gain")] = flutter::EncodableValue(static_cast<double>(gain));
    map[flutter::EncodableValue("useHardwareAcceleration")] = flutter::EncodableValue(use_hardware_acceleration);
    
    if (!filter.empty()) {
      map[flutter::EncodableValue("filter")] = flutter::EncodableValue(filter);
    }
    
    return map;
  }
  
  static ImageAdjustments FromEncodableMap(const flutter::EncodableMap& map) {
    ImageAdjustments adj;
    
    auto get_double_value = [&map](const char* key, float default_value) -> float {
      auto it = map.find(flutter::EncodableValue(key));
      if (it != map.end() && std::holds_alternative<double>(it->second)) {
        return static_cast<float>(std::get<double>(it->second));
      }
      return default_value;
    };
    
    adj.brightness = get_double_value("brightness", 0.0f);
    adj.contrast = get_double_value("contrast", 0.0f);
    adj.saturation = get_double_value("saturation", 0.0f);
    adj.sharpness = get_double_value("sharpness", 0.0f);
    adj.exposure = get_double_value("exposure", 0.0f);
    adj.gain = get_double_value("gain", 1.0f);
    
    auto it_filter = map.find(flutter::EncodableValue("filter"));
    if (it_filter != map.end() && std::holds_alternative<std::string>(it_filter->second)) {
      adj.filter = std::get<std::string>(it_filter->second);
    }
    
    auto it_hardware = map.find(flutter::EncodableValue("useHardwareAcceleration"));
    if (it_hardware != map.end() && std::holds_alternative<bool>(it_hardware->second)) {
      adj.use_hardware_acceleration = std::get<bool>(it_hardware->second);
    }
    
    adj.Clamp();
    
    return adj;
  }
  
  void Clamp() {
    brightness = std::max(-1.0f, std::min(1.0f, brightness));
    contrast = std::max(-1.0f, std::min(1.0f, contrast));
    saturation = std::max(-1.0f, std::min(1.0f, saturation));
    sharpness = std::max(0.0f, std::min(1.0f, sharpness));
    exposure = std::max(-1.0f, std::min(1.0f, exposure));
    gain = std::max(0.0f, std::min(2.0f, gain));
  }
};

struct CameraDevice {
  std::wstring id;
  std::wstring name;
  bool is_default;
  std::string position; // "front", "back", "external", "unknown"
};

// Estrutura para armazenar um frame no buffer
struct FrameData {
  std::vector<uint8_t> data;
  uint32_t width = 0;
  uint32_t height = 0;
  std::chrono::steady_clock::time_point timestamp;
  
  FrameData() = default;
  
  FrameData(std::vector<uint8_t>&& buffer_data, uint32_t w, uint32_t h)
      : data(std::move(buffer_data)), width(w), height(h), 
        timestamp(std::chrono::steady_clock::now()) {}
};

class CameraManager {
 public:
  CameraManager();
  ~CameraManager();

  // Métodos para gerenciamento de câmeras
  flutter::EncodableList GetAvailableCameras();
  bool StartCameraSession(const std::string& camera_id);
  
  // Método otimizado para iniciar sessão com configurações
  bool StartCameraSessionWithConfig(
      const std::string& camera_id,
      const CameraResolution& resolution = CameraResolution(1280, 720),
      const ImageAdjustments& adjustments = ImageAdjustments());
  
  bool StopCameraSession();
  
  // Métodos para captura de frames
  std::vector<uint8_t> CaptureFrame(bool force_capture = false);
  std::vector<uint8_t> CaptureFrameAlternative(bool high_quality = true);
  std::vector<uint8_t> GetLastFrameFromBuffer();
  
  // Método otimizado para captura com ajustes específicos
  std::vector<uint8_t> CaptureFrameWithAdjustments(
      const ImageAdjustments& adjustments,
      bool force_capture = false);
  
  // Métodos para resolução
  bool SetResolution(uint32_t width, uint32_t height);
  CameraResolution GetCurrentResolution() const { return current_resolution_; }
  flutter::EncodableList GetAvailableResolutions();
  
  // Métodos para ajustes de imagem
  bool SetImageAdjustments(const flutter::EncodableMap& adjustments_map);
  ImageAdjustments GetCurrentImageAdjustments() const { return current_adjustments_; }
  
  // Métodos para zoom
  double GetZoomLevel() const { return current_zoom_level_; }
  double GetMaxZoomLevel() const { return max_zoom_level_; }
  bool SetZoomLevel(double zoom_level);
  
  // Métodos para balanço de branco
  bool SetWhiteBalance(const std::string& mode);
  std::string GetCurrentWhiteBalance() const { return current_white_balance_; }

  // Métodos para permissões (Windows não requer)
  bool CheckPermission() { return true; }
  bool RequestPermission() { return true; }

  // Status da sessão
  bool IsSessionActive() const { return session_active_; }
  
 private:
  // Inicialização do sistema
  bool InitializeMF();
  void ShutdownMF();
  bool EnumerateDevices();
  static std::string WideToUtf8(const std::wstring& wstr);
  static std::wstring Utf8ToWide(const std::string& str);
  void FrameCaptureThread();
  bool ProcessFrame(IMFSample* sample);
  
  // Aceleração de hardware
  bool InitializeHardwareAcceleration();
  void CleanupHardwareAcceleration();
  
  // Processamento de imagem otimizado
  bool ApplyImageAdjustments(BYTE* data, UINT width, UINT height, UINT stride);
  bool ApplyImageAdjustmentsSoftware(BYTE* data, UINT width, UINT height, UINT stride);
  bool ApplyImageAdjustmentsHardware(BYTE* data, UINT width, UINT height, UINT stride);  
  bool ApplyImageFilter(BYTE* data, UINT width, UINT height, UINT stride);
  
  // Conversão de formatos
  bool FrameToBMP(BYTE* data, UINT width, UINT height, UINT stride, std::vector<BYTE>& bmpData);
  bool FrameToJPEG(BYTE* data, UINT width, UINT height, UINT stride, std::vector<BYTE>& jpegData);
  
  // Métodos para gestão de resolução
  bool FindClosestResolution(uint32_t& width, uint32_t& height);
  bool EnumerateSupportedResolutions();
  
  // Métodos para gestão adaptativa de qualidade
  void AdaptQualityDown();
  void TryAdaptQualityUp();
  void TrackProcessingTime(double processing_time);
  
  // Propriedades
  Microsoft::WRL::ComPtr<IMFSourceReader> source_reader_;
  std::vector<CameraDevice> devices_;
  std::vector<CameraResolution> supported_resolutions_;
  
  // Thread de captura e sincronização
  std::thread capture_thread_;
  std::mutex frame_mutex_;
  std::condition_variable frame_condition_;
  std::atomic<bool> thread_running_;
  std::atomic<bool> new_frame_available_;
  std::atomic<bool> session_active_;
  
  // Buffer ring de frames para suavizar captura
  std::deque<FrameData> frame_ring_buffer_;
  std::mutex buffer_mutex_;
  
  // Sistema de timeout e controle de desempenho
  std::chrono::steady_clock::time_point last_frame_time_;
  std::chrono::milliseconds frame_interval_{33}; // Aproximadamente 30 FPS
  std::atomic<bool> adaptive_quality_{true};
  std::vector<double> processing_times_;
  int consecutive_slow_frames_ = 0;
  
  // Estado
  bool mf_initialized_;
  
  // Resolução atual
  CameraResolution current_resolution_;
  
  // Ajustes de imagem
  ImageAdjustments current_adjustments_;
  
  // Hardware acceleration
  bool hardware_acceleration_initialized_;
  Microsoft::WRL::ComPtr<ID3D11Device> d3d_device_;
  Microsoft::WRL::ComPtr<ID3D11DeviceContext> d3d_context_;
  Microsoft::WRL::ComPtr<IWICImagingFactory> wic_factory_;
  
  // Zoom
  double current_zoom_level_ = 1.0;
  double max_zoom_level_ = 10.0;
  
  // Balanço de branco
  std::string current_white_balance_ = "auto";
  float white_balance_red_gain_ = 1.0f;
  float white_balance_green_gain_ = 1.0f;
  float white_balance_blue_gain_ = 1.0f;
};

}  // namespace camera_access

#endif  // FLUTTER_PLUGIN_CAMERA_MANAGER_H_