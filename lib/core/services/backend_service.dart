// Modificações no BackendService para usar o novo PythonService

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:get/get.dart';
import '../utils/logger_util.dart';
import '../enums/backend_status_enum.dart';
import 'python_service.dart';
import 'port_checker_service.dart';

class BackendService extends GetxService {
  // Services with Get injection
  final PythonService _pythonService = Get.find<PythonService>();
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
  }

  @override
  void onClose() {
    _healthCheckTimer?.cancel();
    _initTimeTimer?.cancel();
    super.onClose();
  }

  // Verifica se há atualizações disponíveis
  Future<bool> checkForUpdates() async {
    try {
      _setStatus(BackendStatus.checking, 'Verificando atualizações...');
      final hasUpdate = await _pythonService.checkForUpdates();

      if (hasUpdate) {
        _setStatus(BackendStatus.checking, 'Atualização disponível!');
      } else {
        _setStatus(isRunning.value ? BackendStatus.running : BackendStatus.stopped,
            isRunning.value ? 'Backend em execução' : 'Backend parado');
      }

      return hasUpdate;
    } catch (e) {
      LoggerUtil.error('Erro ao verificar atualizações', e);
      return false;
    }
  }

  // Retorna a versão atual do backend
  Future<String> getBackendVersion() async {
    return _pythonService.currentVersion.value;
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

      // Verificar se há algum processo na porta
      _addLog('Verificando se a porta ${serverPort.value} já está em uso...');
      final portCleared = await _clearPortIfNeeded(serverPort.value);
      if (!portCleared) {
        _addLog('Não foi possível liberar a porta ${serverPort.value}. Tentando continuar mesmo assim...');
      } else {
        _addLog('Porta ${serverPort.value} está disponível para uso.');
      }

      // Verificar se o pacote está instalado e atualizado
      currentInitStep.value = BackendInitStep.checkingEnvironment;
      progressValue.value = 0.2;

      // Verificar versão atual
      if (_pythonService.currentVersion.value.isEmpty) {
        _addLog('Pacote microdetect não encontrado. Instalando...');
      } else {
        _addLog('Pacote microdetect encontrado: ${_pythonService.currentVersion.value}. Reinstalando para garantir versão correta...');
      }

      // Instalar ou reinstalar o pacote
      currentInitStep.value = BackendInitStep.installation;
      progressValue.value = 0.4;

      final installSuccess = await _pythonService.installOrUpdate(force: true);
      if (!installSuccess) {
        _setStatus(BackendStatus.error, 'Falha ao instalar o pacote microdetect');
        lastError.value = 'Falha na instalação do pacote';
        isInitializing.value = false;
        return false;
      }

      _addLog('Pacote microdetect instalado com sucesso: ${_pythonService.currentVersion.value}');

      // Verificar saúde do Python
      currentInitStep.value = BackendInitStep.checkingEnvironment;
      progressValue.value = 0.6;

      // Iniciar o servidor
      currentInitStep.value = BackendInitStep.serverStartup;
      progressValue.value = 0.8;

      final serverStarted = await _pythonService.startServer(port: serverPort.value);
      if (!serverStarted) {
        _setStatus(BackendStatus.error, 'Falha ao iniciar o servidor');
        lastError.value = 'Falha ao iniciar o servidor';
        isInitializing.value = false;
        return false;
      }

      _addLog('Servidor iniciado com sucesso');

      // Verificar saúde do servidor
      currentInitStep.value = BackendInitStep.serverStartup;
      progressValue.value = 0.9;

      // Iniciar timer para verificar saúde periodicamente
      if (_healthCheckTimer != null) {
        _healthCheckTimer!.cancel();
      }
      _healthCheckTimer = Timer.periodic(const Duration(seconds: 10), (_) => checkStatus());

      // Inicialização concluída com sucesso
      currentInitStep.value = BackendInitStep.completed;
      progressValue.value = 1.0;
      _setStatus(BackendStatus.running, 'Backend em execução');
      isInitializing.value = false;
      return true;
    } catch (e) {
      _setStatus(BackendStatus.error, 'Erro na inicialização: $e');
      lastError.value = 'Erro: $e';
      isInitializing.value = false;
      return false;
    }
  }

  // Método simplificado equivalente ao initialize original
  Future<bool> initialize({bool isRetry = false}) async {
    return initializeWithPrerequisites();
  }

  // Verificar se a porta está disponível
  Future<bool> _clearPortIfNeeded(int port) async {
    return await _portCheckerService.checkAndKillProcessOnPort(port);
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
      await _pythonService.stopServer(force: true);
      _setStatus(BackendStatus.stopped, 'Backend forçadamente parado');
    } catch (e) {
      LoggerUtil.error('Erro ao forçar parada', e);
      _setStatus(BackendStatus.stopped, 'Backend considerado como parado após erro');
    }
  }

  // Verificar o status atual do backend
  Future<bool> checkStatus() async {
    try {
      final isHealthy = await _pythonService.checkServerHealth();

      if (isHealthy) {
        if (status.value != BackendStatus.running) {
          _setStatus(BackendStatus.running, 'Servidor está rodando');
        }
        return true;
      } else {
        if (status.value == BackendStatus.running) {
          _setStatus(BackendStatus.error, 'Backend não responde');
        }
        return false;
      }
    } catch (e) {
      if (status.value == BackendStatus.running) {
        _setStatus(BackendStatus.error, 'Erro ao verificar status: $e');
      }
      return false;
    }
  }

  // Atualizar o backend
  Future<bool> update() async {
    if (isInitializing.value) return false;

    _setStatus(BackendStatus.initializing, 'Atualizando backend...');

    try {
      // Parar o servidor se estiver rodando
      if (isRunning.value) {
        await stop();
      }

      // Instalar a versão mais recente
      final updateSuccess = await _pythonService.installOrUpdate(force: true);
      if (!updateSuccess) {
        _setStatus(BackendStatus.error, 'Falha ao atualizar o backend');
        lastError.value = 'Falha na atualização do backend';
        return false;
      }

      _setStatus(BackendStatus.initializing, 'Backend atualizado. Iniciando...');

      // Reiniciar o servidor
      return await initialize();
    } catch (e) {
      _setStatus(BackendStatus.error, 'Erro ao atualizar backend: $e');
      lastError.value = 'Erro: $e';
      return false;
    }
  }

  // Adicionar ao lib/core/services/backend_service.dart

  /// Tenta uma instalação personalizada do microdetect com opções específicas
  Future<bool> retryInstallationWithCustomOptions({
    required List<String> pipArgs,
    required Map<String, String> environment,
    required bool useSystemPython,
  }) async {
    try {
      _setStatus(BackendStatus.initializing, 'Tentando instalação personalizada...');
      _addLog('Tentando instalação personalizada com argumentos: ${pipArgs.join(' ')}');

      // Se estamos usando o Python do sistema, precisamos encontrá-lo primeiro
      String? pythonPath;
      if (useSystemPython) {
        _addLog('Procurando por instalação de Python no sistema...');
        pythonPath = await _findSystemPython();

        if (pythonPath == null) {
          _addLog('Python não encontrado no sistema');
          _setStatus(BackendStatus.error, 'Python não encontrado no sistema');
          return false;
        }

        _addLog('Python encontrado: $pythonPath');
      }

      // Executar comando pip personalizado
      final result = await _runCustomPipCommand(
        pipArgs: pipArgs,
        environment: environment,
        pythonPath: pythonPath,
      );

      if (result.exitCode == 0) {
        _addLog('Instalação personalizada concluída com sucesso');
        _setStatus(BackendStatus.initializing, 'Pacote instalado. Verificando...');

        // Verificar se o pacote foi instalado corretamente
        final version = _pythonService.currentVersion();
        if (version.isNotEmpty) {
          _addLog('Microdetect instalado com sucesso: $version');
          return true;
        } else {
          _addLog('Erro: Pacote instalado, mas não foi possível verificar a versão');
          return false;
        }
      } else {
        _addLog('Erro na instalação personalizada: ${result.stderr}');
        _setStatus(BackendStatus.error, 'Falha na instalação personalizada');
        return false;
      }
    } catch (e) {
      _addLog('Erro ao tentar instalação personalizada: $e');
      _setStatus(BackendStatus.error, 'Erro na instalação personalizada: $e');
      return false;
    }
  }

  /// Encontra uma instalação do Python no sistema
  Future<String?> _findSystemPython() async {
    try {
      List<String> possibleCommands = [];

      if (Platform.isWindows) {
        possibleCommands = [
          'python',
          'python3',
          r'C:\Python39\python.exe',
          r'C:\Python310\python.exe',
          r'C:\Python311\python.exe',
          r'C:\Program Files\Python39\python.exe',
          r'C:\Program Files\Python310\python.exe',
          r'C:\Program Files\Python311\python.exe',
        ];
      } else {
        // macOS e Linux
        possibleCommands = [
          '/usr/bin/python3',
          '/usr/local/bin/python3',
          '/opt/homebrew/bin/python3',
          '/usr/bin/python',
          'python3',
          'python',
        ];
      }

      // Tentar comandos diretos
      for (final command in possibleCommands) {
        try {
          final result = await Process.run(
            command,
            ['--version'],
            stdoutEncoding: utf8,
          );

          if (result.exitCode == 0) {
            _addLog('Encontrado Python: $command');
            return command;
          }
        } catch (_) {
          // Continuar para o próximo comando
        }
      }

      // Tentar usando where/which
      final whereCommand = Platform.isWindows ? 'where' : 'which';
      try {
        final result = await Process.run(
          whereCommand,
          ['python3'],
          stdoutEncoding: utf8,
        );

        if (result.exitCode == 0) {
          final path = result.stdout.toString().trim().split('\n').first;
          _addLog('Encontrado Python via $whereCommand: $path');
          return path;
        }
      } catch (_) {
        // Tentar 'python' se 'python3' falhar
        try {
          final result = await Process.run(
            whereCommand,
            ['python'],
            stdoutEncoding: utf8,
          );

          if (result.exitCode == 0) {
            final path = result.stdout.toString().trim().split('\n').first;
            _addLog('Encontrado Python via $whereCommand: $path');
            return path;
          }
        } catch (_) {
          // Ignorar e retornar null
        }
      }

      return null;
    } catch (e) {
      _addLog('Erro ao procurar Python no sistema: $e');
      return null;
    }
  }

  /// Executa um comando pip personalizado
  Future<ProcessResult> _runCustomPipCommand({
    required List<String> pipArgs,
    required Map<String, String> environment,
    String? pythonPath,
  }) async {
    try {
      // Se temos um caminho Python específico, usá-lo
      if (pythonPath != null) {
        return await Process.run(
          pythonPath,
          ['-m', 'pip', ...pipArgs],
          stdoutEncoding: utf8,
          stderrEncoding: utf8,
          environment: environment,
          runInShell: true,
        );
      } else {
        // Caso contrário, delegar para o serviço Python
        return await _pythonService.runPipCommandDirectly(pipArgs, environment);
      }
    } catch (e) {
      _addLog('Erro ao executar comando pip personalizado: $e');
      throw e;
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

  // Iniciar worker para atualizar tempo de inicialização
  void _startInitTimeWorker() {
    _initTimeTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (isInitializing.value) {
        initializationTime.value = DateTime.now().difference(initStartTime.value);
      }
    });
  }
}