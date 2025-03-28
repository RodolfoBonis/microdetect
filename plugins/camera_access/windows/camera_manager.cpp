#include "camera_manager.h"

#include <mfapi.h>
#include <mfreadwrite.h>
#include <mfcaptureengine.h>
#include <mferror.h>
#include <codecvt>
#include <locale>
#include <shlwapi.h>
#include <strsafe.h>
#include <algorithm>
#include <wrl.h>
#include <wincodec.h>
#include <d3d11.h>
#include <memory>
#include <chrono>
#include <cmath>
#include <vector>
#include <thread>
#include <sstream>

// Linking da biblioteca de media foundation
#pragma comment(lib, "mf.lib")
#pragma comment(lib, "mfplat.lib")
#pragma comment(lib, "mfreadwrite.lib")
#pragma comment(lib, "mfuuid.lib")
#pragma comment(lib, "shlwapi.lib")

// Para compilação
#include <windows.media.h>
#include <windows.devices.enumeration.h>

namespace camera_access {

// Constantes para medir tempo de expiração
const DWORD READ_TIMEOUT_MS = 5000;

// Estruturas pré-definidas de resolução comum
const CameraResolution RESOLUTION_VGA(640, 480);
const CameraResolution RESOLUTION_HD(1280, 720);
const CameraResolution RESOLUTION_FULL_HD(1920, 1080);

// Como converter entre formatos de string
std::string CameraManager::WideToUtf8(const std::wstring& wstr) {
  std::wstring_convert<std::codecvt_utf8<wchar_t>> converter;
  return converter.to_bytes(wstr);
}

std::wstring CameraManager::Utf8ToWide(const std::string& str) {
  std::wstring_convert<std::codecvt_utf8<wchar_t>> converter;
  return converter.from_bytes(str);
}

CameraManager::CameraManager()
    : source_reader_(nullptr),
      session_active_(false),
      mf_initialized_(false),
      new_frame_available_(false),
      thread_running_(false),
      hardware_acceleration_initialized_(false) {
  
  // Inicializar resolução padrão
  current_resolution_ = RESOLUTION_HD;
  
  // Inicializar Media Foundation
  InitializeMF();
  
  // Enumerar dispositivos disponíveis
  EnumerateDevices();
  
  // Inicializar aceleração de hardware
  InitializeHardwareAcceleration();
}

CameraManager::~CameraManager() {
  StopCameraSession();
  CleanupHardwareAcceleration();
  ShutdownMF();
}

bool CameraManager::InitializeMF() {
  HRESULT hr = MFStartup(MF_VERSION, MFSTARTUP_LITE);
  mf_initialized_ = SUCCEEDED(hr);
  return mf_initialized_;
}

void CameraManager::ShutdownMF() {
  if (mf_initialized_) {
    MFShutdown();
    mf_initialized_ = false;
  }
}

bool CameraManager::InitializeHardwareAcceleration() {
  if (hardware_acceleration_initialized_) {
    return true;
  }
  
  // Criar dispositivo D3D11
  D3D_FEATURE_LEVEL feature_levels[] = {
    D3D_FEATURE_LEVEL_11_1,
    D3D_FEATURE_LEVEL_11_0,
    D3D_FEATURE_LEVEL_10_1,
    D3D_FEATURE_LEVEL_10_0,
    D3D_FEATURE_LEVEL_9_3
  };
  
  UINT flags = D3D11_CREATE_DEVICE_BGRA_SUPPORT;
  D3D_FEATURE_LEVEL feature_level;
  
  HRESULT hr = D3D11CreateDevice(
      nullptr,                     // Adaptador (padrão)
      D3D_DRIVER_TYPE_HARDWARE,    // Tipo de driver (hardware para aceleração)
      nullptr,                     // Software rasterizer
      flags,                       // Flags
      feature_levels,              // Níveis de recursos desejados
      ARRAYSIZE(feature_levels),   // Número de níveis
      D3D11_SDK_VERSION,           // Versão do SDK
      d3d_device_.GetAddressOf(),  // Dispositivo de saída
      &feature_level,              // Nível de recurso selecionado
      d3d_context_.GetAddressOf()  // Contexto de saída
  );
  
  if (FAILED(hr)) {
    // Falha na aceleração de hardware, tentar criar em WARP (software)
    hr = D3D11CreateDevice(
        nullptr,
        D3D_DRIVER_TYPE_WARP,
        nullptr,
        flags,
        feature_levels,
        ARRAYSIZE(feature_levels),
        D3D11_SDK_VERSION,
        d3d_device_.GetAddressOf(),
        &feature_level,
        d3d_context_.GetAddressOf()
    );
    
    if (FAILED(hr)) {
      return false;
    }
  }
  
  // Criar factory de WIC para processamento de imagem
  hr = CoCreateInstance(
      CLSID_WICImagingFactory,
      nullptr,
      CLSCTX_INPROC_SERVER,
      IID_PPV_ARGS(wic_factory_.GetAddressOf())
  );
  
  if (FAILED(hr)) {
    return false;
  }
  
  hardware_acceleration_initialized_ = true;
  return true;
}

void CameraManager::CleanupHardwareAcceleration() {
  if (hardware_acceleration_initialized_) {
    wic_factory_.Reset();
    staging_texture_.Reset();
    d3d_context_.Reset();
    d3d_device_.Reset();
    hardware_acceleration_initialized_ = false;
  }
}

bool CameraManager::EnumerateDevices() {
  if (!mf_initialized_) {
    return false;
  }

  devices_.clear();

  // Criar atributos para enumeração de dispositivos de vídeo
  IMFAttributes* attributes = nullptr;
  HRESULT hr = MFCreateAttributes(&attributes, 1);
  if (FAILED(hr)) {
    return false;
  }

  // Solicitar apenas dispositivos de captura de vídeo
  hr = attributes->SetGUID(
      MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE,
      MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE_VIDCAP_GUID);
  if (FAILED(hr)) {
    attributes->Release();
    return false;
  }

  // Enumerar dispositivos
  IMFActivate** devices = nullptr;
  UINT32 count = 0;
  hr = MFEnumDeviceSources(attributes, &devices, &count);
  attributes->Release();

  if (FAILED(hr)) {
    return false;
  }

  // Obter informações de cada dispositivo
  for (UINT32 i = 0; i < count; i++) {
    WCHAR friendly_name[256] = {0};
    UINT32 name_size = 0;

    hr = devices[i]->GetString(
        MF_DEVSOURCE_ATTRIBUTE_FRIENDLY_NAME,
        friendly_name,
        sizeof(friendly_name) / sizeof(friendly_name[0]),
        &name_size);

    if (SUCCEEDED(hr)) {
      // Obter o ID do dispositivo
      WCHAR symbolic_link[256] = {0};
      UINT32 link_size = 0;

      hr = devices[i]->GetString(
          MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE_VIDCAP_SYMBOLIC_LINK,
          symbolic_link,
          sizeof(symbolic_link) / sizeof(symbolic_link[0]),
          &link_size);

      if (SUCCEEDED(hr)) {
        CameraDevice camera;
        camera.id = symbolic_link;
        camera.name = friendly_name;
        camera.is_default = (i == 0); // Consideramos o primeiro dispositivo como padrão
        camera.position = "unknown";   // Não temos como saber a posição da câmera

        // Tentar determinar a posição com base no nome
        std::wstring name_lower = camera.name;
        std::transform(name_lower.begin(), name_lower.end(), name_lower.begin(),
                      [](wchar_t c) { return std::towlower(c); });

        if (name_lower.find(L"front") != std::wstring::npos ||
            name_lower.find(L"internal") != std::wstring::npos) {
          camera.position = "front";
        } else if (name_lower.find(L"back") != std::wstring::npos ||
                  name_lower.find(L"rear") != std::wstring::npos) {
          camera.position = "back";
        } else if (name_lower.find(L"usb") != std::wstring::npos ||
                  name_lower.find(L"external") != std::wstring::npos) {
          camera.position = "external";
        }

        devices_.push_back(camera);
      }
    }

    devices[i]->Release();
  }

  CoTaskMemFree(devices);
  return true;
}

flutter::EncodableList CameraManager::GetAvailableCameras() {
  flutter::EncodableList result;

  for (const auto& device : devices_) {
    flutter::EncodableMap camera_map;
    camera_map[flutter::EncodableValue("id")] = flutter::EncodableValue(WideToUtf8(device.id));
    camera_map[flutter::EncodableValue("name")] = flutter::EncodableValue(WideToUtf8(device.name));
    camera_map[flutter::EncodableValue("isDefault")] = flutter::EncodableValue(device.is_default);
    camera_map[flutter::EncodableValue("position")] = flutter::EncodableValue(device.position);

    result.push_back(flutter::EncodableValue(camera_map));
  }

  return result;
}

bool CameraManager::StartCameraSession(const std::string& camera_id) {
  if (session_active_) {
    StopCameraSession();
  }

  if (!mf_initialized_) {
    return false;
  }

  // Converter ID da câmera para formato wide
  std::wstring wide_camera_id = Utf8ToWide(camera_id);

  // Encontrar o dispositivo correspondente ao ID
  bool device_found = false;
  for (const auto& device : devices_) {
    if (device.id == wide_camera_id) {
      device_found = true;
      break;
    }
  }

  if (!device_found) {
    return false;
  }

  // Criar atributos para source reader
  IMFAttributes* attributes = nullptr;
  HRESULT hr = MFCreateAttributes(&attributes, 3);
  if (FAILED(hr)) {
    return false;
  }

  // Definir atributos para captura assíncrona
  hr = attributes->SetUINT32(MF_READWRITE_DISABLE_CONVERTERS, TRUE);
  if (FAILED(hr)) {
    attributes->Release();
    return false;
  }

  // Criar o source
  IMFMediaSource* source = nullptr;
  hr = MFCreateDeviceSource(attributes, &source);
  if (FAILED(hr)) {
    attributes->Release();
    return false;
  }

  // Criar o source reader
  hr = MFCreateSourceReaderFromMediaSource(
      source,
      attributes,
      &source_reader_);

  // Liberar recursos
  source->Release();
  attributes->Release();

  if (FAILED(hr)) {
    return false;
  }

  // Configurar formato de mídia
  // Queremos saída RGB32 que é fácil de converter para JPEG
  IMFMediaType* media_type = nullptr;
  hr = MFCreateMediaType(&media_type);
  if (FAILED(hr)) {
    source_reader_->Release();
    source_reader_ = nullptr;
    return false;
  }

  hr = media_type->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video);
  if (SUCCEEDED(hr)) {
    hr = media_type->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_RGB32);
  }

  // Configurar a saída do source reader
  if (SUCCEEDED(hr)) {
    hr = source_reader_->SetCurrentMediaType(
        (DWORD)MF_SOURCE_READER_FIRST_VIDEO_STREAM,
        nullptr,
        media_type);
  }

  media_type->Release();

  if (FAILED(hr)) {
    source_reader_->Release();
    source_reader_ = nullptr;
    return false;
  }

  // Iniciar thread de captura de frames
  current_camera_id_ = wide_camera_id;
  session_active_ = true;
  thread_running_ = true;
  capture_thread_ = std::thread(&CameraManager::FrameCaptureThread, this);

  return true;
}

