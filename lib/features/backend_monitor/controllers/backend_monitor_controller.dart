// lib/features/backend_monitor/controllers/backend_monitor_controller.dart
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/routes/app_pages.dart';
import '../../../core/enums/backend_status_enum.dart';
import '../../../core/services/backend_service.dart';
import '../../../core/services/backend_installer_service.dart';
import '../../../core/models/check_item_model.dart';
import '../../../core/utils/logger_util.dart';
import '../../../design_system/app_toast.dart';

class BackendMonitorController extends GetxController {
  // Services dependency injection
  final BackendService _backendService = Get.find<BackendService>();
  final BackendInstallerService _installerService = Get.find<BackendInstallerService>();

  // Observable state
  final lastDiagnosticResult = Rxn<Map<String, dynamic>>();
  final isUpdating = false.obs;
  final shouldNavigateAfterInit = true.obs;
  final updatePromptShown = false.obs;
  final navigationAttempts = 0.obs;
  final healthCheckStalls = 0.obs;
  final longRunningThreshold = const Duration(minutes: 2).obs;
  final inactivityThreshold = const Duration(seconds: 60).obs;

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

  // Backend version information
  RxString get currentVersion => _installerService.currentVersion;
  RxString get assetVersion => _installerService.assetVersion;
  Rx<UpdateOperation> get updateOperation => _installerService.updateOperation;

  // Computed observables
  final isLongRunning = false.obs;
  final noActivity = false.obs;

  // Timer for health checks
  Timer? _stateMonitorTimer;

  // Route to navigate after successful initialization
  String rootRoute = AppRoutes.root;

  // Steps in the initialization process
  final List<String> initSteps = [
    'Inicializando sistema',
    'Configurando diretórios',
    'Verificando instalação do backend',
    'Verificando atualizações',
    'Instalando/atualizando backend',
    'Configurando diretórios de dados',
    'Verificando ambiente Python',
    'Instalando dependências',
    'Iniciando servidor',
    'Verificando saúde do servidor',
    'Concluído'
  ];

  @override
  void onInit() {
    super.onInit();

    initialize();
  }

  void initialize() async {
    // Get versions initially
    await _loadVersionsAndCheckForUpdates();

    // Monitor time since last log for stalls
    _startStateMonitoring();

    // Monitor status for navigation and updates
    ever(status, _onStatusChanged);

    // Initialize backend if needed (with delay to let UI render first)
    await _initializeAppBackend();
  }

