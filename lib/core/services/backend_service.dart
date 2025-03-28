// lib/core/services/backend_service.dart
import 'dart:async';
import 'dart:io';
import 'dart:convert';
import 'dart:math' as Math;
import 'package:get/get.dart';
import 'package:microdetect/config/app_directories.dart';
import 'package:microdetect/core/services/health_service.dart';
import 'package:microdetect/core/services/port_checker_service.dart';
import 'package:path/path.dart' as path;
import '../enums/backend_status_enum.dart';
import 'python_service.dart';
import 'backend_installer_service.dart';
import 'backend_fix_service.dart';
import '../utils/logger_util.dart';

class BackendService extends GetxService {
  // Services with Get injection
  final PythonService _pythonService = Get.find<PythonService>();
  final BackendInstallerService _installerService = Get.find<BackendInstallerService>();
  final BackendFixService _fixService = Get.find<BackendFixService>();
  final PortCheckerService _portCheckerService = Get.find<PortCheckerService>();

  // Observable state
  final status = BackendStatus.stopped.obs;
  final statusMessage = ''.obs;
  final isInitializing = false.obs;
  final logs = <String>[].obs;
  final lastLogTime = DateTime.now().obs;
  final initStartTime = DateTime.now().obs;
  final currentInitStep = Rx<BackendInitStep>(BackendInitStep.systemInitialization);
  final lastError = Rxn<String>();
  final progressValue = 0.0.obs;
  final serverPort = 8000.obs;

  // Computed observables
  final isRunning = false.obs;
  final initializationTime = Duration.zero.obs;

  // Singleton accessor
  static BackendService get to => Get.find<BackendService>();

  // Health check timer
  Timer? _healthCheckTimer;
  Timer? _initTimeTimer;

  @override
  void onInit() {
    super.onInit();

    // Configurar workers para estado computado
    ever(status, (value) {
      isRunning.value = (value == BackendStatus.running);
    });

    // Atualizar tempo de inicialização periodicamente
    _startInitTimeWorker();

    // Monitorar mudanças no passo de inicialização
    ever(_installerService.installState, _onInstallerStateChanged);
  }

  // Reagir às mudanças no estado do instalador
  void _onInstallerStateChanged(BackendInitStep step) {
    if (isInitializing.value) {
      currentInitStep.value = step;

      // Atualizar mensagem de status baseado no passo atual
      switch (step) {
        case BackendInitStep.systemInitialization:
          _setStatus(BackendStatus.initializing, 'Inicializando sistema...');
          break;
        case BackendInitStep.directorySetup:
          _setStatus(BackendStatus.initializing, 'Configurando diretórios da aplicação...');
          break;
        case BackendInitStep.installationCheck:
          _setStatus(BackendStatus.initializing, 'Verificando instalação do backend...');
          break;
        case BackendInitStep.updateCheck:
          _setStatus(BackendStatus.initializing, 'Verificando atualizações disponíveis...');
          break;
        case BackendInitStep.backendInstallation:
          _setStatus(BackendStatus.initializing, 'Instalando/atualizando backend...');
          break;
        case BackendInitStep.dataDirectorySetup:
          _setStatus(BackendStatus.initializing, 'Configurando diretórios de dados...');
          break;
        case BackendInitStep.pythonEnvironmentCheck:
          _setStatus(BackendStatus.initializing, 'Verificando ambiente Python...');
          break;
        case BackendInitStep.dependenciesInstallation:
          _setStatus(BackendStatus.initializing, 'Instalando dependências...');
          break;
        case BackendInitStep.serverStartup:
          _setStatus(BackendStatus.initializing, 'Iniciando servidor...');
          break;
        case BackendInitStep.healthCheck:
          _setStatus(BackendStatus.initializing, 'Verificando saúde do servidor...');
          break;
        case BackendInitStep.completed:
          if (!isRunning.value) {
            _setStatus(BackendStatus.running, 'Backend em execução');
          }
          break;
        case BackendInitStep.failed:
          _setStatus(BackendStatus.error, 'Falha na inicialização do backend');
          break;
      }
    }
  }