bool CameraManager::StopCameraSession() {
  if (!session_active_) {
    return true;
  }

  // Parar thread de captura
  thread_running_ = false;
  if (capture_thread_.joinable()) {
    capture_thread_.join();
  }

  // Liberar recursos
  if (source_reader_) {
    source_reader_->Release();
    source_reader_ = nullptr;
  }

  session_active_ = false;
  current_camera_id_.clear();

  {
    std::lock_guard<std::mutex> lock(frame_mutex_);
    current_frame_.clear();
    new_frame_available_ = false;
  }

  return true;
}

std::vector<uint8_t> CameraManager::CaptureFrame(bool force_capture) {
  if (!session_active_ || !source_reader_) {
    return {};
  }

  auto start_time = std::chrono::high_resolution_clock::now();
  
  // Usar um timeout para evitar bloqueio indefinido
  std::unique_lock<std::mutex> lock(buffer_mutex_, std::defer_lock);
  if (!lock.try_lock_for(std::chrono::milliseconds(force_capture ? 50 : 5))) {
    return {}; // Não conseguiu obter o lock no tempo determinado
  }
  
  // Verificar o buffer ring primeiro
  if (!frame_ring_buffer_.empty()) {
    auto now = std::chrono::steady_clock::now();
    auto& latest_frame = frame_ring_buffer_.back();
    
    // Verificar se o frame não é muito antigo
    auto age = std::chrono::duration_cast<std::chrono::milliseconds>(
        now - latest_frame.timestamp).count();
        
    if (age < 100 || !force_capture) { // 100ms é fresco o suficiente para uso normal
      std::vector<uint8_t> result = latest_frame.data;
      lock.unlock();
      return result;
    }
  }
  
  // Se chegamos aqui, precisamos capturar um novo frame
  lock.unlock();
  
  // Aguardar por um novo frame com timeout
  {
    std::unique_lock<std::mutex> frame_lock(frame_mutex_);
    new_frame_available_ = false;
    
    // Definir tempo máximo de espera
    auto wait_time = std::chrono::milliseconds(force_capture ? 200 : 50);
    
    // Aguardar por um novo frame ou timeout
    if (!frame_condition_.wait_for(frame_lock, wait_time, [this] { return new_frame_available_.load(); })) {
      // Timeout - tentar usar o último frame disponível no buffer
      return GetLastFrameFromBuffer();
    }
  }
  
  // Obtém o frame mais recente
  std::lock_guard<std::mutex> buffer_lock(buffer_mutex_);
  if (frame_ring_buffer_.empty()) {
    return {};
  }
  
  auto& latest_frame = frame_ring_buffer_.back();
  auto result = latest_frame.data;
  
  // Registrar tempo de processamento para ajuste adaptativo
  auto end_time = std::chrono::high_resolution_clock::now();
  double processing_time = std::chrono::duration<double, std::milli>(
      end_time - start_time).count();
  TrackProcessingTime(processing_time);
  
  return result;
}

