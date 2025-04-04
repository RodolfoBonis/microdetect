import 'dart:async';

import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'dart:developer' as developer;
import 'package:microdetect/core/services/backend_service.dart';
import 'package:microdetect/features/settings/services/settings_service.dart';
import 'package:microdetect/design_system/app_toast.dart';
import 'package:microdetect/features/shared/events/app_event.dart';
import 'package:microdetect/features/shared/events/event_bus.dart';
import 'package:microdetect/routes/app_pages.dart';

class AppRootController extends GetxController {
  final BackendService backendService;
  final SettingsService settingsService = Get.find<SettingsService>();

  var title = "".obs;
  var currentPath = AppRoutes.home.obs;

  // Controle de UI
  final RxBool isDrawerOpen = false.obs;
  final RxBool isSearchOpen = false.obs;

  AppRootController({required this.backendService});

  @override
  void onInit() {
    super.onInit();
    developer.log('AppRootController - onInit()', name: 'AppRootController');
    _initBackendService();
  }

  void goToPage(String path) {
    currentPath.value = path;
    Get.rootDelegate.offAndToNamed(path);
  }

  void toggleThemeMode() {
    final theme = Get.isDarkMode ? ThemeMode.light : ThemeMode.dark;
    Get.changeThemeMode(theme);
    settingsService.setThemeMode(theme);
  }

  @override
  void onClose() {
    developer.log('AppRootController - onClose()', name: 'AppRootController');
    
    // Desligar o servidor Python antes de encerrar a aplicação
    try {
      debugPrint('Encerrando servidor Python antes de fechar a aplicação...');
      backendService.stop();
    } catch (e) {
      debugPrint('Erro ao desligar servidor: $e');
    }

    super.onClose();
  }

  /// Inicializa o serviço de backend
  Future<void> _initBackendService() async {
    try {
      // Inicializar o serviço de backend se necessário
      if (!backendService.isRunning.value) {
        await backendService.initialize();
      }
    } catch (e) {
      AppToast.error(
        'Erro',
        description: 'Falha ao inicializar o backend: $e',
      );
    }
  }

  // Métodos para controle da UI global

  /// Alterna o estado do drawer
  void toggleDrawer() {
    isDrawerOpen.value = !isDrawerOpen.value;
  }

  /// Abre ou Fecha o drawer
  void changeDrawerState(bool isOpen) {
    isDrawerOpen.value = isOpen;
  }

  /// Alterna o estado da barra de pesquisa
  void toggleSearch() {
    isSearchOpen.value = !isSearchOpen.value;
  }

  /// Atualiza a tela atual
  void refreshCurrentScreen() {
    EventBus.to.emit(AppEvent.refresh);
  }
  
  /// Mostra ajuda
  void showHelp() {
    AppToast.info('Ajuda', description: 'Esta função foi desativada');
  }
  
  /// Atualiza datasets
  void refreshDatasets() {
    AppToast.info('Refresh Datasets', description: 'Esta função foi desativada');
  }
}
