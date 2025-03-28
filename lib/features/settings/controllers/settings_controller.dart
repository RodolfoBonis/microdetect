import 'dart:async';
import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/services/python_service.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_toast.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/shared/events/screen_events.dart';
import 'package:microdetect/features/shared/events/event_manager.dart';
import '../../../core/services/backend_service.dart';
import '../../../core/utils/logger_util.dart';
import '../../../features/backend_monitor/controllers/backend_monitor_controller.dart';
import '../models/settings_model.dart';
import '../services/settings_service.dart';

/// Controller para a tela de configurações
class SettingsController extends GetxController {
  // Referências aos serviços
  final SettingsService settingsService;
  final BackendService backendService;
  final PythonService pythonService;

  // Estados observáveis derivados do modelo
  final Rx<SettingsModel> settings = SettingsModel().obs;
  
  // Estados adicionais da UI
  final RxInt currentTabIndex = 0.obs;
  final RxBool isExportingSettings = false.obs;
  final RxBool isImportingSettings = false.obs;
  final RxBool isLoading = false.obs;
  final RxBool isRestartingBackend = false.obs;
  final RxBool isCheckingUpdate = false.obs;
  final RxBool updateAvailable = false.obs;
  final RxString backendVersion = ''.obs;
  final RxString errorMessage = ''.obs;
  
  // Lista de tipos de eventos registrados para limpeza
  final List<String> _registeredEvents = [];
  
  // Controles e dados adicionais
  DateTime? _lastRefreshTime;
  final _refreshDebounceTime = const Duration(seconds: 2);
  
  // Controller para TabView - nullable para evitar erros se não estiver inicializado
  TabController? _tabController;

  SettingsController({
    required this.settingsService,
    required this.backendService,
    required this.pythonService,
  });

  @override
  void onInit() {
    super.onInit();
    _setupEventListeners();
    _loadSettings();
    _checkBackendVersion();
  }

  @override
  void onClose() {
    _unregisterEventListeners();
    if (_serverMonitorTimer != null) {
      _serverMonitorTimer?.cancel();
    }
    super.onClose();
  }
  
  /// Configura um TabController
  void setTabController(TabController controller) {
    _tabController = controller;
    
    // Sincronizar o estado
    currentTabIndex.value = controller.index;
    
    // Ouvir mudanças
    controller.addListener(() {
      if (!controller.indexIsChanging) {
        currentTabIndex.value = controller.index;
      }
    });
  }
  
  /// Configura os event listeners
  void _setupEventListeners() {
    // Registrar handler para o evento de refresh
    _registerEventListener(ScreenEvents.refresh, _handleRefreshRequest);
  }
  
  // Registrar um listener e armazenar o tipo para limpeza futura
  void _registerEventListener(String eventType, Function(ScreenEvent) handler) {
    Get.events.addListener(eventType, handler);
    _registeredEvents.add(eventType);
  }
  
  // Cancelar todos os listeners registrados
  void _unregisterEventListeners() {
    for (final eventType in _registeredEvents) {
      Get.events.removeAllListenersForType(eventType);
    }
    _registeredEvents.clear();
  }
  
  /// Trata solicitações de atualização
  void _handleRefreshRequest(ScreenEvent event) {
    final now = DateTime.now();
    if (_lastRefreshTime == null || 
        now.difference(_lastRefreshTime!) > _refreshDebounceTime) {
      _lastRefreshTime = now;
      _loadSettings();
      _checkBackendVersion();
    }
  }

  /// Carrega as configurações atuais
  Future<void> _loadSettings() async {
    isLoading.value = true;
    errorMessage.value = '';
    
    try {
      // Garantir que o serviço esteja inicializado
      await settingsService.ensureInitialized();
      
      // Obter configurações e atualizar o estado
      settings.value = settingsService.settings;
      
      isLoading.value = false;
    } catch (e) {
      isLoading.value = false;
      errorMessage.value = 'Falha ao carregar configurações: ${e.toString()}';
      LoggerUtil.error('Erro ao carregar configurações', e);
    }
  }
  