std::vector<uint8_t> CameraManager::CaptureFrameAlternative(bool high_quality) {
  // Se a sessão não estiver ativa, não há como capturar
  if (!session_active_) {
    return {};
  }
  
  // Salvar o ID da câmera atual
  std::wstring current_id = current_camera_id_;
  
  // Parar e reiniciar a sessão da câmera (forçar reinicialização do hardware)
  StopCameraSession();
  
  // Pequena pausa para garantir que o hardware tenha tempo de reiniciar
  std::this_thread::sleep_for(std::chrono::milliseconds(500));
  
  // Se high_quality for true, podemos ajustar a configuração para capturar em resolução maior
  // ou ajustar outros parâmetros de qualidade (isso exigiria implementação adicional)

  // Reiniciar a sessão com a mesma câmera
  bool success = StartCameraSession(WideToUtf8(current_id));
  if (!success) {
    return {};
  }
  
  // Esperar um pouco para que a câmera inicialize e comece a produzir frames
  std::this_thread::sleep_for(std::chrono::milliseconds(500));
  
  // Tentar capturar um frame da câmera reiniciada
  std::unique_lock<std::mutex> lock(frame_mutex_);
  
  // Esperar por no máximo 2 segundos por um novo frame (tempo maior após reinicialização)
  auto status = frame_cv_.wait_for(lock, std::chrono::seconds(2),
                                 [this] { return new_frame_available_; });
  if (!status) {
    return {}; // Timeout esperando por um novo frame
  }
  
  // Retornar cópia do frame atual
  std::vector<uint8_t> frame_copy = current_frame_;
  new_frame_available_ = false;
  
  return frame_copy;
}

std::vector<uint8_t> CameraManager::GetLastFrameFromBuffer() {
  std::lock_guard<std::mutex> lock(buffer_mutex_);
  
  if (frame_ring_buffer_.empty()) {
    return {};
  }
  
  return frame_ring_buffer_.back().data;
}

void CameraManager::FrameCaptureThread() {
  // Configurar prioridade da thread para tempo real para melhorar o FPS
  SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_HIGHEST);
  
  // Calcular tempo entre frames para 30 FPS
  const auto frame_interval = std::chrono::milliseconds(33); // ~30 FPS
  auto last_frame_time = std::chrono::high_resolution_clock::now();
  
  while (thread_running_ && session_active_ && source_reader_) {
    // Verificar se já é hora de capturar um novo frame (controle de taxa de frames)
    auto now = std::chrono::high_resolution_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - last_frame_time);
    
    if (elapsed >= frame_interval) {
      // Solicitar um novo sample
      IMFSample* sample = nullptr;
      DWORD stream_flags = 0;
      LONGLONG timestamp = 0;

      HRESULT hr = source_reader_->ReadSample(
          (DWORD)MF_SOURCE_READER_FIRST_VIDEO_STREAM,
          0,
          nullptr,
          &stream_flags,
          &timestamp,
          &sample);

      if (SUCCEEDED(hr) && sample) {
        ProcessFrame(sample);
        sample->Release();
        last_frame_time = now;
      }
    } else {
      // Dormir pelo tempo restante para atingir a taxa de frames desejada
      auto sleep_time = frame_interval - elapsed;
      if (sleep_time > std::chrono::milliseconds(0)) {
        std::this_thread::sleep_for(sleep_time);
      }
    }
  }
}

bool CameraManager::ProcessFrame(IMFSample* sample) {
  if (!sample) {
    return false;
  }
  
  // Obter buffer do sample
  IMFMediaBuffer* buffer = nullptr;
  HRESULT hr = sample->GetBufferByIndex(0, &buffer);
  if (FAILED(hr)) {
    return false;
  }
  
  // Bloquear buffer para leitura
  BYTE* data = nullptr;
  DWORD max_length = 0;
  DWORD current_length = 0;
  
  hr = buffer->Lock(&data, &max_length, &current_length);
  if (FAILED(hr)) {
    buffer->Release();
    return false;
  }
  
  // Obter informações sobre o formato de mídia
  IMFMediaType* media_type = nullptr;
  hr = source_reader_->GetCurrentMediaType(
      (DWORD)MF_SOURCE_READER_FIRST_VIDEO_STREAM,
      &media_type);
  
  if (FAILED(hr)) {
    buffer->Unlock();
    buffer->Release();
    return false;
  }
  
  // Obter dimensões do frame
  UINT32 width = 0, height = 0;
  hr = MFGetAttributeSize(media_type, MF_MT_FRAME_SIZE, &width, &height);
  media_type->Release();
  
  if (FAILED(hr)) {
    buffer->Unlock();
    buffer->Release();
    return false;
  }
  
  // Aplicar ajustes de imagem se necessário
  UINT32 stride = width * 4;  // 4 bytes por pixel (RGBA)
  ApplyImageAdjustments(data, width, height, stride);
  
  // Criar buffer BMP
  std::vector<BYTE> bmp_data;
  if (!FrameToBMP(data, width, height, stride, bmp_data)) {
    buffer->Unlock();
    buffer->Release();
    return false;
  }
  
  // Desbloquear buffer original
  buffer->Unlock();
  buffer->Release();
  
  // Atualizar frame atual
  {
    std::lock_guard<std::mutex> lock(frame_mutex_);
    current_frame_ = std::move(bmp_data);
    new_frame_available_ = true;
  }
  
  // Notificar que um novo frame está disponível
  frame_cv_.notify_one();
  
  return true;
}

