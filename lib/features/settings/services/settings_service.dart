import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/utils/logger_util.dart';
import '../../../config/app_directories.dart';
import '../models/settings_model.dart';

/// Serviço para gerenciar as configurações da aplicação
class SettingsService extends GetxService {
  // Chave para armazenar as configurações no SharedPreferences
  static const String _settingsKey = 'app_settings';
  
  // SharedPreferences
  late final SharedPreferences _prefs;
  
  // Configurações atuais observáveis
  final Rx<SettingsModel> _settings = SettingsModel().obs;
  
  // Getter para acessar as configurações
  SettingsModel get settings => _settings.value;
  
  // Observável para o tema
  final Rx<ThemeMode> _themeMode = ThemeMode.system.obs;
  
  // Getter para o tema
  ThemeMode get themeMode => _themeMode.value;
  
  // Flag para indicar se o serviço está inicializado
  bool _initialized = false;
  
  /// Inicializar o serviço
  @override
  void onInit() {
    super.onInit();
    _initializeService();
  }
  
  // Inicializar o serviço
  Future<void> _initializeService() async {
    try {
      // Inicializar o SharedPreferences
      _prefs = await SharedPreferences.getInstance();
      
      // Carregar as configurações
      await _loadSettings();
      
      // Atualizar o modo do tema
      _updateThemeMode();
      
      _initialized = true;
      LoggerUtil.debug('Serviço de configurações inicializado com sucesso');
    } catch (e) {
      LoggerUtil.error('Erro ao inicializar serviço de configurações', e);
    }
  }
  
  /// Garantir que o serviço esteja inicializado
  Future<void> ensureInitialized() async {
    if (!_initialized) {
      await _initializeService();
    }
  }
  
  /// Carregar as configurações do SharedPreferences
  Future<void> _loadSettings() async {
    try {
      // Verificar se há configurações salvas
      final String? jsonString = _prefs.getString(_settingsKey);
      
      if (jsonString != null) {
        // Decodificar o JSON
        final Map<String, dynamic> json = jsonDecode(jsonString);
        
        // Atualizar as configurações
        _settings.value = SettingsModel.fromJson(json);
      } else {
        // Salvar configurações padrão
        await _saveSettings();
      }
    } catch (e) {
      LoggerUtil.error('Erro ao carregar configurações', e);
      // Manter as configurações padrão em caso de erro
    }
  }
  
  /// Salvar as configurações no SharedPreferences
  Future<void> _saveSettings() async {
    try {
      // Codificar para JSON
      final String jsonString = _settings.value.toJsonString();
      
      // Salvar no SharedPreferences
      await _prefs.setString(_settingsKey, jsonString);
      
      LoggerUtil.debug('Configurações salvas com sucesso');
    } catch (e) {
      LoggerUtil.error('Erro ao salvar configurações', e);
    }
  }
  
  /// Atualizar o modo do tema
  void _updateThemeMode() {
    switch (_settings.value.themeMode) {
      case 'light':
        _themeMode.value = ThemeMode.light;
        break;
      case 'dark':
        _themeMode.value = ThemeMode.dark;
        break;
      default:
        _themeMode.value = ThemeMode.system;
    }
    
    Get.changeThemeMode(_themeMode.value);
  }
  
  /// Atualizar as configurações e salvar
  Future<void> updateSettings(SettingsModel newSettings) async {
    await ensureInitialized();
    
    // Atualizar o valor observável
    _settings.value = newSettings;
    
    // Atualizar o tema se necessário
    if (_settings.value.themeMode != newSettings.themeMode) {
      _updateThemeMode();
    }
    
    // Salvar as configurações
    await _saveSettings();
  }
  
  /// Atualizar parcialmente as configurações
  Future<void> updatePartialSettings({
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
    await ensureInitialized();
    
    // Criar uma nova configuração com as alterações
    final updatedSettings = _settings.value.copyWith(
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
    
    // Atualizar as configurações
    await updateSettings(updatedSettings);
  }
  
  /// Define o tema da aplicação
  Future<void> setThemeMode(ThemeMode mode) async {
    final modeString = mode == ThemeMode.light 
        ? 'light' 
        : mode == ThemeMode.dark ? 'dark' : 'system';
    
    await updatePartialSettings(themeMode: modeString);
  }
  
  /// Adiciona um projeto à lista de projetos recentes
  Future<void> addRecentProject(String projectId) async {
    await ensureInitialized();
    
    // Obter a lista atual
    List<String> updatedList = List.from(_settings.value.recentProjects);
    
    // Remover se já existir
    updatedList.remove(projectId);
    
    // Adicionar no início
    updatedList.insert(0, projectId);
    
    // Limitar a 10 projetos
    if (updatedList.length > 10) {
      updatedList = updatedList.sublist(0, 10);
    }
    
    // Atualizar a configuração
    await updatePartialSettings(recentProjects: updatedList);
  }
  
  /// Limpa a lista de projetos recentes
  Future<void> clearRecentProjects() async {
    await updatePartialSettings(recentProjects: []);
  }
  
  /// Reseta as configurações para os valores padrão
  Future<void> resetToDefaults() async {
    await ensureInitialized();
    
    // Criar nova instância com valores padrão
    final defaultSettings = SettingsModel();
    
    // Manter alguns valores específicos
    final updatedSettings = defaultSettings.copyWith(
      lastCameraId: _settings.value.lastCameraId,
      lastDatasetId: _settings.value.lastDatasetId,
      pythonPath: _settings.value.pythonPath,
      dataDirectory: _settings.value.dataDirectory,
    );
    
    // Atualizar as configurações
    await updateSettings(updatedSettings);
  }
  
  /// Exporta as configurações para um arquivo
  Future<String> exportSettings(String? customPath) async {
    await ensureInitialized();
    
    try {
      // Converter para JSON com informações extras
      final Map<String, dynamic> exportData = {
        ..._settings.value.toJson(),
        'exportDate': DateTime.now().toIso8601String(),
        'appVersion': '1.0.0', // TODO: obter da configuração do app
      };
      
      final jsonString = jsonEncode(exportData);
      
      // Determinar o caminho de saída
      final String outputPath;
      if (customPath != null && customPath.isNotEmpty) {
        outputPath = customPath;
      } else {
        // Usar o diretório padrão da aplicação
        final homeDir = AppDirectories.instance.baseDir.path;
        outputPath = '$homeDir/settings_export_${DateTime.now().millisecondsSinceEpoch}.json';
      }
      
      // Criar o arquivo e salvar
      final file = File(outputPath);
      await file.writeAsString(jsonString, flush: true);
      
      return outputPath;
    } catch (e) {
      LoggerUtil.error('Erro ao exportar configurações', e);
      rethrow;
    }
  }
  
  /// Importa configurações de um arquivo
  Future<void> importSettings(String filePath) async {
    await ensureInitialized();
    
    try {
      final file = File(filePath);
      if (!await file.exists()) {
        throw FileSystemException('Arquivo não encontrado', filePath);
      }
      
      final jsonString = await file.readAsString();
      final Map<String, dynamic> data = jsonDecode(jsonString);
      
      // Remover campos extras
      data.remove('exportDate');
      data.remove('appVersion');
      
      // Criar novo modelo a partir dos dados do arquivo
      final importedSettings = SettingsModel.fromJson(data);
      
      // Atualizar as configurações
      await updateSettings(importedSettings);
      
      LoggerUtil.info('Configurações importadas com sucesso');
    } catch (e) {
      LoggerUtil.error('Erro ao importar configurações', e);
      rethrow;
    }
  }
} 