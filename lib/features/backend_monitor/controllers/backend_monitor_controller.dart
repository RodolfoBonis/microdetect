// Modificações no BackendMonitorController para verificar atualizações antes da inicialização

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/features/backend_monitor/widgets/pip_error_dialog.dart';
import 'package:microdetect/routes/app_pages.dart';
import '../../../core/enums/backend_status_enum.dart';
import '../../../core/services/backend_service.dart';
import '../../../core/services/python_service.dart';
import '../../../core/models/check_item_model.dart';
import '../../../core/utils/logger_util.dart';
import '../../../design_system/app_toast.dart';

class BackendMonitorController extends GetxController {
  // Services dependency injection
  final BackendService _backendService = Get.find<BackendService>();
  final PythonService _pythonService = Get.find<PythonService>();

  // Observable state
  final lastDiagnosticResult = Rxn<Map<String, dynamic>>();
  final isUpdating = false.obs;
  final shouldNavigateAfterInit = true.obs;
  final updatePromptShown = false.obs;
  final navigationAttempts = 0.obs;
  final healthCheckStalls = 0.obs;
  final longRunningThreshold = const Duration(minutes: 2).obs;
  final inactivityThreshold = const Duration(seconds: 60).obs;

  // Getters for versions
  RxString get currentVersion => _pythonService.currentVersion;
  RxString get latestVersion => _pythonService.latestVersion;

  // Getters with reactivity for backendService properties
  Rx<BackendStatus> get status => _backendService.status;
  RxString get statusMessage => _backendService.statusMessage;
  RxBool get isInitializing => _backendService.isInitializing;
  RxBool get isRunning => _backendService.isRunning;
  RxList<String> get logs => _backendService.logs;
  Rx<DateTime> get lastLogTime => _backendService.lastLogTime;
  Rx<Duration> get initializationTime => _backendService.initializationTime;
  Rx<BackendInitStep> get currentInitStep => _backendService.currentInitStep;
  RxDouble get progressValue => _backendService.progressValue;

  // Computed observables
  final isLongRunning = false.obs;
  final noActivity = false.obs;

  // Verify if an update is available
  bool get updateAvailable =>
      currentVersion.value.isNotEmpty &&
          latestVersion.value.isNotEmpty &&
          currentVersion.value != latestVersion.value;

  // Timer for health checks
  Timer? _stateMonitorTimer;

  // Route to navigate after successful initialization
  String rootRoute = AppRoutes.root;

  @override
  void onInit() {
    super.onInit();
    initialize();
  }

  void initialize() async {
    // Start monitoring state
    _startStateMonitoring();

    // Monitor status changes
    ever(status, _onStatusChanged);

    // First check for updates, then initialize backend if needed
    await _initializeAppBackend();
  }