bool CameraManager::FrameToBMP(BYTE* data, UINT width, UINT height, UINT stride, std::vector<BYTE>& bmpData) {
  if (!data || width == 0 || height == 0) {
    return false;
  }
  
  // Tamanho do cabeçalho BMP
  const int header_size = 54;
  
  // Calcular tamanho total do arquivo BMP
  UINT row_size = (width * 3 + 3) & ~3;  // Cada linha deve ser múltipla de 4 bytes
  UINT data_size = row_size * height;
  UINT file_size = header_size + data_size;
  
  // Redimensionar o vetor para comportar os dados
  bmpData.resize(file_size);
  
  // Preencher cabeçalho BMP
  BYTE* header = bmpData.data();
  
  // Cabeçalho do arquivo BMP
  header[0] = 'B';
  header[1] = 'M';
  *(UINT32*)(header + 2) = file_size;
  *(UINT32*)(header + 6) = 0;
  *(UINT32*)(header + 10) = header_size;
  
  // Cabeçalho de informações DIB
  *(UINT32*)(header + 14) = 40;              // Tamanho do cabeçalho DIB
  *(INT32*)(header + 18) = width;            // Largura
  *(INT32*)(header + 22) = -((INT32)height); // Altura (negativa para orientação de cima para baixo)
  *(UINT16*)(header + 26) = 1;               // Planos
  *(UINT16*)(header + 28) = 24;              // Bits por pixel (BGR)
  *(UINT32*)(header + 30) = 0;               // Sem compressão
  *(UINT32*)(header + 34) = data_size;       // Tamanho dos dados
  *(INT32*)(header + 38) = 0;                // Resolução horizontal
  *(INT32*)(header + 42) = 0;                // Resolução vertical
  *(UINT32*)(header + 46) = 0;               // Cores na paleta
  *(UINT32*)(header + 50) = 0;               // Todas as cores são importantes
  
  // Copiar os dados da imagem (converter de BGRA para BGR)
  BYTE* dst = bmpData.data() + header_size;
  
  for (UINT y = 0; y < height; y++) {
    BYTE* src_row = data + y * stride;
    BYTE* dst_row = dst + y * row_size;
    
    for (UINT x = 0; x < width; x++) {
      // Copiar BGR (ignorar canal alfa)
      dst_row[0] = src_row[0];  // B
      dst_row[1] = src_row[1];  // G
      dst_row[2] = src_row[2];  // R
      
      src_row += 4;   // BGRA
      dst_row += 3;   // BGR
    }
  }
  
  return true;
}

bool CameraManager::StartCameraSessionWithConfig(
    const std::string& camera_id,
    const CameraResolution& resolution,
    const ImageAdjustments& adjustments) {
    
  // Primeiro parar qualquer sessão existente
  StopCameraSession();
  
  // Salvar configurações
  current_resolution_ = resolution;
  current_adjustments_ = adjustments;
  
  // Iniciar a sessão com as novas configurações
  return StartCameraSession(camera_id);
}

std::vector<uint8_t> CameraManager::CaptureFrameWithAdjustments(
    const ImageAdjustments& adjustments,
    bool force_capture) {
    
  if (!session_active_ || !source_reader_) {
    return {};
  }
  
  auto start_time = std::chrono::high_resolution_clock::now();
  
  // Salvar ajustes atuais
  ImageAdjustments original_adjustments = current_adjustments_;
  
  // Aplicar novos ajustes temporariamente
  current_adjustments_ = adjustments;
  
  // Usar um timeout para evitar bloqueio indefinido
  std::unique_lock<std::mutex> lock(buffer_mutex_, std::defer_lock);
  if (!lock.try_lock_for(std::chrono::milliseconds(force_capture ? 50 : 5))) {
    // Restaurar ajustes originais antes de retornar
    current_adjustments_ = original_adjustments;
    return {}; // Não conseguiu obter o lock no tempo determinado
  }
  
  // Verificar o buffer ring primeiro, mas aplicar ajustes personalizados
  std::vector<uint8_t> result;
  
  if (!frame_ring_buffer_.empty()) {
    auto now = std::chrono::steady_clock::now();
    auto& latest_frame = frame_ring_buffer_.back();
    
    // Verificar se o frame não é muito antigo
    auto age = std::chrono::duration_cast<std::chrono::milliseconds>(
        now - latest_frame.timestamp).count();
    
    if (age < 100 || !force_capture) { // 100ms é fresco o suficiente
      // Copiar os dados para aplicar os ajustes
      result = latest_frame.data;
      
      // Liberar o lock do buffer enquanto processamos
      lock.unlock();
      
      // Aplicar ajustes específicos a esta cópia
      if (result.size() >= (latest_frame.width * latest_frame.height * 4)) {
        BYTE* data_ptr = result.data();
        UINT stride = latest_frame.width * 4;
        
        // Aplicar ajustes na cópia
        ApplyImageAdjustments(data_ptr, latest_frame.width, latest_frame.height, stride);
        
        // Restaurar ajustes originais
        current_adjustments_ = original_adjustments;
        
        // Registrar tempo de processamento
        auto end_time = std::chrono::high_resolution_clock::now();
        double processing_time = std::chrono::duration<double, std::milli>(
            end_time - start_time).count();
        TrackProcessingTime(processing_time);
        
        return result;
      }
    }
  }
  
  // Se chegamos aqui, precisamos capturar um novo frame
  lock.unlock();
  
  // Aguardar por um novo frame com timeout
  {
    std::unique_lock<std::mutex> frame_lock(frame_mutex_);
    new_frame_available_ = false;
    
    // Definir tempo máximo de espera
    auto wait_time = std::chrono::milliseconds(force_capture ? 200 : 50);
    
    // Aguardar por um novo frame ou timeout
    if (!frame_condition_.wait_for(frame_lock, wait_time, [this] { return new_frame_available_.load(); })) {
      // Timeout - tentar usar o último frame disponível no buffer
      auto emergency_frame = GetLastFrameFromBuffer();
      
      // Restaurar ajustes originais
      current_adjustments_ = original_adjustments;
      
      return emergency_frame;
    }
  }
  
  // Obtém o frame mais recente
  {
    std::lock_guard<std::mutex> buffer_lock(buffer_mutex_);
    if (frame_ring_buffer_.empty()) {
      // Restaurar ajustes originais
      current_adjustments_ = original_adjustments;
      return {};
    }
    
    auto& latest_frame = frame_ring_buffer_.back();
    result = latest_frame.data;
  }
  
  // Restaurar ajustes originais
  current_adjustments_ = original_adjustments;
  
  // Registrar tempo de processamento para ajuste adaptativo
  auto end_time = std::chrono::high_resolution_clock::now();
  double processing_time = std::chrono::duration<double, std::milli>(
      end_time - start_time).count();
  TrackProcessingTime(processing_time);
  
  return result;
}

bool CameraManager::SetResolution(uint32_t width, uint32_t height) {
  if (!session_active_ || source_reader_ == nullptr) {
    current_resolution_ = CameraResolution(width, height);
    return false;
  }
  
  // Verificar se a resolução desejada está na lista de resoluções suportadas
  bool resolution_supported = false;
  for (const auto& res : supported_resolutions_) {
    if (res.width == width && res.height == height) {
      resolution_supported = true;
      break;
    }
  }
  
  // Se a resolução não for suportada diretamente, encontrar a mais próxima
  if (!resolution_supported) {
    if (!FindClosestResolution(width, height)) {
      return false;
    }
  }
  
  // Configurar formato de mídia para a nova resolução
  IMFMediaType* media_type = nullptr;
  HRESULT hr = MFCreateMediaType(&media_type);
  if (FAILED(hr)) {
    return false;
  }
  
  // Configurar o tipo de mídia
  hr = media_type->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video);
  if (SUCCEEDED(hr)) {
    hr = media_type->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_RGB32);
  }
  
  // Definir a resolução
  if (SUCCEEDED(hr)) {
    hr = MFSetAttributeSize(media_type, MF_MT_FRAME_SIZE, width, height);
  }
  
  // Definir taxa de quadros (30 FPS)
  if (SUCCEEDED(hr)) {
    hr = MFSetAttributeRatio(media_type, MF_MT_FRAME_RATE, 30, 1);
  }
  
  // Configurar a saída do source reader
  if (SUCCEEDED(hr)) {
    hr = source_reader_->SetCurrentMediaType(
        (DWORD)MF_SOURCE_READER_FIRST_VIDEO_STREAM,
        NULL,
        media_type);
  }
  
  // Liberar o tipo de mídia
  if (media_type) {
    media_type->Release();
  }
  
  // Atualizar a resolução atual
  if (SUCCEEDED(hr)) {
    current_resolution_ = CameraResolution(width, height);
    return true;
  }
  
  return false;
}