  // Iniciar worker para atualizar tempo de inicialização quando relevante
  void _startInitTimeWorker() {
    _initTimeTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (isInitializing.value) {
        initializationTime.value = DateTime.now().difference(initStartTime.value);
      }
    });
  }

  @override
  void onClose() {
    _healthCheckTimer?.cancel();
    _initTimeTimer?.cancel();
    super.onClose();
  }

  Future<String> getBackendVersion() async {
    return await _installerService.getCurrentVersion();
  }

  // Inicializar com todos os pré-requisitos
  Future<bool> initializeWithPrerequisites() async {
    if (isInitializing.value) return false;

    isInitializing.value = true;
    initStartTime.value = DateTime.now();
    currentInitStep.value = BackendInitStep.systemInitialization;
    progressValue.value = 0.0;

    try {
      _setStatus(BackendStatus.initializing, 'Inicializando sistema...');
      _addLog('Iniciando processo de inicialização do backend');

      // Primeiro verificar se há algum processo na porta
      _addLog('Verificando se a porta ${serverPort.value} já está em uso...');
      final portCleared = await _clearPortIfNeeded(serverPort.value);
      if (!portCleared) {
        _addLog('Não foi possível liberar a porta ${serverPort.value}. Tentando continuar mesmo assim...');
      } else {
        _addLog('Porta ${serverPort.value} está disponível para uso.');
      }

      // Inicializar diretórios da aplicação
      currentInitStep.value = BackendInitStep.directorySetup;
      progressValue.value = 0.1;

      try {
        await AppDirectories.instance.initialize();
        _addLog('Diretórios da aplicação configurados com sucesso');
      } catch (dirError) {
        _addLog('ERRO ao configurar diretórios da aplicação: $dirError');
        throw dirError; // Propagar o erro
      }

      // Verificar instalação do backend
      _addLog('Avançando para verificação de instalação...');
      currentInitStep.value = BackendInitStep.installationCheck;
      progressValue.value = 0.2;

      final installer = BackendInstallerService.to;
      bool backendInstalled = false;

      try {
        backendInstalled = await installer.isInstalled();
        _addLog('Verificação de instalação concluída: ${backendInstalled ? 'Backend instalado' : 'Backend não instalado'}');
      } catch (installCheckError) {
        _addLog('ERRO ao verificar instalação do backend: $installCheckError');
        throw installCheckError;
      }

      if (!backendInstalled) {
        _addLog('Backend não está instalado. Iniciando instalação...');
        try {
          currentInitStep.value = BackendInitStep.backendInstallation;
          progressValue.value = 0.3;

          final installSuccess = await installer.install();
          if (!installSuccess) {
            _setStatus(BackendStatus.error, 'Falha ao instalar backend');
            lastError.value = 'Falha na instalação do backend';
            _addLog('Falha na instalação do backend - saindo do processo de inicialização');
            isInitializing.value = false;
            return false;
          }

          _addLog('Backend instalado com sucesso');
        } catch (installError) {
          _addLog('ERRO durante instalação do backend: $installError');
          throw installError;
        }
      } else {
        _addLog('Backend está instalado. Verificando atualizações...');

        // Verificar atualizações
        try {
          currentInitStep.value = BackendInitStep.updateCheck;
          progressValue.value = 0.3;
          final updateAvailable = await installer.isUpdateAvailable();

          if (updateAvailable) {
            _addLog('Atualização disponível. Atualizando backend...');
            currentInitStep.value = BackendInitStep.backendInstallation;
            progressValue.value = 0.4;

            await installer.update();
            _addLog('Backend atualizado para versão ${installer.assetVersion.value}');
          } else {
            _addLog('Backend está na versão mais recente (${installer.currentVersion.value})');
          }
        } catch (updateError) {
          _addLog('ERRO ao verificar/instalar atualizações: $updateError');
          // Não propagar esse erro, apenas registrar - podemos continuar mesmo sem atualizar
        }
      }

      // Configurar diretórios de dados
      _addLog('Avançando para configuração de diretórios de dados...');
      currentInitStep.value = BackendInitStep.dataDirectorySetup;
      progressValue.value = 0.5;

      try {
        final dirSetup = await installer.setupDataDirectories();

        if (!dirSetup) {
          _setStatus(BackendStatus.error, 'Falha ao configurar diretórios de dados');
          lastError.value = 'Falha na configuração de diretórios de dados';
          _addLog('Falha na configuração de diretórios de dados - saindo do processo de inicialização');
          isInitializing.value = false;
          return false;
        }

        _addLog('Diretórios de dados configurados com sucesso');
      } catch (dataSetupError) {
        _addLog('ERRO ao configurar diretórios de dados: $dataSetupError');
        throw dataSetupError;
      }

      // IMPORTANTE: Log adicional para debugging - esse é o ponto onde parece travar
      _addLog('Verificando estrutura de diretórios antes de continuar...');

      try {
        // Verificar se a estrutura parece correta
        final backendPath = await installer.backendPath;
        final backendDir = Directory(backendPath);
        if (await backendDir.exists()) {
          _addLog('Backend dir existe em: $backendPath');

          // Listar arquivos para verificar
          final files = await backendDir.list().toList();
          _addLog('Conteúdo do diretório backend (${files.length} itens):');
          for (var i = 0; i < Math.min(10, files.length); i++) {
            _addLog('- ${path.basename(files[i].path)}');
          }

          // Verificar script principal
          final startScript = path.join(backendPath, 'start_backend.py');
          final scriptExists = await File(startScript).exists();
          _addLog('Script principal exists: $scriptExists');

          // Verificar diretório de dados
          final dataPath = await installer.dataPath;
          final dataDir = Directory(dataPath);
          if (await dataDir.exists()) {
            _addLog('Data dir existe em: $dataPath');

            // Listar conteúdo
            final dataFiles = await dataDir.list().toList();
            _addLog('Conteúdo do diretório data (${dataFiles.length} itens):');
            for (var i = 0; i < Math.min(5, dataFiles.length); i++) {
              _addLog('- ${path.basename(dataFiles[i].path)}');
            }
          } else {
            _addLog('ALERTA: Diretório de dados não existe!');
          }

          // Verificar ambiente virtual
          final venvPath = path.join(backendPath, 'venv');
          final venvExists = await Directory(venvPath).exists();
          _addLog('Virtual env exists: $venvExists');
        } else {
          _addLog('ERRO: Diretório backend não encontrado!');
        }
      } catch (inspectError) {
        _addLog('Erro ao inspecionar diretórios: $inspectError');
        // Apenas log, não interromper o fluxo
      }

      _addLog('Avançando para o restante do processo de inicialização...');
      // Continuar com o resto da inicialização
      try {
        return await initialize(isRetry: false, isChainedCall: true);
      } catch (initError) {
        _addLog('ERRO durante a inicialização principal: $initError');
        rethrow;
      }
    } catch (e) {
      _setStatus(BackendStatus.error, 'Erro na inicialização: $e');
      lastError.value = 'Erro: $e';
      _addLog('Erro geral na inicialização: $e');
      isInitializing.value = false;
      return false;
    }
  }

  // Verificar e limpar a porta se necessário
  Future<bool> _clearPortIfNeeded(int port) async {
    try {
      // Primeiro verificar se a porta está disponível usando Socket
      final isAvailable = await _portCheckerService.isPortAvailable(port);

      if (isAvailable) {
        return true; // Porta já está disponível
      }

      _addLog('Porta $port está em uso. Tentando liberar...');

      // Usar o serviço para verificar e matar processos na porta
      final portsCleared = await _portCheckerService.checkAndKillProcessOnPort(port);

      // Verificar novamente se a porta está disponível
      final isAvailableNow = await _portCheckerService.isPortAvailable(port);

      if (isAvailableNow) {
        _addLog('Porta $port liberada com sucesso');
        return true;
      } else if (portsCleared) {
        _addLog('Processos encerrados, mas a porta $port ainda parece estar em uso. Aguardando liberação...');

        // Esperar um pouco para o sistema liberar a porta
        await Future.delayed(const Duration(seconds: 2));

        // Verificar uma última vez
        final isAvailableAfterWait = await _portCheckerService.isPortAvailable(port);
        if (isAvailableAfterWait) {
          _addLog('Porta $port liberada após espera');
          return true;
        } else {
          _addLog('Não foi possível liberar a porta $port mesmo após espera');
          return false;
        }
      }

      _addLog('Não foi possível liberar a porta $port');
      return false;
    } catch (e) {
      _addLog('Erro ao verificar disponibilidade da porta $port: $e');
      return false;
    }
  }

  // Initialize the backend
  Future<bool> initialize({bool isRetry = false, bool isChainedCall = false}) async {
    // Modificamos a condição para permitir chamadas em cadeia a partir de initializeWithPrerequisites
    if (isInitializing.value && !isRetry && !isChainedCall) {
      LoggerUtil.debug('Tentativa de inicializar quando já está inicializando. Ignorando chamada duplicada.');
      return false;
    }

    if (!isRetry && !isChainedCall) {
      isInitializing.value = true;
      initStartTime.value = DateTime.now();
      currentInitStep.value = BackendInitStep.systemInitialization;
      progressValue.value = 0.0;
    } else {
      LoggerUtil.debug('Continuando inicialização em cadeia ou retry');
    }
    try {
      // Fix nested directory structure if needed
      final backendPath = await _installerService.backendPath;
      final needsFix = await _fixService.needsStructureFix(backendPath);

      if (needsFix) {
        _addLog('Detectada estrutura de diretórios aninhados. Corrigindo...');
        final fixSuccess = await _fixService.fixNestedDirectoryStructure(backendPath);

        if (!fixSuccess) {
          _setStatus(BackendStatus.error, 'Falha ao corrigir estrutura de diretórios');
          lastError.value = 'Falha na correção da estrutura de diretórios';
          isInitializing.value = false;
          return false;
        }

        _addLog('Estrutura de diretórios corrigida com sucesso');
      }

      // Verificar ambiente Python
      currentInitStep.value = BackendInitStep.pythonEnvironmentCheck;
      progressValue.value = 0.6;
      final pythonAvailable = await _pythonService.checkPythonAvailability();

      if (!pythonAvailable) {
        _setStatus(BackendStatus.error, 'Python não está disponível no sistema');
        lastError.value = 'Python não encontrado no sistema';
        isInitializing.value = false;
        return false;
      }

      _addLog('Ambiente Python verificado com sucesso');

      // Iniciar servidor Python
      currentInitStep.value = BackendInitStep.serverStartup;
      progressValue.value = 0.7;

      // Verificar porta novamente antes de iniciar o servidor
      await _clearPortIfNeeded(serverPort.value);

      final startSuccess = await _pythonService.startServer(port: serverPort.value);

      if (!startSuccess) {
        _setStatus(BackendStatus.error, 'Falha ao iniciar servidor Python');
        lastError.value = 'Falha ao iniciar servidor Python';
        isInitializing.value = false;
        return false;
      }

      _addLog('Servidor Python iniciado com sucesso');

      // Verificar saúde do servidor
      currentInitStep.value = BackendInitStep.healthCheck;
      progressValue.value = 0.9;

      // Iniciar timer para verificar saúde periodicamente
      if (_healthCheckTimer != null) {
        _healthCheckTimer!.cancel();
      }
      _healthCheckTimer = Timer.periodic(const Duration(seconds: 10), (_) => checkStatus());

      // Retry health check a few times
      bool isHealthy = false;
      for (int i = 0; i < 5; i++) {
        await Future.delayed(const Duration(seconds: 2));
        isHealthy = await _pythonService.checkServerHealth(port: serverPort.value);
        if (isHealthy) break;
        _addLog('Tentativa ${i+1} de verificação de saúde falhou, tentando novamente...');
      }

      if (!isHealthy) {
        _setStatus(BackendStatus.error, 'Servidor Python não está respondendo');
        lastError.value = 'Servidor Python não está respondendo após múltiplas tentativas';
        isInitializing.value = false;
        return false;
      }

      // Inicialização concluída com sucesso
      currentInitStep.value = BackendInitStep.completed;
      progressValue.value = 1.0;
      _setStatus(BackendStatus.running, 'Backend em execução');
      isInitializing.value = false;
      return true;
    } catch (e) {
      _setStatus(BackendStatus.error, 'Erro ao inicializar backend: $e');
      lastError.value = 'Erro: $e';
      isInitializing.value = false;
      return false;
    }
  }

  // Parar o backend
  Future<bool> stop() async {
    if (status.value == BackendStatus.stopped) {
      return true;
    }

    _setStatus(BackendStatus.stopping, 'Parando backend...');

    try {
      final success = await _pythonService.stopServer();

      if (success) {
        _setStatus(BackendStatus.stopped, 'Backend parado');
        return true;
      } else {
        _setStatus(BackendStatus.error, 'Falha ao parar o backend');
        return false;
      }
    } catch (e) {
      _setStatus(BackendStatus.error, 'Erro ao parar: $e');
      return false;
    }
  }

  // Reiniciar o backend
  Future<bool> restart() async {
    if (isInitializing.value) return false;

    _addLog('Reiniciando backend...');

    if (status.value == BackendStatus.error || status.value == BackendStatus.stopped) {
      await forceStop();
      return await initialize();
    }

    await stop();
    return await initialize();
  }

  // Forçar parada do backend
  Future<void> forceStop() async {
    _setStatus(BackendStatus.stopping, 'Forçando parada do backend...');

    try {
      // Primeiro tentar parar o servidor pelo método normal
      await _pythonService.stopServer(force: true);

      // Verificar se ainda existem processos Python relacionados ao backend
      await _ensureAllProcessesKilled();

      // Verificar e matar qualquer processo que esteja usando a porta
      await _clearPortIfNeeded(serverPort.value);

      _setStatus(BackendStatus.stopped, 'Backend forçadamente parado');
    } catch (e) {
      LoggerUtil.error('Erro ao forçar parada', e);
      _setStatus(BackendStatus.stopped, 'Backend considerado como parado após erro');

      // Ainda assim tentar matar qualquer processo persistente
      _ensureAllProcessesKilled();
      await _clearPortIfNeeded(serverPort.value);
    }
  }

  // Método para verificar e encerrar todos os processos Python relacionados
  Future<void> _ensureAllProcessesKilled() async {
    try {
      if (Platform.isWindows) {
        // No Windows, tentar encontrar e matar processos Python via taskkill
        final result = await Process.run(
            'tasklist',
            ['/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
            stdoutEncoding: utf8
        );

        if (result.exitCode == 0 && (result.stdout as String).contains('python.exe')) {
          await Process.run('taskkill', ['/F', '/IM', 'python.exe']);
          _addLog('Processos Python encerrados via taskkill');
        }
      } else if (Platform.isMacOS || Platform.isLinux) {
        // No macOS/Linux, buscar processos Python usando ps e filtrar pelo nome do backend
        final result = await Process.run(
            'ps',
            ['-ef'],
            stdoutEncoding: utf8
        );

        if (result.exitCode == 0) {
          final output = result.stdout as String;
          final lines = output.split('\n');
          int killedProcesses = 0;

          for (final line in lines) {
            // Verificar se a linha contém processos Python relacionados ao nosso backend
            if (line.contains('python') &&
                (line.contains('start_backend') || line.contains('microdetect'))) {
              // Extrair o PID (segunda coluna após separar os espaços)
              final parts = line.trim().split(RegExp(r'\s+'));
              if (parts.length > 1) {
                final pid = parts[1];
                // Tentar matar o processo com SIGKILL (-9)
                await Process.run('kill', ['-9', pid]);
                killedProcesses++;
              }
            }
          }

          if (killedProcesses > 0) {
            _addLog('Encerrados $killedProcesses processos Python relacionados ao backend');
          }
        }
      }
    } catch (e) {
      LoggerUtil.error('Erro ao garantir encerramento de processos', e);
    }
  }

  // Verificar o status atual do backend
  Future<bool> checkStatus() async {
    try {
      // Se o processo Python não está sendo executado, o backend não está funcionando
      if (!_pythonService.isRunning) {
        if (status.value == BackendStatus.running) {
          _setStatus(BackendStatus.stopped, 'Servidor Python não está em execução');
        }
        return false;
      }

      // Tentar se conectar ao backend via API
      final HealthService healthService = Get.find<HealthService>();
      final bool isReachable = await healthService.checkHealth();

      if (isReachable) {
        // Se o backend estava inicializando, atualizar o status para rodando
        if (status.value != BackendStatus.running) {
          if (isInitializing.value) {
            isInitializing.value = false;
          }
          _setStatus(BackendStatus.running, 'Servidor está rodando');
        }
        return true;
      } else {
        if (status.value == BackendStatus.running) {
          _setStatus(BackendStatus.error, 'Backend não responde');
        }
        LoggerUtil.warning('Backend health check falhou: não foi possível conectar');
        return false;
      }
    } catch (e) {
      if (status.value == BackendStatus.running) {
        _setStatus(BackendStatus.error, 'Erro ao verificar status: $e');
      }
      LoggerUtil.error('Erro ao verificar status do backend: $e');
      return false;
    }
  }

  // Update backend from source
  Future<bool> updateBackendFromSource(String sourceDirPath) async {
    _setStatus(BackendStatus.initializing, 'Atualizando backend Python...');

    try {
      if (status.value == BackendStatus.running) {
        await stop();
      }

      final updated = await _installerService.updateFromSource(sourceDirPath);

      if (!updated) {
        _setStatus(BackendStatus.error, 'Falha ao atualizar backend');
        return false;
      }

      _setStatus(BackendStatus.initializing, 'Backend atualizado. Inicializando...');
      return await initialize();
    } catch (e) {
      _setStatus(BackendStatus.error, 'Erro ao atualizar backend: $e');
      return false;
    }
  }

  // Adiciona uma mensagem aos logs
  void _addLog(String message) {
    logs.add(message);
    lastLogTime.value = DateTime.now();

    // Limitar o tamanho dos logs para evitar problemas de memória
    if (logs.length > 100) {
      logs.removeRange(0, logs.length - 100);
    }

    LoggerUtil.debug('[BackendService] $message');
  }

  // Set status
  void _setStatus(BackendStatus newStatus, String message) {
    status.value = newStatus;
    statusMessage.value = message;
    _addLog(message);
  }

  // Run diagnostics
  Future<Map<String, dynamic>> runDiagnostics() async {
    try {
      final installStatus = await _installerService.checkInstallationStatus();

      final pythonAvailable = await _pythonService.checkPythonAvailability();
      final pythonPath = await _pythonService.findPythonPath();
      final portAvailable = await _portCheckerService.isPortAvailable(serverPort.value);

      final result = {
        ...installStatus,
        'pythonAvailable': pythonAvailable,
        'pythonPath': pythonPath,
        'portAvailable': portAvailable,
        'port': serverPort.value,
        'currentStatus': {
          'status': status.value.toString().split('.').last,
          'message': statusMessage.value,
          'isRunning': _pythonService.isRunning,
          'currentStep': currentInitStep.value.toString().split('.').last,
        },
      };

      return result;
    } catch (e) {
      LoggerUtil.error('Erro ao executar diagnóstico', e);
      return {
        'error': e.toString(),
        'currentStatus': {
          'status': status.value.toString().split('.').last,
          'message': statusMessage.value,
        },
      };
    }
  }

  // Clean and reinitialize
  Future<bool> cleanAndReinitialize() async {
    try {
      _setStatus(BackendStatus.initializing, 'Limpando o ambiente do backend...');

      await stop();

      // Limpar porta
      await _clearPortIfNeeded(serverPort.value);

      final status = await _installerService.checkInstallationStatus();

      if (!status['isInstalled']) {
        _setStatus(BackendStatus.initializing, 'Tentando encontrar backend Python válido...');

        final detectedPath = await _detectBackendPath();

        if (detectedPath != null) {
          _setStatus(BackendStatus.initializing, 'Backend Python detectado. Atualizando instalação...');

          final updateSuccess = await updateBackendFromSource(detectedPath);

          if (updateSuccess) {
            return true;
          }
        }
      }

      _setStatus(BackendStatus.error, 'Não foi possível inicializar o backend automaticamente');
      return false;
    } catch (e) {
      _setStatus(BackendStatus.error, 'Erro ao limpar ambiente: $e');
      return false;
    }
  }

  // Detect backend path
  Future<String?> _detectBackendPath() async {
    try {
      final projectDirs = [
        // Projeto atual (provável localização em desenvolvimento)
        '${Directory.current.path}/python_backend',

        // Pasta anexada explicitamente (enviada pelo usuário)
        '/Users/rodolfodebonis/Documents/projects/microdetect/python_backend',

        // Pasta do usuário/Documents/projects/microdetect/python_backend
        if (Platform.environment['HOME'] != null)
          '${Platform.environment['HOME']}/Documents/projects/microdetect/python_backend',

        // Pasta do aplicativo (se estiver em execução como aplicativo)
        '${path.dirname(Platform.resolvedExecutable)}/python_backend',
        '${path.dirname(path.dirname(Platform.resolvedExecutable))}/python_backend',

        // Recursos do macOS
        if (Platform.isMacOS)
          '${path.dirname(path.dirname(Platform.resolvedExecutable))}/Resources/python_backend',

        // Pasta do usuário
        if (Platform.environment['HOME'] != null)
          '${Platform.environment['HOME']}/microdetect/python_backend',
      ];

      for (final dir in projectDirs) {
        final directory = Directory(dir);
        if (await directory.exists()) {
          final script = File('$dir/start_backend.py');
          if (await script.exists()) {
            return dir;
          }
        }
      }

      return null;
    } catch (e) {
      LoggerUtil.error('Erro ao detectar backend', e);
      return null;
    }
  }
}