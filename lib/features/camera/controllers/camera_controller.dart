import 'dart:typed_data';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:camera_access/camera_access.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/design_system/app_toast.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';
import 'package:microdetect/features/settings/services/settings_service.dart';
import 'dart:io';

import '../enums/sidebar_content_enum.dart';
import '../models/camera_image.dart';
import '../models/gallery_image.dart';
import '../services/camera_service.dart';

class CameraController extends GetxController with WidgetsBindingObserver {
  // Dependências
  final CameraAccess _cameraAccess = CameraAccess();
  final CameraService _cameraService = Get.find<CameraService>();
  final SettingsService _settingsService = Get.find<SettingsService>();

  // Parâmetros
  final int? datasetId;

  CameraController({
    this.datasetId,
  });

  // Estado da câmera
  final RxBool _isInitialized = false.obs;
  final RxBool _isImageCaptured = false.obs;
  final Rx<Uint8List?> _capturedFrame = Rx<Uint8List?>(null);
  final Rx<File?> _capturedImageFile = Rx<File?>(null);
  final RxList<CameraDevice> _availableCameras = <CameraDevice>[].obs;
  final RxString _selectedCameraId = ''.obs;

  // Ajustes de imagem
  final RxDouble _brightness = 0.0.obs;
  final RxDouble _contrast = 0.0.obs;
  final RxDouble _saturation = 0.0.obs;
  final RxDouble _sharpness = 0.0.obs;
  final RxString _selectedFilter = 'normal'.obs;

  // Configurações da câmera
  final RxString _currentResolution = 'hd'.obs;
  final RxString _whiteBalance = 'auto'.obs;

  // Estado da UI
  final Rx<SidebarContent> _activeSidebarContent =
      Rx<SidebarContent>(SidebarContent.settings);

  // Lista de imagens
  final RxList<File> _savedImages = <File>[].obs;
  final Rx<List<GalleryImage>> _galleryImages = Rx<List<GalleryImage>>([]);

  // Zoom
  final RxDouble _currentZoom = 1.0.obs;
  final double _maxZoom = 5.0;

  // Configurações de sessão
  static String? _sessionResolution;
  static String? _sessionWhiteBalance;

  // Variáveis auxiliares
  final RxDouble _sidebarWidth = 320.0.obs;
  final RxString _selectedResolution = 'hd'.obs;
  final RxList<String> _availableResolutions =
      <String>['sd', 'fullhd', 'hd'].obs;
  final Rx<String?> _selectedWhiteBalance = 'auto'.obs;
  final RxList<String> _availableWhiteBalances =
      <String>['auto', 'sunny', 'cloudy', 'tungsten', 'fluorescent'].obs;

  // Estado de captura
  final RxBool _isCapturing = false.obs;
  final Rx<CameraImage?> _capturedImage = Rx<CameraImage?>(null);

  // Estado de carregamento
  final RxBool _isLoadingImages = false.obs;

  // Estado de seleção
  final Rx<GalleryImage?> _selectedGalleryImage = Rx<GalleryImage?>(null);
  final RxBool _isSaving = false.obs;
  final Rx<GalleryImage?> _lastSavedImage = Rx<GalleryImage?>(null);
  final Rx<CameraPosition> _cameraPosition =
      Rx<CameraPosition>(CameraPosition.unknown);

  // Dataset selecionado
  final Rx<int?> _selectedDatasetId = Rx<int?>(null);

  // Estado de inicialização
  final RxString _cameraStatus = 'Câmera não inicializada'.obs;
  final RxBool _isCameraLoading = false.obs;

  // Flag para evitar inicializações simultâneas
  bool _isInitializing = false;

  // Timer para captura de frames
  Timer? _frameTimer;

  // Stream de frames
  StreamSubscription? _frameStreamSubscription;

  // Getters para variáveis reativas
  bool get isInitialized => _isInitialized.value;

  bool get isImageCaptured => _isImageCaptured.value;