CameraResolution CameraManager::GetCurrentResolution() const {
  return current_resolution_;
}

flutter::EncodableList CameraManager::GetAvailableResolutions() {
  flutter::EncodableList result;
  
  if (!session_active_) {
    // Se não houver sessão ativa, retornar apenas resoluções comuns
    result.push_back(flutter::EncodableValue(RESOLUTION_VGA.ToEncodableMap()));
    result.push_back(flutter::EncodableValue(RESOLUTION_HD.ToEncodableMap()));
    result.push_back(flutter::EncodableValue(RESOLUTION_FULL_HD.ToEncodableMap()));
    return result;
  }
  
  // Garantir que temos uma lista atualizada de resoluções
  if (supported_resolutions_.empty()) {
    EnumerateSupportedResolutions();
  }
  
  // Converter a lista de resoluções suportadas para EncodableList
  for (const auto& res : supported_resolutions_) {
    result.push_back(flutter::EncodableValue(res.ToEncodableMap()));
  }
  
  return result;
}

bool CameraManager::EnumerateSupportedResolutions() {
  if (!session_active_ || source_reader_ == nullptr) {
    return false;
  }
  
  supported_resolutions_.clear();
  
  // Adicionar resoluções comuns
  supported_resolutions_.push_back(RESOLUTION_VGA);
  supported_resolutions_.push_back(RESOLUTION_HD);
  supported_resolutions_.push_back(RESOLUTION_FULL_HD);
  
  // Tentar obter resoluções suportadas pela câmera
  IMFMediaType* native_type = nullptr;
  HRESULT hr = source_reader_->GetNativeMediaType(
      (DWORD)MF_SOURCE_READER_FIRST_VIDEO_STREAM,
      0,  // Índice do tipo de mídia
      &native_type);
  
  DWORD count = 0;
  while (SUCCEEDED(hr)) {
    // Obter a resolução do tipo de mídia
    UINT32 width = 0, height = 0;
    hr = MFGetAttributeSize(native_type, MF_MT_FRAME_SIZE, &width, &height);
    
    if (SUCCEEDED(hr)) {
      // Adicionar à lista se ainda não existir
      CameraResolution res(width, height);
      if (std::find(supported_resolutions_.begin(), supported_resolutions_.end(), res) == supported_resolutions_.end()) {
        supported_resolutions_.push_back(res);
      }
    }
    
    // Liberar o tipo de mídia
    native_type->Release();
    native_type = nullptr;
    
    // Tentar obter o próximo tipo de mídia
    count++;
    hr = source_reader_->GetNativeMediaType(
        (DWORD)MF_SOURCE_READER_FIRST_VIDEO_STREAM,
        count,
        &native_type);
  }
  
  // Ordenar resoluções por tamanho
  std::sort(supported_resolutions_.begin(), supported_resolutions_.end());
  
  return !supported_resolutions_.empty();
}

bool CameraManager::FindClosestResolution(uint32_t& width, uint32_t& height) {
  if (supported_resolutions_.empty()) {
    return false;
  }
  
  // Encontrar a resolução mais próxima em termos de número total de pixels
  uint32_t target_pixels = width * height;
  
  size_t closest_index = 0;
  uint32_t closest_diff = UINT32_MAX;
  
  for (size_t i = 0; i < supported_resolutions_.size(); i++) {
    const auto& res = supported_resolutions_[i];
    uint32_t res_pixels = res.width * res.height;
    uint32_t diff = (res_pixels > target_pixels) ? (res_pixels - target_pixels) : (target_pixels - res_pixels);
    
    if (diff < closest_diff) {
      closest_diff = diff;
      closest_index = i;
    }
  }
  
  // Atualizar os valores de largura e altura
  width = supported_resolutions_[closest_index].width;
  height = supported_resolutions_[closest_index].height;
  
  return true;
}

bool CameraManager::SetImageAdjustments(const flutter::EncodableMap& adjustments_map) {
  current_adjustments_ = ImageAdjustments::FromEncodableMap(adjustments_map);
  return true;
}

flutter::EncodableMap CameraManager::GetCurrentImageAdjustments() const {
  return current_adjustments_.ToEncodableMap();
}

bool CameraManager::ApplyImageAdjustments(BYTE* data, UINT width, UINT height, UINT stride) {
  if (!current_adjustments_.use_hardware_acceleration || !hardware_acceleration_initialized_) {
    // Implementação em software (CPU)
    return ApplyImageAdjustmentsSoftware(data, width, height, stride);
  }
  
  // Implementação em hardware (GPU)
  return ApplyImageAdjustmentsHardware(data, width, height, stride);
}