  /// Verifica a versão atual do backend
  Future<void> _checkBackendVersion() async {
    isCheckingUpdate.value = true;
    
    try {
      final version = await backendService.getBackendVersion();
      backendVersion.value = version;
      
      // Verificar se há atualização disponível
      final hasUpdate = await pythonService.checkForUpdates();
      updateAvailable.value = hasUpdate;
      
      isCheckingUpdate.value = false;
    } catch (e) {
      isCheckingUpdate.value = false;
      LoggerUtil.error('Erro ao verificar versão do backend', e);
    }
  }
  
  /// Atualiza o backend para a versão mais recente
  Future<void> updateBackend() async {
    try {
      // Usar o método estático do BackendMonitorController para
      // navegar para a tela de monitoramento e iniciar a atualização
      BackendMonitorController.navigateToMonitorAndUpdate();
    } catch (e) {
      AppToast.error(
        'Falha ao iniciar atualização do backend',
        description: e.toString(),
      );
      LoggerUtil.error('Erro ao iniciar atualização do backend', e);
    }
  }
  
  /// Reinicia o serviço de backend
  Future<void> restartBackend() async {
    // Ativar os indicadores de carregamento
    isLoading.value = true;
    isRestartingBackend.value = true;
    
    try {
      // Notificar o usuário sobre o início do processo
      AppToast.info('Finalizando processos do backend...');
      
      // Atualizar texto de status imediatamente
      backendVersion.value = ''; // Isso vai alterar o status na UI para "Status desconhecido"
      
      // Parar o serviço atual com força para garantir que seja encerrado
      await backendService.forceStop();
      
      // Aguardar um tempo adequado para garantir que todos os processos foram encerrados
      await Future.delayed(const Duration(seconds: 5));
      
      AppToast.info('Iniciando backend novamente...');
      
      // Iniciar o serviço novamente
      final success = await backendService.initialize();
      
      if (success) {
        // Atualizar a versão do backend após reiniciar
        final version = await backendService.getBackendVersion();
        backendVersion.value = version;
        
        // Mostrar mensagem de sucesso
        AppToast.success(
          'Backend reiniciado com sucesso',
        );
        
        // Iniciar um monitoramento periódico para verificar se o servidor continua ativo
        _startServerMonitoring();
      } else {
        // Mostrar mensagem de erro
        AppToast.error(
          'Falha ao iniciar o backend após reinicialização',
        );
        
        // Tentar uma última vez usando force stop e depois initialize
        await Future.delayed(const Duration(seconds: 2));
        await backendService.forceStop();
        await Future.delayed(const Duration(seconds: 2));
        final retrySuccess = await backendService.initialize();
        
        if (retrySuccess) {
          // Atualizar a versão do backend após reiniciar
          final version = await backendService.getBackendVersion();
          backendVersion.value = version;
          
          AppToast.success('Backend reiniciado com sucesso na segunda tentativa');
          
          // Iniciar um monitoramento periódico para verificar se o servidor continua ativo
          _startServerMonitoring();
        }
      }
      
      // Desativar os indicadores de carregamento
      isLoading.value = false;
      isRestartingBackend.value = false;
    } catch (e) {
      // Desativar os indicadores de carregamento em caso de erro
      isLoading.value = false;
      isRestartingBackend.value = false;
      
      // Tentar recuperar a versão para atualizar o status na UI
      try {
        final version = await backendService.getBackendVersion();
        backendVersion.value = version;
      } catch (_) {
        // Se falhar, deixar o status como desconhecido
        backendVersion.value = '';
      }
      
      AppToast.error(
        'Falha ao reiniciar backend: ${e.toString()}',
      );
      LoggerUtil.error('Erro ao reiniciar backend', e);
    }
  }
  
  // Timer para monitorar o status do servidor após reinicialização
  Timer? _serverMonitorTimer;
  int _monitoringAttempts = 0;
  