  Uint8List? get capturedFrame => _capturedFrame.value;

  File? get capturedImageFile => _capturedImageFile.value;

  List<CameraDevice> get availableCameras => _availableCameras;

  String get selectedCameraId => _selectedCameraId.value;

  double get brightness => _brightness.value;

  double get contrast => _contrast.value;

  double get saturation => _saturation.value;

  double get sharpness => _sharpness.value;

  String get selectedFilter => _selectedFilter.value;

  String get currentResolution => _currentResolution.value;

  String get whiteBalance => _whiteBalance.value;

  SidebarContent get activeSidebarContent => _activeSidebarContent.value;

  List<File> get savedImages => _savedImages;

  List<GalleryImage> get galleryImages => _galleryImages.value;

  double get currentZoom => _currentZoom.value;

  double get sidebarWidth => _sidebarWidth.value;

  String get selectedResolution => _selectedResolution.value;

  List<String> get availableResolutions => _availableResolutions;

  String? get selectedWhiteBalance => _selectedWhiteBalance.value;

  List<String> get availableWhiteBalances => _availableWhiteBalances;

  bool get isCapturing => _isCapturing.value;

  CameraImage? get capturedImage => _capturedImage.value;

  bool get isLoadingImages => _isLoadingImages.value;

  GalleryImage? get selectedGalleryImage => _selectedGalleryImage.value;

  bool get isSaving => _isSaving.value;

  GalleryImage? get lastSavedImage => _lastSavedImage.value;

  CameraPosition get cameraPosition => _cameraPosition.value;

  int? get selectedDatasetId => _selectedDatasetId.value;

  String get cameraStatus => _cameraStatus.value;

  bool get isCameraLoading => _isCameraLoading.value;

  @override
  void onInit() {
    super.onInit();
    WidgetsBinding.instance.addObserver(this);

    // Inicializar dataset selecionado
    _selectedDatasetId.value = datasetId;

    _initializeCamera();

    loadSavedImages();
  }


  /// Atualiza o status da câmera
  void _updateCameraStatus(String status, {bool isLoading = false}) {
    _cameraStatus.value = status;
    _isCameraLoading.value = isLoading;
  }

  /// Inicializa uma câmera específica por ID
  Future<void> initializeSpecificCamera(String cameraId) async {
    if (_isInitializing) {
      return;
    }

    // Obter o nome da câmera para mensagens mais informativas
    String cameraName = 'Câmera selecionada';
    try {
      final camera = _availableCameras.firstWhere((cam) => cam.id == cameraId);
      cameraName = camera.name;
    } catch (_) {}

    _selectedCameraId.value = cameraId;

    // Atualizar status para feedback imediato ao usuário
    _updateCameraStatus('Inicializando $cameraName...', isLoading: true);

    try {
      // Sempre interromper a câmera atual primeiro
      if (_isInitialized.value) {
        await _stopCamera();

        // Aguardar para garantir que os recursos sejam liberados
        await Future.delayed(const Duration(milliseconds: 500));
      }

      // Resetar contadores e estados
      _isInitializing =
          false; // Reset para garantir que possamos começar novamente
      _isInitialized.value = false;
      _capturedFrame.value = null; // Limpar qualquer frame anterior

      // Inicialização padrão para todas as câmeras
      await _initializeCamera(forceCameraId: cameraId);
    } catch (e) {
      _updateCameraStatus('Erro ao inicializar $cameraName', isLoading: false);
    }
  }