bool CameraManager::ApplyImageAdjustmentsSoftware(BYTE* data, UINT width, UINT height, UINT stride) {
  if (data == nullptr || width == 0 || height == 0 || stride == 0) {
    return false;
  }
  
  // ======== IMPLEMENTAR ZOOM ========
  // Aplicar zoom digital se o nível de zoom for maior que 1
  if (current_zoom_level_ > 1.01) {
    // Criar um buffer temporário para armazenar a imagem original
    std::vector<BYTE> temp_buffer(stride * height);
    memcpy(temp_buffer.data(), data, stride * height);
    
    // Calcular o retângulo de recorte centralizado
    float zoom = static_cast<float>(current_zoom_level_);
    UINT crop_width = static_cast<UINT>(width / zoom);
    UINT crop_height = static_cast<UINT>(height / zoom);
    UINT crop_x = (width - crop_width) / 2;
    UINT crop_y = (height - crop_height) / 2;
    
    // Limites de segurança
    if (crop_width < 1) crop_width = 1;
    if (crop_height < 1) crop_height = 1;
    if (crop_x + crop_width > width) crop_x = width - crop_width;
    if (crop_y + crop_height > height) crop_y = height - crop_height;
    
    // Limpar os dados originais (preencher com preto)
    memset(data, 0, stride * height);
    
    // Redimensionar a região recortada de volta para o tamanho completo com interpolação bilinear
    for (UINT y = 0; y < height; y++) {
      for (UINT x = 0; x < width; x++) {
        // Mapear coordenadas do destino para a região de origem (recorte)
        float src_x = crop_x + (static_cast<float>(x) / width) * crop_width;
        float src_y = crop_y + (static_cast<float>(y) / height) * crop_height;
        
        // Coordenadas inteiras para interpolação
        UINT src_x_int = static_cast<UINT>(src_x);
        UINT src_y_int = static_cast<UINT>(src_y);
        
        // Garantir que estamos dentro dos limites
        if (src_x_int + 1 >= width || src_y_int + 1 >= height) {
          continue;
        }
        
        // Pesos para interpolação bilinear
        float weight_x = src_x - src_x_int;
        float weight_y = src_y - src_y_int;
        
        // Índices dos quatro pixels vizinhos
        UINT idx_tl = src_y_int * stride + src_x_int * 4;
        UINT idx_tr = src_y_int * stride + (src_x_int + 1) * 4;
        UINT idx_bl = (src_y_int + 1) * stride + src_x_int * 4;
        UINT idx_br = (src_y_int + 1) * stride + (src_x_int + 1) * 4;
        
        // Endereço do pixel de destino
        BYTE* dst_pixel = data + y * stride + x * 4;
        
        // Interpolação para cada canal (B, G, R)
        for (int c = 0; c < 3; c++) {
          float tl = temp_buffer[idx_tl + c];
          float tr = temp_buffer[idx_tr + c];
          float bl = temp_buffer[idx_bl + c];
          float br = temp_buffer[idx_br + c];
          
          // Interpolação bilinear
          float top = tl * (1 - weight_x) + tr * weight_x;
          float bottom = bl * (1 - weight_x) + br * weight_x;
          float result = top * (1 - weight_y) + bottom * weight_y;
          
          dst_pixel[c] = static_cast<BYTE>(result);
        }
        
        // Copiar canal alfa (geralmente 255)
        dst_pixel[3] = temp_buffer[idx_tl + 3];
      }
    }
    
    // Remover o buffer temporário (liberação automática)
  }
  
  // Verificar se há outros ajustes a serem aplicados
  if (current_adjustments_.brightness == 0.0f &&
      current_adjustments_.contrast == 0.0f &&
      current_adjustments_.saturation == 0.0f &&
      current_adjustments_.exposure == 0.0f &&
      current_adjustments_.gain == 1.0f &&
      current_adjustments_.filter.empty()) {
    return true;  // Não há mais ajustes a fazer
  }
  
  // Aplicar brilho e contraste
  float brightness = current_adjustments_.brightness * 255.0f;  // -255 a 255
  float contrast = current_adjustments_.contrast + 1.0f;        // 0 a 2
  float saturation = current_adjustments_.saturation + 1.0f;    // 0 a 2
  float exposure = powf(2.0f, current_adjustments_.exposure);   // 0.5 a 2
  float gain = current_adjustments_.gain;                       // 0 a 2
  
  for (UINT y = 0; y < height; y++) {
    BYTE* pixel = data + y * stride;
    
    for (UINT x = 0; x < width; x++) {
      // Formato BGR32: B, G, R, A
      float b = static_cast<float>(pixel[0]);
      float g = static_cast<float>(pixel[1]);
      float r = static_cast<float>(pixel[2]);
      
      // Aplicar exposição e ganho
      r *= exposure * gain;
      g *= exposure * gain;
      b *= exposure * gain;
      
      // Aplicar saturação
      if (saturation != 1.0f) {
        // Converter para HSL, ajustar S, converter de volta para RGB
        float max_val = std::max(std::max(r, g), b);
        float min_val = std::min(std::min(r, g), b);
        float lum = (max_val + min_val) / 2.0f;
        
        if (max_val != min_val) {
          float sat = (lum <= 127.5f) ? 
              (max_val - min_val) / (max_val + min_val) : 
              (max_val - min_val) / (510.0f - max_val - min_val);
          
          // Ajustar saturação
          sat *= saturation;
          sat = std::min(1.0f, std::max(0.0f, sat));
          
          // Aplicar nova saturação
          float min_new = lum * (1.0f - sat);
          float max_new = lum * (1.0f + sat);
          
          if (r == max_val) {
            r = max_new;
            if (g == min_val) {
              g = min_new;
              b = min_new + (b - min_val) * (max_new - min_new) / (max_val - min_val);
            } else {
              b = min_new;
              g = min_new + (g - min_val) * (max_new - min_new) / (max_val - min_val);
            }
          } else if (g == max_val) {
            g = max_new;
            if (r == min_val) {
              r = min_new;
              b = min_new + (b - min_val) * (max_new - min_new) / (max_val - min_val);
            } else {
              b = min_new;
              r = min_new + (r - min_val) * (max_new - min_new) / (max_val - min_val);
            }
          } else { // b == max_val
            b = max_new;
            if (r == min_val) {
              r = min_new;
              g = min_new + (g - min_val) * (max_new - min_new) / (max_val - min_val);
            } else {
              g = min_new;
              r = min_new + (r - min_val) * (max_new - min_new) / (max_val - min_val);
            }
          }
        }
      }
      
      // Aplicar brilho
      r += brightness;
      g += brightness;
      b += brightness;
      
      // Aplicar contraste
      r = (r - 127.5f) * contrast + 127.5f;
      g = (g - 127.5f) * contrast + 127.5f;
      b = (b - 127.5f) * contrast + 127.5f;
      
      // Limitar valores entre 0 e 255
      pixel[0] = static_cast<BYTE>(std::min(255.0f, std::max(0.0f, b)));
      pixel[1] = static_cast<BYTE>(std::min(255.0f, std::max(0.0f, g)));
      pixel[2] = static_cast<BYTE>(std::min(255.0f, std::max(0.0f, r)));
      
      // Próximo pixel
      pixel += 4;
    }
  }
  
  // Aplicar filtros especiais
  if (!current_adjustments_.filter.empty()) {
    ApplyImageFilter(data, width, height, stride);
  }
  
  return true;
}