  /// Inicia um monitoramento periódico para verificar se o servidor permanece ativo
  void _startServerMonitoring() {
    // Cancelar timer existente se houver
    _serverMonitorTimer?.cancel();
    _monitoringAttempts = 0;
    
    // Iniciar monitoramento a cada 5 segundos, por até 6 verificações (30 segundos)
    _serverMonitorTimer = Timer.periodic(const Duration(seconds: 5), (timer) async {
      _monitoringAttempts++;
      
      // Verificar status do servidor
      final isRunning = await backendService.checkStatus();
      
      if (!isRunning) {
        LoggerUtil.warning('Servidor não está respondendo durante monitoramento pós-reinicialização');
        
        // Atualizar UI para refletir status correto
        backendVersion.value = '';
        
        // Se for a segunda tentativa ou mais e o servidor não estiver respondendo, tentar reiniciar
        if (_monitoringAttempts >= 2) {
          LoggerUtil.warning('Tentando reiniciar o servidor que parou de responder');
          timer.cancel();
          
          // Reiniciar o servidor silenciosamente (sem notificações ou indicadores de UI)
          await _silentlyRestartServer();
        }
      } else {
        LoggerUtil.debug('Servidor verificado e está respondendo corretamente');
        
        // Atualizar versão se necessário
        if (backendVersion.value.isEmpty) {
          try {
            final version = await backendService.getBackendVersion();
            backendVersion.value = version;
          } catch (_) {}
        }
      }
      
      // Parar monitoramento após 6 tentativas
      if (_monitoringAttempts >= 6) {
        timer.cancel();
        LoggerUtil.debug('Monitoramento pós-reinicialização concluído');
      }
    });
  }
  
  /// Reinicia o servidor silenciosamente após detectar que parou de responder
  Future<void> _silentlyRestartServer() async {
    try {
      // Forçar parada e aguardar
      await backendService.forceStop();
      await Future.delayed(const Duration(seconds: 3));
      
      // Iniciar novamente
      final success = await backendService.initialize();
      
      if (success) {
        // Atualizar versão
        try {
          final version = await backendService.getBackendVersion();
          backendVersion.value = version;
        } catch (_) {}
        
        LoggerUtil.info('Servidor reiniciado automaticamente com sucesso');
      } else {
        LoggerUtil.error('Falha ao reiniciar servidor automaticamente');
      }
    } catch (e) {
      LoggerUtil.error('Erro ao tentar reiniciar servidor automaticamente', e);
    }
  }
  
  /// Altera o tema da aplicação
  void changeThemeMode(ThemeMode mode) async {
    try {
      // Atualizar o tema no serviço
      await settingsService.setThemeMode(mode);
      
      // Atualizar o modelo local
      settings.value = settingsService.settings;
      
      // Aplicar o tema no GetX
      Get.changeThemeMode(mode);
    } catch (e) {
      LoggerUtil.error('Erro ao alterar tema', e);
    }
  }
  