  /// Inicializa a câmera
  Future<void> _initializeCamera({String? forceCameraId}) async {
    if (_isInitializing) {
      return;
    }

    _isInitializing = true;
    _updateCameraStatus('Inicializando câmera...', isLoading: true);

    try {
      // 1. Parar qualquer sessão existente
      await _cameraAccess
          .stopCameraSession()
          .timeout(
            const Duration(seconds: 2),
            onTimeout: () => true,
          )
          .catchError((_) => true);

      // 2. Verificar permissão
      final hasPermission = await _cameraAccess.hasPermission();
      if (!hasPermission) {
        final permissionGranted = await _cameraAccess.requestPermission();
        if (!permissionGranted) {
          _updateCameraStatus('Permissão da câmera negada', isLoading: false);
          _isInitializing = false;
          return;
        }
      }

      // 3. Obter câmeras disponíveis
      final cameras = await _cameraAccess.getAvailableCameras();
      _availableCameras.value = cameras;

      if (cameras.isEmpty) {
        _updateCameraStatus('Nenhuma câmera encontrada', isLoading: false);
        _isInitializing = false;
        return;
      }

      // 4. Selecionar câmera
      String cameraId;

      if (forceCameraId != null &&
          cameras.any((cam) => cam.id == forceCameraId)) {
        // Usar câmera específica se solicitada
        cameraId = forceCameraId;
      } else {
        // Lógica prioritária: última usada → externa → unknown → qualquer uma
        final lastId = _settingsService.settings.lastCameraId;

        if (lastId.isNotEmpty && cameras.any((cam) => cam.id == lastId)) {
          cameraId = lastId;
        } else if (cameras
            .any((cam) => cam.position == CameraPosition.external)) {
          cameraId = cameras
              .firstWhere((cam) => cam.position == CameraPosition.external)
              .id;
        } else if (cameras
            .any((cam) => cam.position == CameraPosition.unknown)) {
          cameraId = cameras
              .firstWhere((cam) => cam.position == CameraPosition.unknown)
              .id;
        } else {
          cameraId = cameras.first.id;
        }
      }

      _selectedCameraId.value = cameraId;

      // 5. Iniciar sessão da câmera
      final camera = cameras.firstWhere((cam) => cam.id == cameraId);
      _updateCameraStatus('Conectando à ${camera.name}...', isLoading: true);

      final success = await _cameraAccess
          .startCameraSession(cameraId)
          .timeout(const Duration(seconds: 10), onTimeout: () => false);

      if (!success) {
        _updateCameraStatus('Falha ao conectar à câmera', isLoading: false);
        _isInitializing = false;
        return;
      }

      // 6. Configurar câmera
      _isInitialized.value = true;
      final settings = _settingsService.settings;
      _currentResolution.value =
          _sessionResolution ?? settings.defaultResolution;
      _selectedResolution.value = _currentResolution.value;
      _whiteBalance.value =
          _sessionWhiteBalance ?? settings.defaultWhiteBalance;
      _selectedWhiteBalance.value = _whiteBalance.value;

      // 7. Iniciar escuta do frameStream nativo do plugin
      _listenToFrameStream();

      // 8. Aplicar configurações em background
      Future.microtask(() async {
        await _applyResolution(_currentResolution.value).catchError((_) {});
        await _cameraAccess
            .setWhiteBalance(_whiteBalance.value)
            .catchError((_) {});
        await _settingsService.updatePartialSettings(lastCameraId: cameraId);
      });

      _updateCameraStatus('Câmera pronta', isLoading: false);
    } catch (e) {
      _updateCameraStatus('Erro ao inicializar câmera', isLoading: false);
      _isInitialized.value = false;
    } finally {
      _isInitializing = false;
    }
  }

  /// Atualiza a lista de câmeras disponíveis
  Future<void> refreshCameras() async {
    final cameras = await _cameraAccess.getAvailableCameras();
    _availableCameras.value = cameras;
  }

  /// Altera a câmera em uso
  Future<void> changeCamera(String cameraId) async {
    if (cameraId == _selectedCameraId.value) return;

    _isInitialized.value = false;

    // Parar a sessão atual
    await _cameraAccess.stopCameraSession();

    // Iniciar nova sessão com a câmera selecionada
    final success = await _cameraAccess.startCameraSession(cameraId);

    if (success) {
      _selectedCameraId.value = cameraId;
      _isInitialized.value = true;

      // Reaplicar os ajustes
      _applyImageAdjustments();
    } else {
      // Se falhar, tente voltar para a câmera anterior
      await _cameraAccess.startCameraSession(_selectedCameraId.value);

      AppToast.error(
        'Erro',
        description: 'Falha ao alterar para a câmera selecionada',
      );
    }
  }