bool CameraManager::ApplyImageAdjustmentsHardware(BYTE* data, UINT width, UINT height, UINT stride) {
  if (data == nullptr || !d3d_device_ || !d3d_context_ || !wic_factory_) {
    return false;
  }
  
  // Implementar aplicação de ajustes usando D3D11
  // Esta é uma implementação básica que pode ser expandida conforme necessário
  
  // Criar textura de origem
  D3D11_TEXTURE2D_DESC tex_desc = {};
  tex_desc.Width = width;
  tex_desc.Height = height;
  tex_desc.MipLevels = 1;
  tex_desc.ArraySize = 1;
  tex_desc.Format = DXGI_FORMAT_B8G8R8A8_UNORM;
  tex_desc.SampleDesc.Count = 1;
  tex_desc.Usage = D3D11_USAGE_DEFAULT;
  tex_desc.BindFlags = D3D11_BIND_SHADER_RESOURCE | D3D11_BIND_RENDER_TARGET;
  
  D3D11_SUBRESOURCE_DATA init_data = {};
  init_data.pSysMem = data;
  init_data.SysMemPitch = stride;
  
  Microsoft::WRL::ComPtr<ID3D11Texture2D> src_texture;
  HRESULT hr = d3d_device_->CreateTexture2D(&tex_desc, &init_data, src_texture.GetAddressOf());
  if (FAILED(hr)) {
    return false;
  }
  
  // Criar textura de destino
  Microsoft::WRL::ComPtr<ID3D11Texture2D> dst_texture;
  tex_desc.Usage = D3D11_USAGE_DEFAULT;
  tex_desc.CPUAccessFlags = 0;
  hr = d3d_device_->CreateTexture2D(&tex_desc, nullptr, dst_texture.GetAddressOf());
  if (FAILED(hr)) {
    return false;
  }
  
  // Criar textura de staging para leitura posterior
  if (!staging_texture_) {
    tex_desc.Usage = D3D11_USAGE_STAGING;
    tex_desc.BindFlags = 0;
    tex_desc.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
    hr = d3d_device_->CreateTexture2D(&tex_desc, nullptr, staging_texture_.GetAddressOf());
    if (FAILED(hr)) {
      return false;
    }
  }
  
  // Processar a textura usando recursos do D3D11
  // Aqui, você usaria efeitos e shaders para aplicar os ajustes
  
  // Para este exemplo simplificado, apenas copiamos a textura de origem para a de destino
  d3d_context_->CopyResource(dst_texture.Get(), src_texture.Get());
  
  // Copiar para a textura de staging para leitura pela CPU
  d3d_context_->CopyResource(staging_texture_.Get(), dst_texture.Get());
  
  // Mapear a textura para a CPU para leitura
  D3D11_MAPPED_SUBRESOURCE mapped_resource;
  hr = d3d_context_->Map(staging_texture_.Get(), 0, D3D11_MAP_READ, 0, &mapped_resource);
  if (FAILED(hr)) {
    return false;
  }
  
  // Copiar os dados processados de volta para o buffer original
  BYTE* src_data = static_cast<BYTE*>(mapped_resource.pData);
  UINT src_stride = mapped_resource.RowPitch;
  
  for (UINT y = 0; y < height; y++) {
    memcpy(data + y * stride, src_data + y * src_stride, width * 4);
  }
  
  // Desmaear textura
  d3d_context_->Unmap(staging_texture_.Get(), 0);
  
  return true;
}

bool CameraManager::ApplyImageFilter(BYTE* data, UINT width, UINT height, UINT stride) {
  // Aplicar filtros especiais como sépia, preto e branco, etc.
  if (current_adjustments_.filter == "grayscale" || current_adjustments_.filter == "blackandwhite") {
    for (UINT y = 0; y < height; y++) {
      BYTE* pixel = data + y * stride;
      
      for (UINT x = 0; x < width; x++) {
        // Formato BGR32: B, G, R, A
        BYTE b = pixel[0];
        BYTE g = pixel[1];
        BYTE r = pixel[2];
        
        // Converter para escala de cinza (média ponderada)
        BYTE gray = static_cast<BYTE>(0.299f * r + 0.587f * g + 0.114f * b);
        
        pixel[0] = gray;
        pixel[1] = gray;
        pixel[2] = gray;
        
        // Próximo pixel
        pixel += 4;
      }
    }
  } else if (current_adjustments_.filter == "sepia") {
    for (UINT y = 0; y < height; y++) {
      BYTE* pixel = data + y * stride;
      
      for (UINT x = 0; x < width; x++) {
        // Formato BGR32: B, G, R, A
        float b = static_cast<float>(pixel[0]);
        float g = static_cast<float>(pixel[1]);
        float r = static_cast<float>(pixel[2]);
        
        // Aplicar efeito sépia
        float new_r = std::min(255.0f, (r * 0.393f) + (g * 0.769f) + (b * 0.189f));
        float new_g = std::min(255.0f, (r * 0.349f) + (g * 0.686f) + (b * 0.168f));
        float new_b = std::min(255.0f, (r * 0.272f) + (g * 0.534f) + (b * 0.131f));
        
        pixel[0] = static_cast<BYTE>(new_b);
        pixel[1] = static_cast<BYTE>(new_g);
        pixel[2] = static_cast<BYTE>(new_r);
        
        // Próximo pixel
        pixel += 4;
      }
    }
  } else if (current_adjustments_.filter == "inverted" || current_adjustments_.filter == "negative") {
    for (UINT y = 0; y < height; y++) {
      BYTE* pixel = data + y * stride;
      
      for (UINT x = 0; x < width; x++) {
        // Inverter cores
        pixel[0] = 255 - pixel[0];  // B
        pixel[1] = 255 - pixel[1];  // G
        pixel[2] = 255 - pixel[2];  // R
        
        // Próximo pixel
        pixel += 4;
      }
    }
  }
  
  return true;
}

void CameraManager::TrackProcessingTime(double processing_time) {
  // Adicionar tempo ao histórico
  processing_times_.push_back(processing_time);
  
  // Manter apenas os últimos 30 tempos
  if (processing_times_.size() > 30) {
    processing_times_.erase(processing_times_.begin());
  }
  
  // Analisar desempenho para ajuste adaptativo
  if (processing_times_.size() >= 5 && adaptive_quality_) {
    // Calcular tempo médio de processamento
    double avg_time = 0.0;
    for (const auto& time : processing_times_) {
      avg_time += time;
    }
    avg_time /= processing_times_.size();
    
    // Verificar tempos em relação ao intervalo entre frames
    double target_time = frame_interval_.count() * 0.7; // 70% do intervalo
    
    if (avg_time > target_time) {
      // Processamento está levando muito tempo
      consecutive_slow_frames_++;
      
      if (consecutive_slow_frames_ >= 3) {
        consecutive_slow_frames_ = 0;
        AdaptQualityDown();
      }
    } else if (avg_time < target_time * 0.5) {
      // Processamento está rápido, pode tentar melhorar qualidade
      TryAdaptQualityUp();
    } else {
      // Processamento em faixa aceitável
      consecutive_slow_frames_ = 0;
    }
  }
}

void CameraManager::AdaptQualityDown() {
  // Reduzir frameRate aumentando o intervalo entre frames
  if (frame_interval_.count() < 66) { // Não ir abaixo de 15 FPS (66ms)
    frame_interval_ = std::chrono::milliseconds(
        static_cast<int>(frame_interval_.count() * 1.2));
    
    OutputDebugString(L"Reduzindo qualidade para melhorar desempenho\n");
  }
  
  // Limpar histórico para nova avaliação
  processing_times_.clear();
}

void CameraManager::TryAdaptQualityUp() {
  // Aumentar frameRate reduzindo o intervalo entre frames
  if (frame_interval_.count() > 17) { // Não ir acima de 60 FPS (16.7ms)
    frame_interval_ = std::chrono::milliseconds(
        static_cast<int>(frame_interval_.count() * 0.9));
    
    OutputDebugString(L"Aumentando qualidade, desempenho bom\n");
  }
  
  // Limpar histórico para nova avaliação
  processing_times_.clear();
}