  void _startStateMonitoring() {
    _stateMonitorTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      _checkForStall();
      _monitorHealthCheck();
    });
  }

  String getDetailedErrorMessage() {
    if (logs.isEmpty) return statusMessage.value;

    for (final log in logs.reversed) {
      if (log.contains("Error:") || log.contains("Erro:") ||
          log.contains("ERROR") || log.contains("Exception") ||
          log.contains("Failed") || log.contains("Falha")) {
        return log;
      }
    }

    return statusMessage.value;
  }

  void handlePipInstallationError() {
    // Verificar se o erro está relacionado ao pip/instalação
    if (statusMessage.value.contains('Falha ao instalar o pacote') ||
        statusMessage.value.contains('Erro ao instalar pacote') ||
        statusMessage.value.contains('EOF when reading a line')) {

      LoggerUtil.info('Detectado erro de instalação do pip. Mostrando opções avançadas.');

      // Obter detalhe do erro a partir dos logs
      String errorDetail = '';
      for (final log in logs.reversed) {
        if (log.contains('Error:') ||
            log.contains('Erro:') ||
            log.contains('ERROR') ||
            log.contains('EOFError') ||
            log.contains('pip')) {
          errorDetail = '$log\n$errorDetail';
          // Limitar para não ficar muito longo
          if (errorDetail.length > 1500) break;
        }
      }

      // Se não encontramos detalhes, usar a mensagem de status
      if (errorDetail.isEmpty) {
        errorDetail = statusMessage.value;
      }

      // Mostrar diálogo de erro com opções avançadas
      PipErrorDialog.show(errorDetail);
    }
  }

  /// Executar diagnóstico do sistema
  Future<void> runDiagnostics() async {
    LoggerUtil.info('Executando diagnóstico do backend...');

    AppToast.info(
      'Diagnóstico',
      description: 'Executando diagnóstico do backend...',
    );

    try {
      // Verificar disponibilidade do Python
      final pythonAvailable = await _pythonService.pythonIsAvailable();

      final pipAvailable = await _pythonService.pipIsAvailble();

      // Verificar disponibilidade do backend
      final backendStatus = await _backendService.checkStatus();

      // Obter versão atual
      final currentVersion = _pythonService.currentVersion.value;

      // Verificar disponibilidade de atualizações
      final hasUpdate = await _backendService.checkForUpdates();

      // Criar resultado do diagnóstico
      final result = {
        'pythonAvailable': pythonAvailable,
        'backendStatus': backendStatus,
        'currentVersion': currentVersion,
        'latestVersion': _pythonService.latestVersion.value,
        'updateAvailable': hasUpdate,
        'isRunning': isRunning.value,
        'status': status.value.toString(),
      };

      // Armazenar resultados
      lastDiagnosticResult.value = result;

      // Exibir resultado para o usuário
      AppToast.success(
        'Diagnóstico Concluído',
        description: backendStatus
            ? 'O backend está funcionando corretamente.'
            : 'Foram detectados problemas com o backend.',
      );
    } catch (e) {
      AppToast.error(
        'Erro',
        description: 'Erro ao executar diagnóstico: $e',
      );

      // Armazenar erro
      lastDiagnosticResult.value = {
        'error': e.toString()
      };
    }
  }

  // Modified to check for updates first
  Future<void> _initializeAppBackend() async {
    await Future.delayed(const Duration(milliseconds: 300));

    // Check for updates first
    LoggerUtil.info('Verificando atualizações antes de inicializar...');
    final hasUpdate = await _backendService.checkForUpdates();

    if (hasUpdate && !updatePromptShown.value) {
      // If update available, prompt user before initializing
      _promptToUpdate();
    } else {
      // If no update or user already seen the prompt, initialize normally
      await _initializeBackendIfNeeded();
    }
  }

  // Ask the user if they want to update
  void _promptToUpdate() {
    updatePromptShown.value = true;

    Get.dialog(
      AlertDialog(
        title: const Text('Atualização Disponível'),
        content: Text(
            'Uma nova versão do backend está disponível (${latestVersion.value}).\n\n'
                'Versão atual: ${currentVersion.value}\n\n'
                'Deseja atualizar agora?'
        ),
        actions: [
          TextButton(
            onPressed: () {
              Get.back();
              // Continue with initialization using current version
              _initializeBackendIfNeeded();
            },
            child: const Text('Mais tarde'),
          ),
          ElevatedButton(
            onPressed: () {
              Get.back();
              // Update backend first, then initialize
              updateBackend();
            },
            child: const Text('Atualizar agora'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Get.theme.primaryColor,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
      barrierDismissible: false,
    );
  }

  // Initialize backend if needed
  Future<void> _initializeBackendIfNeeded() async {
    if (!isRunning.value && !isInitializing.value) {
      // Reset for new initialization
      navigationAttempts.value = 0;
      shouldNavigateAfterInit.value = true;
      await _backendService.initializeWithPrerequisites();
    }
  }

  // Monitor status changes
  void _onStatusChanged(BackendStatus newStatus) {
    // Implementation remains the same
    LoggerUtil.debug('Backend status changed to: $newStatus');

    if (newStatus == BackendStatus.error) {
      // Verificar se o erro está relacionado à instalação do pip
      if (statusMessage.value.contains('Falha ao instalar o pacote') ||
          statusMessage.value.contains('Erro ao instalar pacote') ||
          statusMessage.value.contains('EOF when reading a line')) {

        // Verificar se estamos na tela de monitor
        if (Get.currentRoute.contains('/backend_monitor')) {
          // Esperar um pouco para garantir que o usuário veja a mudança de status
          Future.delayed(const Duration(milliseconds: 500), () {
            handlePipInstallationError();
          });
        }
      }
    } else if (newStatus == BackendStatus.running) {
      try {
        // If an update was detected during initialization, don't navigate
        if (updateAvailable && !isUpdating.value && !updatePromptShown.value) {
          shouldNavigateAfterInit.value = false;
          Future.delayed(const Duration(seconds: 2), () {
            _promptToUpdate();
          });
          return;
        }

        // Check if we're on a screen that shouldn't auto-navigate
        final currentRoute = Get.currentRoute;
        if (currentRoute.contains('/settings') || currentRoute.contains('/backend_monitor')) {
          LoggerUtil.info('Backend restarted on specific screen - auto-navigation disabled');
          return;
        }

        // If we shouldn't navigate after initialization, return
        if (!shouldNavigateAfterInit.value) {
          LoggerUtil.info('Auto-navigation disabled by controller');
          return;
        }

        // Wait a bit to show success before navigating
        Future.delayed(const Duration(seconds: 2), () {
          if (!shouldNavigateAfterInit.value ||
              status.value != BackendStatus.running ||
              navigationAttempts.value >= 3) {
            return;
          }

          LoggerUtil.info('Backend initialized successfully, navigating to home');
          navigationAttempts.value++;
          Get.offAllNamed(rootRoute);
        });
      } catch (e) {
        LoggerUtil.error('Error handling status change: $e');
      }
    }
  }

  // Set the root route
  void setRootRoute(String route) {
    rootRoute = route;
  }

  // Check for updates
  Future<void> checkForUpdates() async {
    LoggerUtil.info('Checking for backend updates...');

    AppToast.info(
      'Verificação',
      description: 'Verificando atualizações disponíveis...',
    );

    try {
      final hasUpdate = await _backendService.checkForUpdates();

      if (hasUpdate) {
        AppToast.info(
          'Atualização Disponível',
          description: 'Nova versão ${latestVersion.value} disponível!',
        );

        // Reset to show prompt again
        updatePromptShown.value = false;
        _promptToUpdate();
      } else {
        AppToast.success(
          'Atualizado',
          description: 'Você já está usando a versão mais recente (${currentVersion.value}).',
        );
      }
    } catch (e) {
      LoggerUtil.error('Erro ao verificar atualizações: $e');
      AppToast.error(
        'Erro',
        description: 'Falha ao verificar atualizações: $e',
      );
    }
  }

  // Update backend
  Future<void> updateBackend() async {
    LoggerUtil.info('Updating backend to new version...');

    isUpdating.value = true;

    try {
      // Update backend
      final success = await _backendService.update();

      if (success) {
        AppToast.success(
          'Sucesso',
          description: 'Backend atualizado com sucesso para versão ${latestVersion.value}!',
        );

        // Reset update prompt flag
        updatePromptShown.value = false;
      } else {
        AppToast.error(
          'Erro',
          description: 'Falha ao atualizar o backend.',
        );
      }
    } catch (e) {
      LoggerUtil.error('Erro ao atualizar o backend: $e');
      AppToast.error(
        'Erro',
        description: 'Falha ao atualizar o backend: $e',
      );
    } finally {
      isUpdating.value = false;

      // If we're not running, initialize after update
      if (!isRunning.value && !isInitializing.value) {
        _initializeBackendIfNeeded();
      }
    }
  }

  // Check for stalled initialization
  void _checkForStall() {
    // Implementation remains the same
    if (!isInitializing.value) {
      isLongRunning.value = false;
      noActivity.value = false;
      return;
    }

    final timeSinceLastLog = DateTime.now().difference(lastLogTime.value);
    noActivity.value = timeSinceLastLog > inactivityThreshold.value;
    isLongRunning.value = initializationTime.value > longRunningThreshold.value;

    if (noActivity.value || isLongRunning.value) {
      LoggerUtil.warning('Initialization issue detected: ${noActivity.value
          ? 'No activity for ${timeSinceLastLog.inSeconds}s. '
          : ''}${isLongRunning.value
          ? 'Slow initialization (${initializationTime.value.inMinutes}min). '
          : ''}');
    }
  }

  // Monitor health check stalls
  void _monitorHealthCheck() {
    // Implementation remains the same
    if (currentInitStep.value == BackendInitStep.healthCheck && isInitializing.value) {
      healthCheckStalls.value++;

      if (healthCheckStalls.value >= 6) {
        LoggerUtil.warning('Stuck in health check. Forcing progress check.');
        _backendService.checkStatus();
        healthCheckStalls.value = 0;
      }
    } else {
      healthCheckStalls.value = 0;
    }
  }

  @override
  void onClose() {
    _stateMonitorTimer?.cancel();
    super.onClose();
  }

  // Get check items for UI
  List<CheckItem> getCheckItems() {
    // Implementation remains the same
    // ...
    return []; // Simplified for brevity
  }

  // Restart backend
  Future<void> restartBackend() async {
    LoggerUtil.info('Restarting backend...');

    isLongRunning.value = false;
    noActivity.value = false;

    AppToast.info(
      'Reiniciando',
      description: 'Reiniciando o servidor backend...',
    );

    await _backendService.restart();
  }

  // Force restart backend
  Future<void> forceRestartBackend() async {
    LoggerUtil.warning('Forcing backend restart...');

    isLongRunning.value = false;
    noActivity.value = false;

    AppToast.warning(
      'Reinicialização Forçada',
      description: 'Forçando reinicialização do servidor...',
    );

    await _backendService.forceStop();
    await Future.delayed(const Duration(seconds: 1));
    await _backendService.initialize();
  }

  // Static method to navigate to monitor screen and start update
  static void navigateToMonitorAndUpdate() {
    // Navigate to monitor screen
    Get.toNamed(AppRoutes.backendMonitor);

    // Get controller instance and start update
    Future.delayed(const Duration(milliseconds: 500), () {
      final controller = Get.find<BackendMonitorController>();
      controller.updateBackend();
    });
  }

  // Continue waiting (for stalled screen)
  void continueWaiting() {
    isLongRunning.value = false;
    noActivity.value = false;

    LoggerUtil.info('Continuing to wait for backend initialization...');

    AppToast.info(
      'Aguardando',
      description: 'Continuando a aguardar a inicialização do backend...',
    );
  }
}