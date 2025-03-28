import 'package:get/get.dart';
import 'package:flutter/material.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/features/settings/services/settings_service.dart';

/// Serviço para inicializar as configurações do sistema no início do aplicativo
class SettingsInitializer {
  /// Inicializa o serviço de configurações e aplicar configurações globais
  static Future<void> initialize() async {
    // Verificar se o serviço já está registrado
    if (!Get.isRegistered<SettingsService>()) {
      // Registrar o serviço
      final settingsService = SettingsService();
      Get.put<SettingsService>(settingsService, permanent: true);
      
      // Inicializar o serviço
      await settingsService.ensureInitialized();
    } else {
      // Se já estiver registrado, garantir que está inicializado
      await Get.find<SettingsService>().ensureInitialized();
    }
    
    // Obter o serviço de configurações
    final settingsService = Get.find<SettingsService>();
    final settings = settingsService.settings;
    
    // Configurar sistema de logs
    LoggerUtil.setLogLevels(
      debug: settings.enableLogging,
      info: settings.enableLogging,
      warning: settings.enableLogging,
      error: settings.enableLogging,
    );
    
    // Configurar persistência de logs
    if (settings.enableLogPersistence) {
      await LoggerUtil.setEnabled(true);
    }
    
    // Aplicar o tema global
    switch (settings.themeMode) {
      case 'light':
        Get.changeThemeMode(ThemeMode.light);
        break;
      case 'dark':
        Get.changeThemeMode(ThemeMode.dark);
        break;
      case 'system':
      default:
        Get.changeThemeMode(ThemeMode.system);
        break;
    }
    
    LoggerUtil.info('Serviço de configurações inicializado com sucesso');
  }
  
  /// Sincroniza as configurações com o sistema de logs
  static Future<void> syncLoggerSettings() async {
    final settingsService = Get.find<SettingsService>();
    final settings = settingsService.settings;
    
    LoggerUtil.setLogLevels(
      debug: settings.enableLogging,
      info: settings.enableLogging,
      warning: settings.enableLogging,
      error: settings.enableLogging,
    );
    
    await LoggerUtil.setEnabled(settings.enableLogPersistence);
  }
} 