bool CameraManager::FrameToJPEG(BYTE* data, UINT width, UINT height, UINT stride, std::vector<BYTE>& jpegData) {
  if (!data || width == 0 || height == 0) {
    return false;
  }
  
  HRESULT hr = S_OK;
  
  // Usar WIC para conversão para JPEG
  if (!wic_factory_) {
    hr = CoCreateInstance(
        CLSID_WICImagingFactory,
        nullptr,
        CLSCTX_INPROC_SERVER,
        IID_PPV_ARGS(&wic_factory_));
        
    if (FAILED(hr)) {
      return false;
    }
  }
  
  Microsoft::WRL::ComPtr<IWICBitmapEncoder> encoder;
  Microsoft::WRL::ComPtr<IWICBitmapFrameEncode> frame;
  Microsoft::WRL::ComPtr<IWICStream> stream;
  Microsoft::WRL::ComPtr<IStream> memoryStream;
  
  // Criar stream na memória
  hr = CreateStreamOnHGlobal(nullptr, TRUE, &memoryStream);
  if (FAILED(hr)) {
    return false;
  }
  
  // Criar stream WIC
  hr = wic_factory_->CreateStream(&stream);
  if (FAILED(hr)) {
    return false;
  }
  
  // Inicializar stream WIC
  hr = stream->InitializeFromIStream(memoryStream.Get());
  if (FAILED(hr)) {
    return false;
  }
  
  // Criar encoder JPEG
  hr = wic_factory_->CreateEncoder(GUID_ContainerFormatJpeg, nullptr, &encoder);
  if (FAILED(hr)) {
    return false;
  }
  
  // Inicializar encoder
  hr = encoder->Initialize(stream.Get(), WICBitmapEncoderNoCache);
  if (FAILED(hr)) {
    return false;
  }
  
  // Criar frame
  hr = encoder->CreateNewFrame(&frame, nullptr);
  if (FAILED(hr)) {
    return false;
  }
  
  // Inicializar frame
  hr = frame->Initialize(nullptr);
  if (FAILED(hr)) {
    return false;
  }
  
  // Definir tamanho
  hr = frame->SetSize(width, height);
  if (FAILED(hr)) {
    return false;
  }
  
  // Definir formato de pixel (BGRA)
  WICPixelFormatGUID pixelFormat = GUID_WICPixelFormat32bppBGRA;
  hr = frame->SetPixelFormat(&pixelFormat);
  if (FAILED(hr)) {
    return false;
  }
  
  // Escrever pixels
  hr = frame->WritePixels(height, stride, stride * height, data);
  if (FAILED(hr)) {
    return false;
  }
  
  // Commit do frame
  hr = frame->Commit();
  if (FAILED(hr)) {
    return false;
  }
  
  // Commit do encoder
  hr = encoder->Commit();
  if (FAILED(hr)) {
    return false;
  }
  
  // Obter dados do stream
  STATSTG stats;
  hr = memoryStream->Stat(&stats, STATFLAG_NONAME);
  if (FAILED(hr)) {
    return false;
  }
  
  // Alocar buffer para os dados
  jpegData.resize(static_cast<size_t>(stats.cbSize.QuadPart));
  
  // Voltar ao início do stream
  LARGE_INTEGER zero = {0};
  hr = memoryStream->Seek(zero, STREAM_SEEK_SET, nullptr);
  if (FAILED(hr)) {
    return false;
  }
  
  // Ler os dados
  ULONG bytesRead = 0;
  hr = memoryStream->Read(jpegData.data(), static_cast<ULONG>(jpegData.size()), &bytesRead);
  
  return SUCCEEDED(hr) && bytesRead > 0;
}

bool CameraManager::SetZoomLevel(double zoom_level) {
  // Validar entrada
  if (zoom_level < 1.0) {
    zoom_level = 1.0; // zoom mínimo é 1x (sem zoom)
  }
  
  if (zoom_level > max_zoom_level_) {
    zoom_level = max_zoom_level_;
  }
  
  // No Windows, o zoom é implementado em software
  // Armazenamos o nível de zoom e aplicamos durante o processamento de frames
  
  // Bloquear acesso para thread safety
  std::lock_guard<std::mutex> lock(frame_mutex_);
  
  // Atualizar o valor de zoom
  current_zoom_level_ = zoom_level;
  
  // Log para diagnóstico
  std::stringstream ss;
  ss << "Zoom definido para: " << zoom_level << "x";
  OutputDebugStringA(ss.str().c_str());
  
  return true;
}

bool CameraManager::SetWhiteBalance(const std::string& mode) {
  if (!session_active_ || !source_reader_) {
    return false;
  }
  
  // Armazenar o modo de balanço de branco
  current_white_balance_ = mode;
  
  // No Windows, vamos implementar o balanço de branco via software
  // já que o Media Foundation não oferece controle direto para isso
  
  // Atualizar os parâmetros de processamento de imagem
  float temperature = 0.0f;
  
  // Converter o modo para valores de temperatura
  if (mode == "auto") {
    // Em modo auto, não aplicamos ajustes - deixamos o hardware decidir
    return true;
  } else if (mode == "daylight" || mode == "sunny") {
    // Temperatura para luz do dia (aproximadamente 5500K)
    temperature = 5500.0f;
  } else if (mode == "cloudy") {
    // Temperatura para dia nublado (aproximadamente 6500K)
    temperature = 6500.0f;
  } else if (mode == "fluorescent") {
    // Temperatura para luz fluorescente (aproximadamente 4000K)
    temperature = 4000.0f;
  } else if (mode == "incandescent" || mode == "tungsten") {
    // Temperatura para luz incandescente (aproximadamente 2700K)
    temperature = 2700.0f;
  } else {
    // Modo desconhecido, usar auto
    current_white_balance_ = "auto";
    return true;
  }
  
  // Aqui implementaríamos o ajuste em software ou via controles de câmera se disponíveis
  // Esta é uma implementação básica que simula o comportamento
  
  // Atualizar os valores RGB que seriam aplicados no processamento de imagem
  // baseado na temperatura de cor - implementação simplificada
  float red_gain = 1.0f;
  float green_gain = 1.0f;
  float blue_gain = 1.0f;
  
  if (temperature <= 5000.0f) {
    // Para temperaturas mais baixas (amareladas/avermelhadas)
    blue_gain = 0.5f + (temperature / 10000.0f);
    red_gain = 1.0f;
    green_gain = 0.7f + (temperature / 12000.0f);
  } else {
    // Para temperaturas mais altas (azuladas)
    red_gain = 10000.0f / temperature;
    blue_gain = 1.0f;
    green_gain = 0.9f;
  }
  
  // Em uma implementação completa, esses ganhos seriam aplicados durante o processamento de imagem
  // Aqui apenas armazenamos os valores que seriam utilizados pelo processador de imagem
  white_balance_red_gain_ = red_gain;
  white_balance_green_gain_ = green_gain;
  white_balance_blue_gain_ = blue_gain;
  
  // Essas variáveis precisam ser declaradas como membros da classe
  
  return true;
}

}  // namespace camera_access