  /// Atualiza uma configuração específica
  Future<void> updateSetting({
    String? themeMode,
    String? language,
    bool? showAdvancedOptions,
    String? lastCameraId,
    String? defaultCameraDir,
    String? defaultResolution,
    String? defaultWhiteBalance,
    double? adjustBrightness,
    double? adjustContrast,
    double? adjustSaturation,
    double? adjustSharpness,
    String? filterType,
    bool? enableLogging,
    bool? enableDebugMode,
    bool? enableLogPersistence,
    bool? autoStartBackend,
    bool? backgroundProcessing,
    int? autoSaveInterval,
    bool? normalizeImages,
    bool? backupEnabled,
    String? pythonPath,
    String? dataDirectory,
    String? defaultExportDir,
    List<String>? recentProjects,
    String? lastDatasetId,
  }) async {
    try {
      // Atualizar no serviço
      await settingsService.updatePartialSettings(
        themeMode: themeMode,
        language: language,
        showAdvancedOptions: showAdvancedOptions,
        lastCameraId: lastCameraId,
        defaultCameraDir: defaultCameraDir,
        defaultResolution: defaultResolution,
        defaultWhiteBalance: defaultWhiteBalance,
        adjustBrightness: adjustBrightness,
        adjustContrast: adjustContrast,
        adjustSaturation: adjustSaturation,
        adjustSharpness: adjustSharpness,
        filterType: filterType,
        enableLogging: enableLogging,
        enableDebugMode: enableDebugMode,
        enableLogPersistence: enableLogPersistence,
        autoStartBackend: autoStartBackend,
        backgroundProcessing: backgroundProcessing,
        autoSaveInterval: autoSaveInterval,
        normalizeImages: normalizeImages,
        backupEnabled: backupEnabled,
        pythonPath: pythonPath,
        dataDirectory: dataDirectory,
        defaultExportDir: defaultExportDir,
        recentProjects: recentProjects,
        lastDatasetId: lastDatasetId,
      );
      
      // Atualizar o modelo local
      settings.value = settingsService.settings;
      
      // Aplicar configurações específicas conforme necessário
      if (enableLogging != null) {
        LoggerUtil.setLogLevels(
          debug: enableLogging,
          info: enableLogging,
          warning: enableLogging,
          error: enableLogging,
        );
      }
      
      // Ativar/desativar persistência de logs
      if (enableLogPersistence != null) {
        await LoggerUtil.setEnabled(enableLogPersistence);
      }
    } catch (e) {
      LoggerUtil.error('Erro ao atualizar configuração', e);
      AppToast.error(
        'Falha ao salvar configuração',
      );
    }
  }
  
  /// Seleciona um diretório e atualiza a configuração
  Future<void> selectDirectory(String settingName) async {
    final String? path = await FilePicker.platform.getDirectoryPath();
    
    if (path != null) {
      switch (settingName) {
        case 'defaultExportDir':
          await updateSetting(defaultExportDir: path);
          break;
        case 'dataDirectory':
          await updateSetting(dataDirectory: path);
          break;
        case 'defaultCameraDir':
          await updateSetting(defaultCameraDir: path);
          break;
      }
    }
  }
  
  /// Seleciona um arquivo Python e atualiza a configuração
  Future<void> selectPythonPath() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles();
    