  /// Carrega as imagens salvas da galeria
  Future<void> loadSavedImages() async {
    _isLoadingImages.value = true;

    try {
      final images = await _cameraService.loadGalleryImages(
        datasetId: datasetId,
      );

      _galleryImages.value = images;
    } catch (e) {
      AppToast.error(
        'Erro',
        description: 'Erro ao carregar imagens: $e',
      );
    } finally {
      _isLoadingImages.value = false;
    }
  }

  /// Captura uma imagem da câmera
  Future<void> captureImage() async {
    if (!_isInitialized.value) return;

    try {
      _isCapturing.value = true;

      // Usar o método captureImage que aplica ajustes automaticamente
      final capturedImage = await _cameraAccess.captureImage(
        applyAdjustments: true,
        brightness: _brightness.value,
        contrast: _contrast.value,
        saturation: _saturation.value,
        sharpness: _sharpness.value,
        filter:
            _selectedFilter.value != 'normal' ? _selectedFilter.value : null,
      );

      if (capturedImage != null) {
        _capturedFrame.value = capturedImage.bytes;
        _isImageCaptured.value = true;
      } else {
        // Tentar método alternativo com captureFrame
        final frameData = await _cameraAccess.captureFrame(forceCapture: true);

        if (frameData != null) {
          _capturedFrame.value = frameData;
          _isImageCaptured.value = true;
        } else {
          throw Exception('Falha ao capturar imagem');
        }
      }
    } catch (e) {
      // Mostrar mensagem de erro
      AppToast.error(
        'Erro',
        description: 'Erro ao capturar imagem',
      );
    } finally {
      _isCapturing.value = false;
    }
  }

  /// Descarta a imagem capturada
  void discardCapturedImage() {
    _capturedFrame.value = null;
    _isImageCaptured.value = false;
    _capturedImageFile.value = null;
  }

  /// Salva a imagem capturada
  Future<void> saveImage(CameraImage cameraImage) async {
    _isSaving.value = true;

    try {
      // Verificar se a API está disponível
      if (!_cameraService.isApiInitialized) {
        AppToast.error(
          'Erro',
          description: 'API não inicializada. Não é possível salvar imagens.',
        );
        _isSaving.value = false;
        return;
      }

      // Converter a imagem para bytes PNG se necessário
      final Uint8List imageBytes = cameraImage.bytes ??
          await FlutterImageCompress.compressWithList(
            cameraImage.rawBytes!,
            quality: 90,
            format: CompressFormat.png,
          );

      // Preparar metadados relevantes
      final timestamp = DateTime.now();
      final fileName = 'image_${timestamp.millisecondsSinceEpoch}.png';

      // Metadados para a imagem
      final Map<String, dynamic> metadata = {
        'timestamp': timestamp.toIso8601String(),
        'adjustments': _getImageAdjustments(),
        'cameraSettings': _getCameraSettings(),
        'isProcessed': cameraImage.isProcessed,
      };

      // Usar o dataset selecionado (ou o passado pelo widget)
      final datasetId = _selectedDatasetId.value ?? this.datasetId;

      if (datasetId != null) {
        metadata['datasetId'] = datasetId;
      }

      // Usar o serviço para fazer upload da imagem
      final savedImage = await _cameraService.saveImage(
        imageBytes: imageBytes,
        fileName: fileName,
        datasetId: datasetId,
        metadata: metadata,
      );

      AppToast.success(
        'Sucesso',
        description: 'Imagem salva com sucesso!',
      );

      _lastSavedImage.value = savedImage;

      // Voltar para o modo preview
      discardCapturedImage();

      // Mudar para a galeria e atualizar a lista
      _activeSidebarContent.value = SidebarContent.gallery;
      await showGallery(); // Carregar imagens na galeria
    } catch (e) {
      AppToast.error(
        'Erro',
        description: 'Erro ao salvar imagem: ${e.toString()}',
      );
    } finally {
      _isSaving.value = false;
    }
  }