  void _startStateMonitoring() {
    _stateMonitorTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      _checkForStall();
      _monitorHealthCheck();
    });
  }

  // Load versions and check for updates
  Future<void> _loadVersionsAndCheckForUpdates() async {
    await _installerService.getCurrentVersion();
    await _installerService.getAssetVersion();
    await verifyIfUpdateIsAvailable();

    // If there's an update, ask if user wants to update
    if (updateAvailable && !isUpdating.value && !isInitializing.value && !updatePromptShown.value) {
      // If we're initializing when the update is detected, don't navigate automatically
      if (isInitializing.value) {
        shouldNavigateAfterInit.value = false;
      }
      _promptToUpdate();
    }
  }

  // Check if update is available
  bool get updateAvailable =>
      currentVersion.value != 'Não instalado' &&
          currentVersion.value != assetVersion.value &&
          !currentVersion.value.startsWith('Erro:') &&
          !assetVersion.value.startsWith('Erro:');

  // Ask the user if they want to update
  void _promptToUpdate() {
    if (!Get.isDialogOpen! && !updatePromptShown.value) {
      updatePromptShown.value = true;

      Get.dialog(
        AlertDialog(
          title: const Text('Atualização Disponível'),
          content: Text(
              'Uma nova versão do backend está disponível (${assetVersion.value}).\n\n'
                  'Versão atual: ${currentVersion.value}\n\n'
                  'Deseja atualizar agora?'
          ),
          actions: [
            TextButton(
              onPressed: () {
                Get.back();
              },
              child: const Text('Mais tarde'),
            ),
            ElevatedButton(
              onPressed: () {
                Get.back();
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
  }

  // Monitor health check stalls
  void _monitorHealthCheck() {
    // Check if we're stuck in health check step for too long
    if (currentInitStep.value == BackendInitStep.healthCheck && isInitializing.value) {
      healthCheckStalls.value++;

      // If we're stuck for too long (30 seconds), force progress
      if (healthCheckStalls.value >= 6) { // 6 x 5 seconds = 30 seconds
        LoggerUtil.warning('Stuck in health check. Forcing progress check.');

        // Check backend status directly
        _backendService.checkStatus().then((isRunning) {
          if (isRunning) {
            // If the backend is running but we're not progressing, force status change
            if (status.value == BackendStatus.initializing || status.value == BackendStatus.checking) {
              _backendService.status.value = BackendStatus.running;
              isInitializing.value = false;
              LoggerUtil.info('Backend detected as running. Status updated.');
            }
          }
        });

        // Reset counter after check
        healthCheckStalls.value = 0;
      }
    } else {
      // Reset counter if we're not in health check step
      healthCheckStalls.value = 0;
    }
  }

  // Monitor status changes
  void _onStatusChanged(BackendStatus newStatus) {
    LoggerUtil.debug('Backend status changed to: $newStatus');

    // If backend initialized successfully and is running, check if we should navigate
    if (newStatus == BackendStatus.running) {
      try {
        // If an update was detected during initialization, don't navigate
        if (updateAvailable && !isUpdating.value && !updatePromptShown.value) {
          // Don't navigate if we're initializing when the update is detected
          shouldNavigateAfterInit.value = false;

          // Offer update after a delay
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
          try {
            // Check again to make sure nothing changed
            if (!shouldNavigateAfterInit.value) {
              return;
            }

            // Check again if the current route is one that shouldn't navigate
            final route = Get.currentRoute;
            if (route.contains('/settings') || route.contains('/backend_monitor')) {
              LoggerUtil.info('Navigation cancelled - user is on specific screen');
              return;
            }

            // Check if still running before navigating
            if (status.value == BackendStatus.running) {
              // Avoid excessive navigation attempts
              if (navigationAttempts.value < 3) {
                LoggerUtil.info('Backend initialized successfully, navigating to home');
                navigationAttempts.value++;

                // Navigate to root route
                Get.offAllNamed(rootRoute);
              }
            }
          } catch (e) {
            LoggerUtil.error('Error during navigation after initialization: $e');
          }
        });
      } catch (e) {
        LoggerUtil.error('Error handling status change: $e');
      }
    }
  }

  // Set the root route to navigate to after successful initialization
  void setRootRoute(String route) {
    rootRoute = route;
    LoggerUtil.debug('Root route set to: $route');
  }

  // Verify if update is available
  Future<void> verifyIfUpdateIsAvailable() async {
    try {
      await _installerService.isUpdateAvailable();
    } catch (e) {
      LoggerUtil.error('Error checking for updates: $e');
    }
  }

  // Initialize with a small delay to improve UX
  Future<void> _initializeAppBackend() async {
    await Future.delayed(const Duration(milliseconds: 300));
    await _initializeBackendIfNeeded();
  }

  // Initialize backend if it's not already running
  Future<void> _initializeBackendIfNeeded() async {
    if (!isRunning.value && !isInitializing.value) {
      // Reset for new initialization
      navigationAttempts.value = 0;
      shouldNavigateAfterInit.value = true;
      await BackendService.to.initializeWithPrerequisites();
    } else if (isRunning.value) {
      // If already running, check if we should offer an update
      if (updateAvailable && !isUpdating.value && !updatePromptShown.value) {
        _promptToUpdate();
      }
    }
  }

  // Check if initialization is taking too long or if there's no activity
  void _checkForStall() {
    // Only check if initializing
    if (!isInitializing.value) {
      isLongRunning.value = false;
      noActivity.value = false;
      return;
    }

    // Calculate time since last log
    final timeSinceLastLog = DateTime.now().difference(lastLogTime.value);

    // Check if there's no activity for too long
    noActivity.value = timeSinceLastLog > inactivityThreshold.value;

    // Check if initialization is taking too long
    isLongRunning.value = initializationTime.value > longRunningThreshold.value;

    // Log for debug
    if (noActivity.value || isLongRunning.value) {
      LoggerUtil.warning(
          'Initialization issue detected: ${noActivity.value
              ? 'No activity for ${timeSinceLastLog.inSeconds}s. '
              : ''}${isLongRunning.value
              ? 'Slow initialization (${initializationTime.value.inMinutes}min). '
              : ''}'
      );
    }
  }

  @override
  void onClose() {
    // Cancel timers when closing the controller
    _stateMonitorTimer?.cancel();
    super.onClose();
  }

  // Get check items for UI based on the current initialization step
  List<CheckItem> getCheckItems() {
    // Map BackendInitStep enum to index in initSteps list
    int currentStepIndex;

    switch (currentInitStep.value) {
      case BackendInitStep.systemInitialization:
        currentStepIndex = 0;
        break;
      case BackendInitStep.directorySetup:
        currentStepIndex = 1;
        break;
      case BackendInitStep.installationCheck:
        currentStepIndex = 2;
        break;
      case BackendInitStep.updateCheck:
        currentStepIndex = 3;
        break;
      case BackendInitStep.backendInstallation:
        currentStepIndex = 4;
        break;
      case BackendInitStep.dataDirectorySetup:
        currentStepIndex = 5;
        break;
      case BackendInitStep.pythonEnvironmentCheck:
        currentStepIndex = 6;
        break;
      case BackendInitStep.dependenciesInstallation:
        currentStepIndex = 7;
        break;
      case BackendInitStep.serverStartup:
        currentStepIndex = 8;
        break;
      case BackendInitStep.healthCheck:
        currentStepIndex = 9;
        break;
      case BackendInitStep.completed:
        currentStepIndex = 10;
        break;
      case BackendInitStep.failed:
      // Keep current step but mark as error
        if (progressValue.value < 0.3) {
          currentStepIndex = 2; // Installation check
        } else if (progressValue.value < 0.6) {
          currentStepIndex = 6; // Python environment
        } else if (progressValue.value < 0.8) {
          currentStepIndex = 8; // Server startup
        } else {
          currentStepIndex = 9; // Health check
        }
        break;
    }

    return List.generate(
      initSteps.length,
          (index) => CheckItem(
        title: initSteps[index],
        status:
        index < currentStepIndex
            ? CheckStatus.completed
            : index == currentStepIndex
            ? currentInitStep.value == BackendInitStep.failed
            ? CheckStatus.error
            : CheckStatus.inProgress
            : CheckStatus.pending,
      ),
    );
  }

  // Get detailed error message from logs
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

  // Restart backend
  Future<void> restartBackend() async {
    // Visual feedback
    LoggerUtil.info('Restarting backend...');

    // Reset states
    isLongRunning.value = false;
    noActivity.value = false;

    // Tell users what's happening
    AppToast.info(
      'Reiniciando',
      description: 'Reiniciando o servidor backend...',
    );

    // Call backend service
    await _backendService.restart();
  }

  // Force stop and restart backend
  Future<void> forceRestartBackend() async {
    LoggerUtil.warning('Forcing backend restart...');

    // Reset states
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
    // Small delay to ensure controller is initialized
    Future.delayed(const Duration(milliseconds: 500), () {
      final controller = Get.find<BackendMonitorController>();
      controller.updateBackend();
    });
  }

  // Update backend from assets
  Future<void> updateBackend() async {
    LoggerUtil.info('Updating backend to new version...');

    isUpdating.value = true;

    try {
      // Stop backend before updating
      if (isRunning.value) {
        await _backendService.stop();
      }

      // Update backend
      await _installerService.update();

      // Restart backend after update
      await _backendService.initialize();

      AppToast.success(
        'Sucesso',
        description: 'Backend atualizado com sucesso para versão ${assetVersion.value}!',
      );

      // Reset update prompt flag
      updatePromptShown.value = false;
    } catch (e) {
      LoggerUtil.error('Erro ao atualizar o backend: $e');

      AppToast.error(
        'Erro',
        description: 'Falha ao atualizar o backend: $e',
      );
    } finally {
      isUpdating.value = false;
    }
  }

  // Update backend from source directory
  Future<void> updateBackendFromSource(String sourcePath) async {
    LoggerUtil.info('Updating backend from source: $sourcePath');

    isUpdating.value = true;

    try {
      // Stop backend before updating
      if (isRunning.value) {
        await _backendService.stop();
      }

      // Update backend from source directory
      await _installerService.updateFromSource(sourcePath);

      // Restart backend after update
      await _backendService.initialize();

      AppToast.success(
        'Sucesso',
        description: 'Backend atualizado com sucesso a partir do diretório fonte!',
      );
    } catch (e) {
      LoggerUtil.error('Erro ao atualizar o backend do diretório: $e');
      AppToast.error(
        'Erro',
        description: 'Falha ao atualizar o backend: $e',
      );
    } finally {
      isUpdating.value = false;
    }
  }

  // Check for available updates
  Future<void> checkForUpdates() async {
    LoggerUtil.info('Checking for backend updates...');

    AppToast.info(
      'Verificação',
      description: 'Verificando atualizações disponíveis...',
    );

    try {
      // Update versions
      await _installerService.getCurrentVersion();
      await _installerService.getAssetVersion();

      final hasUpdate = await _installerService.isUpdateAvailable();

      if (hasUpdate) {
        AppToast.info(
          'Atualização Disponível',
          description: 'Nova versão ${assetVersion.value} disponível!',
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

  // Run diagnostics
  Future<void> runDiagnostics() async {
    LoggerUtil.info('Running backend diagnostics...');

    AppToast.info(
      'Diagnóstico',
      description: 'Executando diagnóstico do backend...',
    );

    // Run diagnostics on the backend service
    final diagnosticResults = await _backendService.runDiagnostics();
    lastDiagnosticResult.value = diagnosticResults;

    // Log results
    LoggerUtil.debug(
        'Diagnostics completed with ${diagnosticResults.length} items');

    // Show toast with basic results
    final isOk = !(diagnosticResults['issues'] as List).isNotEmpty;

    if (isOk) {
      AppToast.success(
        'Diagnóstico Concluído',
        description: 'Nenhum problema encontrado no backend.',
      );
    } else {
      AppToast.warning(
        'Problemas Encontrados',
        description: 'Foram encontrados problemas no backend. Veja os detalhes.',
      );
    }
  }

  // Continue waiting (used in StalledScreenWidget)
  void continueWaiting() {
    // Reset flags to hide stalled dialog
    isLongRunning.value = false;
    noActivity.value = false;

    LoggerUtil.info('Continuing to wait for backend initialization...');

    AppToast.info(
      'Aguardando',
      description: 'Continuando a aguardar a inicialização do backend...',
    );
  }
}