    if (result != null && result.files.single.path != null) {
      final path = result.files.single.path!;
      await updateSetting(pythonPath: path);
    }
  }
  
  /// Exporta as configurações para um arquivo
  Future<void> exportSettingsToFile() async {
    isExportingSettings.value = true;
    
    try {
      // Obter o diretório padrão do aplicativo
      final homeDir = '${Platform.environment['HOME']}/.microdetect';
      final exportPath = '$homeDir/microdetect_settings_${DateTime.now().millisecondsSinceEpoch}.json';
      
      // Exportar as configurações
      final filePath = await settingsService.exportSettings(exportPath);
      
      // Mostrar mensagem de sucesso
      AppToast.success(
        'Configurações exportadas para: $filePath',
        duration: const Duration(seconds: 5),
      );
      
      isExportingSettings.value = false;
    } catch (e) {
      isExportingSettings.value = false;
      AppToast.error(
        'Falha ao exportar configurações: ${e.toString()}',
      );
      LoggerUtil.error('Erro ao exportar configurações', e);
    }
  }
  
  /// Importa as configurações de um arquivo
  Future<void> importSettingsFromFile() async {
    isImportingSettings.value = true;
    
    try {
      // Selecionar o arquivo
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['json'],
      );
      
      if (result != null && result.files.single.path != null) {
        final path = result.files.single.path!;
        
        // Importar as configurações
        await settingsService.importSettings(path);
        
        // Recarregar o modelo local
        settings.value = settingsService.settings;
        
        // Mostrar mensagem de sucesso
        AppToast.success(
          'Configurações importadas com sucesso',
        );
      }
      
      isImportingSettings.value = false;
    } catch (e) {
      isImportingSettings.value = false;
      AppToast.error(
        'Falha ao importar configurações: ${e.toString()}',
      );
      LoggerUtil.error('Erro ao importar configurações', e);
    }
  }
  
  /// Restaura as configurações para os valores padrão
  Future<void> resetToDefaults() async {
    isLoading.value = true;
    
    try {
      // Confirmar com o usuário
      final result = await Get.dialog<bool>(
        AlertDialog(
          title: Text('Restaurar configurações', 
              style: AppTypography.textTheme.titleLarge),
          content: Text(
            'Tem certeza que deseja restaurar todas as configurações para os valores padrão?',
            style: AppTypography.textTheme.bodyMedium,
          ),
          actions: [
            TextButton(
              onPressed: () => Get.back(result: false),
              child: Text('Cancelar', 
                  style: AppTypography.textTheme.labelLarge?.copyWith(
                    color: AppColors.grey,
                  )),
            ),
            TextButton(
              onPressed: () => Get.back(result: true),
              child: Text('Restaurar', 
                  style: AppTypography.textTheme.labelLarge?.copyWith(
                    color: AppColors.error,
                  )),
            ),
          ],
        ),
      );
      
      if (result == true) {
        // Restaurar configurações padrão
        await settingsService.resetToDefaults();
        
        // Recarregar o modelo local
        settings.value = settingsService.settings;
        
        // Aplicar o tema no GetX
        final themeMode = settings.value.themeMode == 'light' 
            ? ThemeMode.light 
            : settings.value.themeMode == 'dark' 
                ? ThemeMode.dark 
                : ThemeMode.system;
        Get.changeThemeMode(themeMode);
        
        // Mostrar mensagem de sucesso
        AppToast.success(
          'Configurações restauradas com sucesso',
        );
      }
      
      isLoading.value = false;
    } catch (e) {
      isLoading.value = false;
      AppToast.error(
        'Falha ao restaurar configurações: ${e.toString()}',
      );
      LoggerUtil.error('Erro ao restaurar configurações', e);
    }
  }
  
  /// Exporta os logs para um arquivo
  Future<void> exportLogFile() async {
    isLoading.value = true;
    
    try {
      // Obter diretório padrão
      final homeDir = '${Platform.environment['HOME']}/.microdetect';
      final exportPath = '$homeDir/microdetect_logs_${DateTime.now().millisecondsSinceEpoch}.txt';
      
      // Exportar logs
      final result = await LoggerUtil.exportLogs(exportPath);
      
      if (result != null) {
        AppToast.success(
          'Logs exportados para: $result',
          duration: const Duration(seconds: 5),
        );
      } else {
        AppToast.warning(
          'Nenhum log disponível para exportação',
        );
      }
      
      isLoading.value = false;
    } catch (e) {
      isLoading.value = false;
      AppToast.error(
        'Falha ao exportar logs: ${e.toString()}',
      );
      LoggerUtil.error('Erro ao exportar logs', e);
    }
  }
  
  /// Limpa todos os logs
  Future<void> clearLogFiles() async {
    isLoading.value = true;
    
    try {
      // Confirmar com o usuário
      final result = await Get.dialog<bool>(
        AlertDialog(
          title: Text('Limpar logs', 
              style: AppTypography.textTheme.titleLarge),
          content: Text(
            'Tem certeza que deseja limpar todos os logs? Esta ação não pode ser desfeita.',
            style: AppTypography.textTheme.bodyMedium,
          ),
          actions: [
            TextButton(
              onPressed: () => Get.back(result: false),
              child: Text('Cancelar', 
                  style: AppTypography.textTheme.labelLarge?.copyWith(
                    color: AppColors.grey,
                  )),
            ),
            TextButton(
              onPressed: () => Get.back(result: true),
              child: Text('Limpar', 
                  style: AppTypography.textTheme.labelLarge?.copyWith(
                    color: AppColors.error,
                  )),
            ),
          ],
        ),
      );
      
      if (result == true) {
        await LoggerUtil.clearLogs();
        AppToast.success('Logs limpos com sucesso');
      }
      
      isLoading.value = false;
    } catch (e) {
      isLoading.value = false;
      AppToast.error(
        'Falha ao limpar logs: ${e.toString()}',
      );
      LoggerUtil.error('Erro ao limpar logs', e);
    }
  }
}