  /// Obtém os ajustes atuais da imagem como metadados
  Map<String, dynamic> _getImageAdjustments() {
    return {
      'brightness': _brightness.value,
      'contrast': _contrast.value,
      'saturation': _saturation.value,
      'sharpness': _sharpness.value,
    };
  }

  /// Obtém as configurações atuais da câmera como metadados
  Map<String, dynamic> _getCameraSettings() {
    return {
      'resolution': _selectedResolution.value?.toString(),
      'whiteBalance': _selectedWhiteBalance.value?.toString(),
      'zoomLevel': _currentZoom.value,
      'cameraPosition': _cameraPosition.value.toString(),
    };
  }

  /// Exibe a galeria de imagens
  Future<void> showGallery({int? datasetId}) async {
    _isLoadingImages.value = true;

    try {
      // Usar o datasetId passado como parâmetro, se disponível, ou o armazenado no controller
      final targetDatasetId = datasetId ?? this.datasetId;

      final images = await _cameraService.loadGalleryImages(
        datasetId: targetDatasetId,
      );

      _galleryImages.value = images;
    } catch (e) {
      AppToast.error(
        'Erro',
        description: 'Erro ao carregar galeria: ${e.toString()}',
        duration: const Duration(seconds: 3),
      );

      _galleryImages.value = [];
    } finally {
      _isLoadingImages.value = false;
    }
  }

  /// Define diretamente a lista de imagens da galeria
  void setGalleryImages(List<GalleryImage> images) {
    _galleryImages.value = images;
  }

  /// Manipula a seleção de uma imagem da galeria
  void handleImageSelected(GalleryImage image) {
    _selectedGalleryImage.value = image;

    // Aqui você pode adicionar a lógica para mostrar um diálogo ou navegar para visualização
    // Essa parte será implementada na página usando o Get.dialog
  }

  /// Exclui uma imagem da galeria
  Future<void> deleteImage(GalleryImage image) async {
    try {
      final success = await _cameraService.deleteImage(image);

      if (success) {
        AppToast.success(
          'Sucesso',
          description: 'Imagem excluída com sucesso',
        );

        // Recarregar a galeria
        await showGallery();
      } else {
        throw Exception('Não foi possível excluir a imagem');
      }
    } catch (e) {
      AppToast.error(
        'Erro',
        description: 'Erro ao excluir imagem: ${e.toString()}',
      );
    }
  }

  /// Aplica zoom na câmera
  Future<void> handleZoom(bool zoomIn) async {
    if (_isImageCaptured.value) return;

    double newZoom;
    try {
      // Calcular o novo nível de zoom baseado na direção (zoom in ou zoom out)
      if (zoomIn) {
        newZoom = (_currentZoom.value + 0.1).clamp(1.0, _maxZoom);
      } else {
        newZoom = (_currentZoom.value - 0.1).clamp(1.0, _maxZoom);
      }

      // Aplicar o novo zoom apenas se mudou
      if (newZoom != _currentZoom.value) {
        final success = await _cameraAccess.setZoomLevel(newZoom);
        if (success) {
          _currentZoom.value = newZoom;
        }
      }
    } catch (e) {
      LoggerUtil.error('Erro ao ajustar zoom', e);
    }
  }

  /// Callback para mudança de filtro
  void handleFilterChanged(String filter) {

    // Forçar uma atualização de estado mesmo se for o mesmo filtro (para garantir que "normal" sempre será aplicado)
    if (filter == 'normal' || filter != _selectedFilter.value) {
      _selectedFilter.value = filter;

      // Se for o filtro normal, podemos forçar uma "mudança" para garantir que os ajustes sejam reaplicados
      if (filter == 'normal') {
        // Um pequeno "hack" para forçar a atualização da câmera
        _brightness.value = _brightness.value - 0.001;
        Future.delayed(Duration(milliseconds: 50), () {
          _brightness.value = _brightness.value + 0.001;
        });
      }

      _applyImageAdjustments();
    }
  }

