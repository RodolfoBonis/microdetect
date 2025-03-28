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
  // Injeção de dependência dos serviços
  final BackendService _backendService = Get.find<BackendService>();
  final BackendInstallerService _installerService = Get.find<
      BackendInstallerService>();

  // Observable state
  final currentStepIndex = 0.obs;
  final isLongRunning = false.obs;
  final noActivity = false.obs;
  final lastDiagnosticResult = Rxn<Map<String, dynamic>>();
  final isUpdating = false.obs;
  final _updateAvailable = false.obs;
  final shouldNavigateAfterInit = true.obs; // Novo controle para decidir se deve navegar após inicialização

  // Getters com reatividade para propriedades do backendService
  Rx<BackendStatus> get status => _backendService.status;

  RxString get statusMessage => _backendService.statusMessage;

  RxBool get isInitializing => _backendService.isInitializing;

  RxBool get isRunning => _backendService.isRunning;

  RxList<String> get logs => _backendService.logs;

  Rx<DateTime> get lastLogTime => _backendService.lastLogTime;

  Rx<Duration> get initializationTime => _backendService.initializationTime;

  // Informações sobre versão do backend
  RxString get currentVersion => _installerService.currentVersion;

  RxString get assetVersion => _installerService.assetVersion;

  bool get updateAvailable => _updateAvailable.value;

  // Timer para verificar saúde do servidor regularmente (para evitar que fique preso na etapa de verificação)
  Timer? _healthCheckTimer;
  // Contador para limitar tentativas de navegação
  int _navigationAttempts = 0;
  // Contador para verificações de saúde sem mudança de status
  int _healthCheckCounter = 0;

  // Steps in the initialization process - atualizado para incluir todos os passos
  final List<String> initSteps = [
    'Inicializando sistema',
    // Inicialização de diretórios e configurações
    'Configurando diretórios',
    // Preparação de estrutura
    'Verificando instalação do backend',
    // Verificação do backend
    'Verificando atualizações',
    // Verificação de atualizações disponíveis
    'Instalando/atualizando backend',
    // Instalação ou atualização
    'Configurando diretórios de dados',
    // Setup de diretórios para modelos/dados
    'Verificando ambiente Python',
    // Verificação do Python e venv
    'Instalando dependências',
    // Instalação de pacotes Python
    'Iniciando servidor',
    // Inicialização do servidor
    'Verificando saúde do servidor'
    // Checagem de saúde via API
  ];

  @override
  void onInit() {
    super.onInit();
    
    // Obter as versões no início
    _loadVersionsAndCheckForUpdates();
    
    // Usar workers para monitorar mudanças em objetos observáveis
    ever(logs, (_) => _updateCurrentStep());
    
    // Monitorar status para navegação e atualizações
    ever(status, _onStatusChanged);

    // Monitorar tempo de inicialização com debounce para evitar atualizações frequentes
    debounce(
        lastLogTime,
        (_) => _checkForStall(),
        time: const Duration(seconds: 10)
    );

    // Inicializar backend se necessário (com atraso para deixar a UI renderizar primeiro)
    _initializeAppBackend();
    
    // Iniciar timer para verificar saúde periodicamente (a cada 10 segundos)
    _healthCheckTimer = Timer.periodic(const Duration(seconds: 10), (_) => _checkHealthAndProgress());
  }
  
  // Carregar versões e verificar atualizações
  Future<void> _loadVersionsAndCheckForUpdates() async {
    await _installerService.getCurrentVersion();
    await _installerService.getAssetVersion();
    await verifyIfUpdateIsAvailable();
    
    // Se houver atualização, perguntar ao usuário se deseja atualizar
    if (_updateAvailable.value && !isUpdating.value && !isInitializing.value) {
      // Se houver atualização, não devemos navegar automaticamente
      if (isInitializing.value) {
        shouldNavigateAfterInit.value = false;
      }
      _promptToUpdate();
    }
  }
  
  // Perguntar ao usuário se deseja atualizar
  void _promptToUpdate() {
    if (!Get.isDialogOpen!) {
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
              onPressed: () => Get.back(),
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
  
  // Verificar saúde do servidor e progresso para evitar que fique preso
  void _checkHealthAndProgress() {
    // Verificar se estamos na etapa de verificação de saúde há muito tempo
    if (currentStepIndex.value == 9 && isInitializing.value) {
      _healthCheckCounter++;
      
      // Se estamos presos nessa etapa por muito tempo (30 segundos)
      if (_healthCheckCounter >= 3) {
        LoggerUtil.warning('Preso na verificação de saúde do servidor. Forçando progresso.');
        
        // Verificar o status atual do backend
        _backendService.checkStatus().then((isRunning) {
          if (isRunning) {
            // Se o backend está rodando, mas não progredimos, forçar mudança de status
            if (status.value == BackendStatus.initializing || status.value == BackendStatus.checking) {
              _backendService.status.value = BackendStatus.running;
              isInitializing.value = false;
              LoggerUtil.info('Backend detectado como em execução. Status atualizado.');
            }
          }
        });
        
        // Resetar contador após a verificação
        _healthCheckCounter = 0;
      }
    } else {
      // Resetar contador se estamos em outra etapa
      _healthCheckCounter = 0;
    }
  }

  // Monitorar mudanças de status para ações adicionais
  void _onStatusChanged(BackendStatus newStatus) {
    LoggerUtil.debug('Status do backend alterado para: $newStatus');
    
    // Se o backend inicializou com sucesso e está rodando, verificar se deve navegar
    if (newStatus == BackendStatus.running) {
      try {
        // Se foi detectada uma atualização durante a inicialização, não navegar
        if (_updateAvailable.value && !isUpdating.value) {
          // Se estamos inicializando quando a atualização é detectada, não navegar
          shouldNavigateAfterInit.value = false;
          
          // Após um tempo, verificar se precisamos oferecer atualização
          Future.delayed(const Duration(seconds: 2), () {
            _promptToUpdate();
          });
          return;
        }
        
        // Verificar se estamos em uma tela que não deve ser navegada automaticamente
        final currentRoute = Get.currentRoute;
        if (currentRoute.contains('/settings') || currentRoute.contains('/backend_monitor')) {
          LoggerUtil.info('Backend reiniciado em tela específica - navegação automática desativada');
          return; // Não navegar automaticamente se estiver na tela de configurações ou monitoramento
        }
        
        // Se não devemos navegar após a inicialização, retornar
        if (!shouldNavigateAfterInit.value) {
          LoggerUtil.info('Navegação automática desativada pelo controller');
          return;
        }
        
        // Aguardar um tempo para mostrar o sucesso antes de navegar
        Future.delayed(const Duration(seconds: 2), () {
          try {
            // Verificar novamente para certificar-se de que não houve mudanças
            if (!shouldNavigateAfterInit.value) {
              return;
            }
            
            // Verificar novamente se a rota atual é uma que não deve ser navegada
            final route = Get.currentRoute;
            if (route.contains('/settings') || route.contains('/backend_monitor')) {
              LoggerUtil.info('Navegação cancelada - usuário está em tela específica');
              return;
            }
            
            // Verificar se ainda está rodando antes de navegar
            if (status.value == BackendStatus.running) {
              // Evitar tentativas excessivas de navegação
              if (_navigationAttempts < 3) {
                LoggerUtil.info('Backend inicializado com sucesso, navegando para a home');
                _navigationAttempts++;
                
                // Navegar para a página root (home) - sem verificar a rota atual
                Get.offAllNamed(rootRoute);
              }
            }
          } catch (e) {
            LoggerUtil.error('Erro ao processar navegação após inicialização: $e');
          }
        });
      } catch (e) {
        LoggerUtil.error('Erro ao processar mudança de status: $e');
      }
    }
  }

  // Definir a rota raiz para onde navegar após inicialização bem-sucedida
  String rootRoute = AppRoutes.root;
  void setRootRoute(String route) {
    rootRoute = route;
    LoggerUtil.debug('Rota raiz definida para: $route');
  }

  // Verificar se há atualização disponível
  Future<void> verifyIfUpdateIsAvailable() async {
    try {
      _updateAvailable.value = await _installerService.isUpdateAvailable();
      LoggerUtil.debug('Atualização disponível: ${_updateAvailable.value}');
      
      if (_updateAvailable.value) {
        LoggerUtil.info('Nova versão disponível: ${assetVersion.value} (atual: ${currentVersion.value})');
      }
    } catch (e) {
      LoggerUtil.error('Erro ao verificar atualizações: $e');
    }
  }

  // Inicializar com pequeno atraso para melhorar UX
  Future<void> _initializeAppBackend() async {
    await Future.delayed(const Duration(milliseconds: 300));
    await _initializeBackendIfNeeded();
  }

  // Initialize backend if it's not already running
  Future<void> _initializeBackendIfNeeded() async {
    if (!isRunning.value && !isInitializing.value) {
      // Resetar o passo atual para o início do processo
      currentStepIndex.value = 0;
      _navigationAttempts = 0; // Resetar contagem de tentativas de navegação
      shouldNavigateAfterInit.value = true; // Por padrão, navegar após inicialização bem-sucedida
      await BackendService.to.initializeWithPrerequisites();
    } else if (isRunning.value) {
      // Se já está rodando, verificar se devemos oferecer uma atualização
      if (updateAvailable && !isUpdating.value) {
        _promptToUpdate();
      }
    }
  }

  // Verificar se a inicialização está demorando muito ou se está sem atividade
  void _checkForStall() {
    // Verifica se está inicializando
    if (!isInitializing.value) return;

    // Calculando tempo desde o último log
    final timeSinceLastLog = DateTime.now().difference(lastLogTime.value);

    // Verificar se não há atividade por muito tempo (60 segundos)
    noActivity.value = timeSinceLastLog.inSeconds > 60;

    // Verificar se a inicialização está demorando muito (2 minutos)
    isLongRunning.value = initializationTime.value.inMinutes >= 2;

    // Log para debug
    if (noActivity.value || isLongRunning.value) {
      LoggerUtil.warning(
          'Problema detectado na inicialização: ${noActivity.value
              ? 'Sem atividade por ${timeSinceLastLog.inSeconds}s. '
              : ''}${isLongRunning.value
              ? 'Inicialização lenta (${initializationTime.value
              .inMinutes}min). '
              : ''}'
      );
    }
  }

  @override
  void onClose() {
    // Cancelar timer ao fechar o controller
    _healthCheckTimer?.cancel();
    super.onClose();
  }

  // Update the current step based on logs
  void _updateCurrentStep() {
    if (logs.isEmpty) return;

    // Definir flags para detectar cada etapa nas mensagens de log
    bool foundInitializing = false;
    bool foundDirectoryConfig = false;
    bool foundInstallationCheck = false;
    bool foundUpdateCheck = false;
    bool foundInstallUpdate = false;
    bool foundDataDirConfig = false;
    bool foundPythonEnvCheck = false;
    bool foundDepsInstall = false;
    bool foundServerStart = false;
    bool foundHealthCheck = false;
    
    // Considerar todos os logs para garantir que não perdemos etapas anteriores
    for (var log in logs) {
      final logLower = log.toLowerCase();
      
      // Etapa 0 - Inicializando sistema
      if (logLower.contains('inicializando sistema') || 
          logLower.contains('iniciando aplicação')) {
        foundInitializing = true;
      }
      
      // Etapa 1 - Configurando diretórios
      else if (logLower.contains('configurando diretórios') || 
               logLower.contains('criando estrutura de diretórios')) {
        foundDirectoryConfig = true;
      }
      
      // Etapa 2 - Verificando instalação
      else if (logLower.contains('verificando instalação') || 
               logLower.contains('checando backend instalado')) {
        foundInstallationCheck = true;
      }
      
      // Etapa 3 - Verificando atualizações
      else if (logLower.contains('verificando atualizações') || 
               logLower.contains('comparando versões') ||
               logLower.contains('versão atual:') ||
               logLower.contains('versão disponível:')) {
        foundUpdateCheck = true;
      }
      
      // Etapa 4 - Instalando/atualizando
      else if (logLower.contains('instalando backend') || 
               logLower.contains('atualizando backend') || 
               logLower.contains('extraindo arquivos') || 
               logLower.contains('copiando arquivos')) {
        foundInstallUpdate = true;
        isUpdating.value = logLower.contains('atualiz');
      }
      
      // Etapa 5 - Configurando diretórios de dados
      else if (logLower.contains('diretórios de dados') || 
               logLower.contains('setup de diretórios para dados')) {
        foundDataDirConfig = true;
      }
      
      // Etapa 6 - Verificando ambiente Python
      else if (logLower.contains('verificando ambiente python') || 
               logLower.contains('ambiente virtual') || 
               logLower.contains('configurando python')) {
        foundPythonEnvCheck = true;
      }
      
      // Etapa 7 - Instalando dependências
      else if (logLower.contains('instalando dependências') || 
               logLower.contains('etapa 1/2') || 
               logLower.contains('dependências instaladas')) {
        foundDepsInstall = true;
      }
      
      // Etapa 8 - Iniciando servidor
      else if (logLower.contains('iniciando servidor') || 
               logLower.contains('etapa 2/2')) {
        foundServerStart = true;
      }
      
      // Etapa 9 - Verificando saúde do servidor
      else if (logLower.contains('servidor confirmado como saudável') || 
               logLower.contains('verificando saúde') ||
               logLower.contains('servidor está rodando')) {
        foundHealthCheck = true;
      }
    }
    
    // Definir o passo atual com base no progresso de inicialização
    // Usamos uma abordagem sequencial onde cada etapa só é considerada
    // se a anterior já foi concluída (exceto a primeira)
    
    if (foundHealthCheck) {
      currentStepIndex.value = 9;
    } else if (foundServerStart && (foundDepsInstall || foundPythonEnvCheck)) {
      currentStepIndex.value = 8;
    } else if (foundDepsInstall && foundPythonEnvCheck) {
      currentStepIndex.value = 7;
    } else if (foundPythonEnvCheck && (foundDataDirConfig || foundInstallUpdate)) {
      currentStepIndex.value = 6;
    } else if (foundDataDirConfig && (foundInstallUpdate || foundUpdateCheck)) {
      currentStepIndex.value = 5;
    } else if (foundInstallUpdate && foundUpdateCheck) {
      currentStepIndex.value = 4;
    } else if (foundUpdateCheck && foundInstallationCheck) {
      currentStepIndex.value = 3;
    } else if (foundInstallationCheck && foundDirectoryConfig) {
      currentStepIndex.value = 2;
    } else if (foundDirectoryConfig && foundInitializing) {
      currentStepIndex.value = 1;
    } else if (foundInitializing) {
      currentStepIndex.value = 0;
    }

    // Ensure index doesn't exceed the steps array
    if (currentStepIndex.value >= initSteps.length) {
      currentStepIndex.value = initSteps.length - 1;
    }
  }

  // Get check items for UI
  List<CheckItem> getCheckItems() {
    return List.generate(
      initSteps.length,
          (index) =>
          CheckItem(
            title: initSteps[index],
            status: index < currentStepIndex.value
                ? CheckStatus.completed
                : index == currentStepIndex.value
                ? CheckStatus.inProgress
                : CheckStatus.pending,
          ),
    );
  }

  // Get detailed error message
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
    // Mostrar feedback visual
    LoggerUtil.info('Reiniciando backend...');

    // Resetar os estados
    isLongRunning.value = false;
    noActivity.value = false;
    currentStepIndex.value = 0; // Resetar para o início do processo

    // Chamar serviço de backend
    await _backendService.restart();
  }

  // Force stop and restart backend
  Future<void> forceRestartBackend() async {
    LoggerUtil.warning('Forçando reinicialização do backend...');

    // Resetar os estados
    isLongRunning.value = false;
    noActivity.value = false;
    currentStepIndex.value = 0; // Resetar para o início do processo

    await _backendService.forceStop();
    await Future.delayed(const Duration(seconds: 1));
    await _backendService.initialize();
  }

  // Método estático para navegar para a tela de monitoramento e iniciar atualização
  static void navigateToMonitorAndUpdate() {
    // Navegar para a tela de monitoramento
    Get.toNamed(AppRoutes.backendMonitor);
    
    // Obter a instância do controller e iniciar atualização
    // Pequeno atraso para garantir que o controller já foi inicializado
    Future.delayed(const Duration(milliseconds: 500), () {
      final controller = Get.find<BackendMonitorController>();
      controller.updateBackend();
    });
  }

  // Atualizar o backend a partir dos assets
  Future<void> updateBackend() async {
    LoggerUtil.info('Atualizando backend para nova versão...');

    isUpdating.value = true;

    try {
      // Parar o backend antes de atualizar
      if (isRunning.value) {
        await _backendService.stop();
      }

      // Atualizar o backend
      await _installerService.update();

      // Reiniciar o backend após a atualização
      await _backendService.initialize();

      AppToast.success(
        'Sucesso',
        description: 'Backend atualizado com sucesso para versão ${assetVersion.value}!',
      );
    } catch (e) {
      LoggerUtil.error('Erro ao atualizar o backend: $e');
    } finally {
      isUpdating.value = false;
    }
  }

  // Atualizar o backend a partir de um diretório fonte
  Future<void> updateBackendFromSource(String sourcePath) async {
    LoggerUtil.info('Atualizando backend a partir de: $sourcePath');

    isUpdating.value = true;

    try {
      // Parar o backend antes de atualizar
      if (isRunning.value) {
        await _backendService.stop();
      }

      // Atualizar o backend a partir do diretório fonte
      await _installerService.updateFromSource(sourcePath);

      // Reiniciar o backend após a atualização
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

  // Verificar atualizações disponíveis
  Future<void> checkForUpdates() async {
    LoggerUtil.info('Verificando atualizações do backend...');

    try {
      // Atualizar versões
      await _installerService.getCurrentVersion();
      await _installerService.getAssetVersion();

      final hasUpdate = await _installerService.isUpdateAvailable();
      _updateAvailable.value = hasUpdate;

    } catch (e) {
      LoggerUtil.error('Erro ao verificar atualizações: $e');
      AppToast.error(
        'Erro',
        description: 'Falha ao verificar atualizações: $e',
      );
    }
  }

  // Run diagnostics method used in ErrorScreenWidget
  Future<void> runDiagnostics() async {
    LoggerUtil.info('Executando diagnóstico do backend...');

    // Run diagnostics on the backend service
    final diagnosticResults = await _backendService.runDiagnostics();
    lastDiagnosticResult.value = diagnosticResults;

    // Log results
    LoggerUtil.debug(
        'Diagnóstico concluído com ${diagnosticResults.length} itens');

    // Show diagnostic results
    AppToast.info(
      'Diagnóstico',
      description: 'Diagnóstico do backend concluído',
    );
  }

  // Continue waiting method used in StalledScreenWidget
  void continueWaiting() {
    // Reset the long running flag to hide the stalled dialog
    isLongRunning.value = false;
    noActivity.value = false;

    LoggerUtil.info('Continuando a aguardar a inicialização do backend...');
  }
}

