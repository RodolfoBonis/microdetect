// lib/core/services/backend_service.dart
import 'dart:async';
import 'dart:io';
import 'dart:convert';
import 'package:get/get.dart';
import 'package:microdetect/config/app_directories.dart';
import 'package:microdetect/core/services/health_service.dart';
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

  // Observable state
  final status = BackendStatus.stopped.obs;
  final statusMessage = ''.obs;
  final isInitializing = false.obs;
  final logs = <String>[].obs;
  final lastLogTime = DateTime.now().obs;
  final initStartTime = DateTime.now().obs;
  
  // Computed observables
  final isRunning = false.obs;
  final initializationTime = Duration.zero.obs;

  // Singleton acessor
  static BackendService get to => Get.find<BackendService>();
  
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

  // Iniciar worker para atualizar tempo de inicialização quando relevante
  void _startInitTimeWorker() {
    Timer.periodic(const Duration(seconds: 1), (_) {
      if (isInitializing.value) {
        initializationTime.value = DateTime.now().difference(initStartTime.value);
      }
    });
  }

  Future<String> getBackendVersion() async {
    return await _installerService.getCurrentVersion();
  }

  Future<bool> initializeWithPrerequisites() async {
    try {
      // Já começa a reportar status
      _setStatus(BackendStatus.initializing, 'Inicializando sistema...');

      // Inicializar diretórios (relatando progresso)
      _setStatus(BackendStatus.initializing, 'Configurando diretórios da aplicação...');
      await AppDirectories.instance.initialize();

      // Carregar configurações
      _setStatus(BackendStatus.initializing, 'Carregando configurações...');
      // AppSettings já deve estar inicializado no main()

      // Verificar instalação do backend
      _setStatus(BackendStatus.initializing, 'Verificando instalação do backend...');
      final installer = BackendInstallerService.to;
      if (!await installer.isInstalled()) {
        _setStatus(BackendStatus.initializing, 'Instalando backend Python...');
        final installSuccess = await installer.install();

        if (!installSuccess) {
          _setStatus(BackendStatus.failed, 'Falha ao instalar backend');
          return false;
        }

        _setStatus(BackendStatus.initializing, 'Configurando diretórios de dados...');
        await installer.setupDataDirectories();
      }

      // Continuar com o resto da inicialização
      return await initialize();
    } catch (e) {
      _setStatus(BackendStatus.failed, 'Erro na inicialização: $e');
      return false;
    }
  }

  // Initialize the backend
  Future<bool> initialize() async {
    if (isInitializing.value) return false;

    isInitializing.value = true;
    initStartTime.value = DateTime.now();

    try {
      _setStatus(BackendStatus.initializing, 'Inicializando backend...');

      // Check if backend is installed
      final isInstalled = await _installerService.isInstalled();
      if (!isInstalled) {
        _setStatus(BackendStatus.initializing, 'Backend não está instalado. Instalando...');
        final installSuccess = await _installerService.install();

        if (!installSuccess) {
          _setStatus(BackendStatus.failed, 'Falha ao instalar backend');
          isInitializing.value = false;
          return false;
        }

        _setStatus(BackendStatus.initializing, 'Backend instalado. Configurando...');
      }

      // Setup data directories
      final dirSetup = await _installerService.setupDataDirectories();
      if (!dirSetup) {
        _setStatus(BackendStatus.failed, 'Falha ao configurar diretórios');
        isInitializing.value = false;
        return false;
      }

      // Fix nested directory structure if needed
      final backendPath = await _installerService.backendPath;
      final needsFix = await _fixService.needsStructureFix(backendPath);

      if (needsFix) {
        _setStatus(BackendStatus.initializing, 'Corrigindo estrutura de diretórios...');
        final fixSuccess = await _fixService.fixNestedDirectoryStructure(backendPath);

        if (!fixSuccess) {
          _setStatus(BackendStatus.failed, 'Falha ao corrigir estrutura de diretórios');
          isInitializing.value = false;
          return false;
        }
      }

      // Initialize Python service
      _setStatus(BackendStatus.initializing, 'Inicializando serviço Python...');
      final pythonInitSuccess = await _pythonService.initialize();

      if (!pythonInitSuccess) {
        _setStatus(BackendStatus.failed, 'Falha ao inicializar serviço Python');
        isInitializing.value = false;
        return false;
      }

      // Start Python server
      _setStatus(BackendStatus.initializing, 'Iniciando servidor Python...');
      final startSuccess = await _pythonService.startServer();

      if (!startSuccess) {
        _setStatus(BackendStatus.failed, 'Falha ao iniciar servidor Python');
        isInitializing.value = false;
        return false;
      }

      // Check server health
      _setStatus(BackendStatus.initializing, 'Verificando saúde do servidor...');

      // Retry health check a few times
      bool isHealthy = false;
      for (int i = 0; i < 3; i++) {
        await Future.delayed(const Duration(seconds: 2));
        isHealthy = await _pythonService.checkServerHealth();
        if (isHealthy) break;
        _addLog('Tentativa ${i+1} de verificação de saúde falhou, tentando novamente...');
      }

      if (!isHealthy) {
        _setStatus(BackendStatus.failed, 'Servidor Python não está respondendo');
        isInitializing.value = false;
        return false;
      }

      _setStatus(BackendStatus.running, 'Backend em execução');
      _addLog('Backend em execução');
      isInitializing.value = false;
      return true;
    } catch (e) {
      _setStatus(BackendStatus.failed, 'Erro ao inicializar backend: $e');
      _addLog('Erro ao inicializar backend: $e');
      isInitializing.value = false;
      return false;
    }
  }

  // Stop the backend
  Future<bool> stop() async {
    if (status.value == BackendStatus.stopped) {
      return true;
    }

    _setStatus(BackendStatus.initializing, 'Parando backend...');

    try {
      final success = await _pythonService.stopServer();

      if (success) {
        _setStatus(BackendStatus.stopped, 'Backend parado');
        return true;
      } else {
        _setStatus(BackendStatus.failed, 'Falha ao parar o backend');
        return false;
      }
    } catch (e) {
      _setStatus(BackendStatus.failed, 'Erro ao parar: $e');
      return false;
    }
  }

  // Restart the backend
  Future<bool> restart() async {
    if (status.value == BackendStatus.failed || status.value == BackendStatus.stopped) {
      await forceStop();
      return await initialize();
    }

    await stop();
    return await initialize();
  }

  // Force stop the backend
  Future<void> forceStop() async {
    _setStatus(BackendStatus.initializing, 'Forçando parada do backend...');

    try {
      // Primeiro tentar parar o servidor pelo método normal 
      await _pythonService.stopServer(force: true);
      
      // Verificar se ainda existem processos Python relacionados ao backend
      await _ensureAllProcessesKilled();
      
      _setStatus(BackendStatus.stopped, 'Backend forçadamente parado');
    } catch (e) {
      LoggerUtil.error('Erro ao forçar parada', e);
      _setStatus(BackendStatus.stopped, 'Backend considerado como parado');
      
      // Ainda assim tentar matar qualquer processo persistente
      _ensureAllProcessesKilled();
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
                _addLog('Forçou encerramento do processo Python: $pid');
              }
            }
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
      LoggerUtil.debug('Verificando status do backend...');
      
      // Se o processo Python não está sendo executado, o backend não está funcionando
      if (!_pythonService.isRunning) {
        _setStatus(BackendStatus.stopped, 'Servidor Python não está em execução');
        return false;
      }

      // Tentar se conectar ao backend via API
      final HealthService healthService = Get.find<HealthService>();
      final bool isReachable = await healthService.checkHealth();

      if (isReachable) {
        // Se o backend estava inicializando, atualizar o status para rodando
        if (status.value == BackendStatus.initializing || 
            status.value == BackendStatus.checking || 
            status.value == BackendStatus.starting) {
          isInitializing.value = false;
          _setStatus(BackendStatus.running, 'Servidor está rodando');
        } else if (status.value != BackendStatus.running) {
          // Se estava em outro estado, também atualizar para rodando
          _setStatus(BackendStatus.running, 'Servidor está rodando');
        }
        
        // Adicionar log sobre sucesso da verificação
        _addLog('Servidor confirmado como saudável via API health check');
        return true;
      } else {
        if (status.value == BackendStatus.running) {
          _setStatus(BackendStatus.error, 'Backend não responde');
        }
        LoggerUtil.warning('Backend health check falhou: não foi possível conectar');
        return false;
      }
    } catch (e) {
      _setStatus(BackendStatus.error, 'Erro ao verificar status: $e');
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
        _setStatus(BackendStatus.failed, 'Falha ao atualizar backend');
        return false;
      }

      _setStatus(BackendStatus.initializing, 'Backend atualizado. Inicializando...');
      return await initialize();
    } catch (e) {
      _setStatus(BackendStatus.failed, 'Erro ao atualizar backend: $e');
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
    _addLog('Status: $message');
  }

  // Run diagnostics
  Future<Map<String, dynamic>> runDiagnostics() async {
    try {
      final installStatus = await _installerService.checkInstallationStatus();

      final pythonAvailable = await _pythonService.checkPythonAvailability();
      final pythonPath = await _pythonService.findPythonPath();

      final result = {
        ...installStatus,
        'pythonAvailable': pythonAvailable,
        'pythonPath': pythonPath,
        'currentStatus': {
          'status': status.value.toString().split('.').last,
          'message': statusMessage.value,
          'isRunning': _pythonService.isRunning,
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

      _setStatus(BackendStatus.failed, 'Não foi possível inicializar o backend automaticamente');
      return false;
    } catch (e) {
      _setStatus(BackendStatus.failed, 'Erro ao limpar ambiente: $e');
      return false;
    }
  }

  // Detect backend path
  Future<String?> _detectBackendPath() async {
    try {
      final projectDirs = [
        '/Users/rodolfodebonis/Documents/projects/microdetect/python_backend',

        if (Platform.environment['HOME'] != null)
          '${Platform.environment['HOME']}/Documents/projects/microdetect/python_backend',

        '${Directory.current.path}/python_backend',

        '${path.dirname(Platform.resolvedExecutable)}/python_backend',
        '${path.dirname(path.dirname(Platform.resolvedExecutable))}/python_backend',

        if (Platform.isMacOS)
          '${path.dirname(path.dirname(Platform.resolvedExecutable))}/Resources/python_backend',

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

  @override
  void onClose() {
    // Garantir que o backend seja encerrado quando o serviço for fechado
    forceStop().then((_) {
      // Aguardar um momento para garantir que processos sejam finalizados
      Future.delayed(const Duration(milliseconds: 500), () {
        // Verificar se ainda existem processos e forçar encerramento
        _ensureAllProcessesKilled();
      });
    });
    super.onClose();
  }
}