  /// Aplica a resolução especificada à câmera
  Future<void> _applyResolution(String resolution) async {
    try {
      // Converter string para objeto CameraResolution
      CameraResolution cameraResolution;

      switch (resolution) {
        case 'sd':
          cameraResolution = const CameraResolution(640, 480);
          break;
        case 'fullhd':
          cameraResolution = const CameraResolution(1920, 1080);
          break;
        case 'hd':
        default:
          cameraResolution = const CameraResolution(1280, 720);
          break;
      }

      // Aplicar resolução via plugin de câmera
      bool success = await _cameraAccess.setResolution(cameraResolution);

      if (success) {
        // Atualizar a variável estática para manter entre sessões
        _sessionResolution = resolution;
      } else {
        AppToast.warning('Aviso',
            description:
                'AVISO: Falha ao aplicar resolução. Mantendo resolução de sessão anterior: $_sessionResolution');
      }
    } catch (e) {
      AppToast.error('Erro', description: 'Erro ao alterar resolução: $e');
    }
  }

  /// Callback para mudança de resolução
  Future<void> handleResolutionChanged(String resolution) async {
    if (_currentResolution.value == resolution) {
      return;
    }

    // Atualizar a resolução atual na UI
    _currentResolution.value = resolution;
    _selectedResolution.value = resolution;

    // Aplicar a resolução - isso vai atualizar _sessionResolution se for bem sucedido
    await _applyResolution(resolution);

    // Garantir que a UI reflita a resolução que foi realmente aplicada
    if (_sessionResolution != null &&
        _sessionResolution != _currentResolution.value) {
      _currentResolution.value = _sessionResolution!;
      _selectedResolution.value = _sessionResolution!;
    }
  }

  /// Callback para mudança de balanço de branco
  Future<void> handleWhiteBalanceChanged(String mode) async {
    if (_whiteBalance.value == mode) return;

    _whiteBalance.value = mode;
    _selectedWhiteBalance.value = mode;

    // Armazenar o balanço de branco escolhido durante a sessão
    _sessionWhiteBalance = mode;

    try {
      // Chamar o método implementado no plugin
      final success = await _cameraAccess.setWhiteBalance(_whiteBalance.value);
      if (!success) {
        AppToast.warning(
          'Aviso',
          description: 'Falha ao alterar balanço de branco',
        );
      }
    } catch (e) {
      // Verificar se é o erro específico de funcionalidade não implementada
      if (e.toString().contains('MissingPluginException')) {
        // Implementação não está disponível no plugin nativo ainda

        AppToast.warning(
          'Aviso',
          description:
              'Balanço de branco "${_whiteBalance.value}" selecionado, mas a implementação nativa ainda não está disponível',
        );
      } else {
        // Outro tipo de erro
        AppToast.error(
          'Erro',
          description: 'Erro ao alterar balanço de branco: $e',
        );
      }
    }
  }

  /// Aplica os ajustes à imagem em tempo real
  Future<void> _applyImageAdjustments() async {
    await _cameraAccess.setImageAdjustments(
      CameraImageAdjustments(
        brightness: _brightness.value,
        contrast: _contrast.value,
        saturation: _saturation.value,
        sharpness: _sharpness.value,
        filter:
            _selectedFilter.value != 'normal' ? _selectedFilter.value : null,
      ),
    );
  }

  /// Para a câmera de forma limpa
  Future<void> _stopCamera() async {
    if (!_isInitialized.value) {
      return;
    }

    // 1. Cancelar a inscrição no frameStream
    _cancelFrameStreamSubscription();

    // 2. Parar a sessão da câmera
    try {
      await _cameraAccess.stopCameraSession();
    } catch (e) {
      LoggerUtil.error(e.toString());
    }

    // 3. Limpar o frame atual
    _capturedFrame.value = null;

    // 4. Atualizar estado
    _isInitialized.value = false;
    _updateCameraStatus('Câmera desconectada', isLoading: false);
  }

  /// Callback quando um dataset é selecionado no painel de configurações
  void handleDatasetSelected(Dataset? dataset) {

    _selectedDatasetId.value = dataset?.id;

    if (dataset == null) {
      AppToast.info(
        'Dataset',
        description:
        'Nenhum dataset selecionado. As imagens capturadas não serão associadas a nenhum dataset.',
      );
    } else {
      AppToast.info(
        'Dataset',
        description:
        'Dataset selecionado: ${dataset.name}. As imagens capturadas serão associadas a ele.',
      );
    }
    // Mostrar mensagem de confirmação


    // Carregar imagens do dataset
    loadSavedImages();
  }

  /// Aplica o brilho à imagem
  Future<void> applyBrightness(double value) async {
    _brightness.value = value;
    await _applyImageAdjustments();
  }

  /// Aplica o contraste à imagem
  Future<void> applyContrast(double value) async {
    _contrast.value = value;
    await _applyImageAdjustments();
  }

  /// Aplica a saturação à imagem
  Future<void> applySaturation(double value) async {
    _saturation.value = value;
    await _applyImageAdjustments();
  }

  /// Aplica a nitidez à imagem
  Future<void> applySharpness(double value) async {
    _sharpness.value = value;
    await _applyImageAdjustments();
  }

  /// Alterna o conteúdo da barra lateral
  void setActiveSidebarContent(SidebarContent content) {
    _activeSidebarContent.value = content;
  }

  CameraImage createCameraImageFromCapturedFrame() {
    if (_capturedFrame.value == null) {
      throw Exception('Nenhuma imagem capturada disponível');
    }

    return CameraImage(
      bytes: _capturedFrame.value,
      isProcessed: true,
      timestamp: DateTime.now(),
      adjustments: _getImageAdjustments(),
      cameraSettings: _getCameraSettings(),
    );
  }

  /// Reinicia completamente a câmera
  Future<void> restartCamera() async {
    _updateCameraStatus('Reiniciando câmera...', isLoading: true);

    // 1. Parar a câmera completamente
    try {
      _capturedFrame.value = null;
      _frameTimer?.cancel();
      _frameTimer = null;

      await _cameraAccess
          .stopCameraSession()
          .timeout(
            const Duration(seconds: 2),
            onTimeout: () => false,
          )
          .catchError((_) => false);
    } catch (e) {
      LoggerUtil.error('Erro ao parar sessão de câmera: $e', e);
    }

    // 2. Resetar estados
    _isInitialized.value = false;
    _isInitializing = false;

    // 3. Pequena pausa para garantir liberação de recursos
    await Future.delayed(const Duration(milliseconds: 300));

    // 4. Inicializar novamente
    await _initializeCamera();
  }

  /// Cancela a inscrição no frameStream
  void _cancelFrameStreamSubscription() {
    if (_frameStreamSubscription != null) {
      _frameStreamSubscription!.cancel();
      _frameStreamSubscription = null;
    }
  }

  /// Começa a escutar o frameStream nativo do plugin
  void _listenToFrameStream() {
    // Cancelar inscrição existente
    _cancelFrameStreamSubscription();

    // Inscrever-se no frameStream nativo do plugin
    _frameStreamSubscription = _cameraAccess.frameStream.listen(
      (frame) {
        if (!_isImageCaptured.value) {
          _capturedFrame.value = frame;
        }
      },
    );
  }

  @override
  void onClose() {
    WidgetsBinding.instance.removeObserver(this);
    _stopCamera();
    _frameTimer?.cancel();
    _frameStreamSubscription?.cancel();
    super.onClose();
  }
}
