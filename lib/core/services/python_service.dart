import 'dart:async';
import 'dart:io';
import 'dart:convert';
import 'dart:math' as Math;
import 'package:flutter/foundation.dart';
import 'package:get/get.dart';
import 'package:path/path.dart' as path;
import 'package:path_provider/path_provider.dart';
import '../utils/logger_util.dart';
import '../enums/backend_status_enum.dart';
import '../../config/app_directories.dart';

class PythonService extends GetxService {
  // Observable state
  final _isRunning = false.obs;
  final _port = 8000.obs;
  final _host = '127.0.0.1'.obs;
  final _logs = <String>[].obs;
  final _status = false.obs;
  final pythonState = Rx<BackendInitStep>(BackendInitStep.systemInitialization);

  // Private variables
  Process? _pythonProcess;

  // Getters
  bool get isRunning => _isRunning.value;
  String get baseUrl => 'http://${_host.value}:${_port.value}';
  int get port => _port.value;
  List<String> get logs => _logs.toList();
  Stream<bool> get statusStream => _status.stream;

  @override
  void onInit() {
    super.onInit();
    // Configuração inicial se necessário
    LoggerUtil.debug('PythonService inicializado');
  }

  @override
  void onClose() {
    stopServer(force: true).then((_) {
      // Garantir que todos os processos Python relacionados sejam encerrados
      if (Platform.isMacOS || Platform.isLinux) {
        _killPythonProcesses();
      } else if (Platform.isWindows) {
        _killPythonProcessesWindows();
      }
    });
    super.onClose();
  }

  // Diretório do backend Python
  Future<String> get pythonBackendPath async {
    await AppDirectories.instance.ensureInitialized();
    return AppDirectories.instance.pythonBackendDir.path;
  }

  // Diretório de dados separado
  Future<String> get dataPath async {
    await AppDirectories.instance.ensureInitialized();
    return AppDirectories.instance.dataDir.path;
  }

  // Caminho para o executável Python no ambiente virtual
  Future<String> get pythonExecutable async {
    final backendPath = await pythonBackendPath;

    if (Platform.isWindows) {
      return path.join(backendPath, 'venv', 'Scripts', 'python.exe');
    } else {
      return path.join(backendPath, 'venv', 'bin', 'python');
    }
  }

  // Caminho para o script principal
  Future<String> get startScriptPath async {
    final backendPath = await pythonBackendPath;
    final scriptPath = path.join(backendPath, 'start_backend.py');

    // Verificar se o script existe
    if (await File(scriptPath).exists()) {
      return scriptPath;
    }

    // Se não existir, verificar no subdiretório python_backend (caso ainda não tenha sido corrigido)
    final nestedScriptPath = path.join(backendPath, 'python_backend', 'start_backend.py');
    if (await File(nestedScriptPath).exists()) {
      return nestedScriptPath;
    }

    // Retornar o caminho original mesmo se não existir
    return scriptPath;
  }

  Future<bool> initialize({int port = 8000}) async {
    try {
      if (_isRunning.value) {
        _addLog('Backend Python já está em execução');
        return true;
      }

      _status.value = false;
      _port.value = port;
      _addLog('Inicializando serviço Python na porta $port...');
      pythonState.value = BackendInitStep.systemInitialization;

      // DEBUGGING: Verificar diretórios antes de começar
      try {
        final backendPath = await pythonBackendPath;
        final pathData = await dataPath;

        _addLog('Checando diretórios antes da inicialização:');
        _addLog('- Backend path: $backendPath');
        _addLog('- Data path: $pathData');

        // Verificar se os diretórios existem
        final backendExists = await Directory(backendPath).exists();
        final dataExists = await Directory(pathData).exists();

        _addLog('- Backend directory exists: $backendExists');
        _addLog('- Data directory exists: $dataExists');

        // Verificar conteúdo do diretório backend
        if (backendExists) {
          final files = await Directory(backendPath).list().toList();
          _addLog('- Backend dir contém ${files.length} arquivos/diretórios');

          // Mostrar alguns arquivos para verificação
          for (var i = 0; i < Math.min(5, files.length); i++) {
            _addLog('  - ${path.basename(files[i].path)}');
          }
        }
      } catch (dirError) {
        _addLog('Erro ao verificar diretórios: $dirError');
        // Apenas log, continuar com a inicialização
      }

      // Verificar se os arquivos do backend existem
      final backendPath = await pythonBackendPath;
      if (!await Directory(backendPath).exists()) {
        _addLog('Diretório do backend não encontrado: $backendPath');
        pythonState.value = BackendInitStep.failed;
        return false;
      }

      _addLog('Diretório do backend encontrado: $backendPath');
      pythonState.value = BackendInitStep.directorySetup;

      // Verificar script principal
      final startScript = await startScriptPath;
      _addLog('Procurando script principal em: $startScript');

      if (!await File(startScript).exists()) {
        _addLog('Script principal não encontrado: $startScript');

        // Tentar procurar em outros locais possíveis
        _addLog('Tentando encontrar script em locais alternativos...');
        final possibleLocations = [
          path.join(backendPath, 'start_backend.py'),
          path.join(backendPath, 'python_backend', 'start_backend.py'),
          path.join(backendPath, 'app', 'start_backend.py'),
          path.join(path.dirname(backendPath), 'start_backend.py'),
        ];

        bool found = false;
        for (final location in possibleLocations) {
          _addLog('Verificando: $location');
          if (await File(location).exists()) {
            _addLog('Script encontrado em local alternativo: $location');
            found = true;
            break;
          }
        }

        if (!found) {
          _addLog('Script não encontrado em nenhum local alternativo');
          pythonState.value = BackendInitStep.failed;
          return false;
        }
      }

      _addLog('Script principal encontrado: $startScript');
      pythonState.value = BackendInitStep.pythonEnvironmentCheck;

      // Verificar se o Python está disponível
      _addLog('Verificando disponibilidade do Python...');
      final result = await checkPythonAvailability();
      if (!result) {
        _addLog('Python não está disponível no sistema');
        _addLog('Verifique se o Python está instalado e acessível');
        pythonState.value = BackendInitStep.failed;
        return false;
      }

      _addLog('Python encontrado e disponível!');

      // Verificar ambiente virtual e criar se necessário
      _addLog('Verificando ambiente virtual...');
      final venvResult = await createVirtualEnvIfNeeded();
      _addLog('Resultado da verificação do ambiente virtual: ${venvResult ? 'Sucesso' : 'Falha'}');

      pythonState.value = BackendInitStep.serverStartup;
      // Iniciar o servidor
      _addLog('Iniciando servidor Python...');
      return await startServer(port: port);
    } catch (e) {
      _addLog('Erro ao inicializar: $e');
      pythonState.value = BackendInitStep.failed;
      return false;
    }
  }

  Future<bool> checkPythonAvailability() async {
    try {
      // Primeiro, tentar usar o Python do ambiente virtual embutido
      final pyExec = await pythonExecutable;
      final pyExecFile = File(pyExec);

      if (await pyExecFile.exists()) {
        _addLog('Python encontrado em: $pyExec');
        return true;
      }

      // Se estamos no macOS, verificar caminhos conhecidos
      if (Platform.isMacOS) {
        final commonPaths = [
          '/usr/bin/python3',
          '/usr/local/bin/python3',
          '/opt/homebrew/bin/python3',
          '/usr/bin/python',
        ];

        for (final pythonPath in commonPaths) {
          final file = File(pythonPath);
          if (await file.exists()) {
            _addLog('Python encontrado em: $pythonPath');
            return true;
          }
        }
      }

      // Em último caso, tente usar o Python do sistema
      try {
        final result = await Process.run('python', ['--version']);
        if (result.exitCode == 0) {
          _addLog('Python do sistema encontrado via comando');
          return true;
        }
      } catch (e) {
        _addLog('Erro ao verificar Python via comando: $e');
      }

      try {
        final result = await Process.run('python3', ['--version']);
        if (result.exitCode == 0) {
          _addLog('Python3 do sistema encontrado via comando');
          return true;
        }
      } catch (e) {
        _addLog('Erro ao verificar Python3 via comando: $e');
      }

      _addLog('Python não encontrado no sistema');
      return false;
    } catch (e) {
      _addLog('Erro ao verificar Python: $e');
      return false;
    }
  }

  Future<bool> startServer({int port = 8000}) async {
    if (_isRunning.value) {
      LoggerUtil.debug('O servidor Python já está em execução');
      return true;
    }

    try {
      _port.value = port;
      pythonState.value = BackendInitStep.serverStartup;

      // Obter caminho para o executável Python
      final pythonPath = await findPythonPath();
      if (pythonPath == null) {
        _addLog('Erro: Python não encontrado no sistema');
        pythonState.value = BackendInitStep.failed;
        return false;
      }

      // Obter caminho para o script do backend
      final backendPath = await pythonBackendPath;
      final pathStartScript = await startScriptPath;
      final dataDir = await dataPath;

      // Verificar se o script existe
      if (!await File(pathStartScript).exists()) {
        _addLog('Erro: Script start_backend.py não encontrado em $backendPath');
        pythonState.value = BackendInitStep.failed;
        return false;
      }

      // ETAPA 1: Primeiro instalar apenas as dependências
      _addLog('Etapa 1/2: Instalando dependências Python...');
      pythonState.value = BackendInitStep.dependenciesInstallation;

      // Preparar os argumentos para instalação de dependências
      List<String> installArgs = [
        pathStartScript,
        '--install-only',  // Apenas instalar, não iniciar o servidor
      ];

      // Definir ambiente para o processo de instalação
      Map<String, String> installEnv = {
        ...Platform.environment,
        'PYTHONUNBUFFERED': '1',      // Desativar buffer para output em tempo real
        'PYTHONIOENCODING': 'utf-8',  // Garantir codificação correta
        'DATA_DIR': dataDir,          // Informar o diretório de dados separado
      };

      // Adicionar o caminho do backend ao PYTHONPATH
      if (Platform.isWindows || Platform.isLinux || Platform.isMacOS) {
        installEnv['PYTHONPATH'] = backendPath;
      }

      // Iniciar o processo Python para instalação
      final installProcess = await Process.start(
        pythonPath,
        installArgs,
        workingDirectory: backendPath,
        environment: installEnv,
      );

      // Escutar a saída do processo de instalação
      StringBuffer installOutput = StringBuffer();

      // Capturar e processar stdout
      installProcess.stdout.transform(utf8.decoder).listen((data) {
        _addLog(data);
        installOutput.write(data);
      });

      // Capturar e processar stderr
      installProcess.stderr.transform(utf8.decoder).listen((data) {
        _addLog('ERR: $data');
        installOutput.write('ERR: $data');
      });

      // Aguardar até que o processo de instalação termine
      final installExitCode = await installProcess.exitCode;
      _addLog('Instalação concluída com código: $installExitCode');

      // Verificar se a instalação foi bem-sucedida
      if (installExitCode != 0) {
        _addLog('Erro na instalação de dependências (código $installExitCode)');
        pythonState.value = BackendInitStep.failed;
        return false;
      }

      // Verificar se houve erros na saída
      if (installOutput.toString().contains("falha ao instalar") ||
          installOutput.toString().contains("failed to install") ||
          installOutput.toString().toLowerCase().contains("error:")) {
        _addLog('Erros detectados durante instalação de dependências');
        _addLog('Tentando iniciar o servidor mesmo assim...');
      } else {
        _addLog('Dependências instaladas com sucesso');
      }

      // Aguardar um momento antes de iniciar o servidor
      await Future.delayed(const Duration(seconds: 2));

      // ETAPA 2: Agora iniciar o servidor sem reinstalar dependências
      _addLog('Etapa 2/2: Iniciando servidor Python na porta $port...');
      pythonState.value = BackendInitStep.serverStartup;

      // Preparar os argumentos para o servidor
      List<String> serverArgs = [
        pathStartScript,
        '--port', port.toString(), // Especificar o diretório de dados
      ];

      // Definir ambiente para o processo do servidor
      Map<String, String> serverEnv = {
        ...Platform.environment,
        'INSTALL_DEPS_FIRST': 'false', // Não reinstalar dependências
        'PYTHONUNBUFFERED': '1',       // Desativar buffer para output em tempo real
        'PORT': port.toString(),
        'PYTHONIOENCODING': 'utf-8',   // Garantir codificação correta
        'DATA_DIR': dataDir,           // Informar o diretório de dados separado
      };

      // Adicionar o caminho do backend ao PYTHONPATH
      if (Platform.isWindows || Platform.isLinux || Platform.isMacOS) {
        serverEnv['PYTHONPATH'] = backendPath;
      }

      // Iniciar o processo Python para o servidor
      _pythonProcess = await Process.start(
        pythonPath,
        serverArgs,
        workingDirectory: backendPath,
        environment: serverEnv,
      );

      // Escutar stdout para detectar quando o servidor está rodando
      _pythonProcess!.stdout.transform(utf8.decoder).listen((data) {
        _addLog(data);

        // Verificar se o servidor está rodando
        if (data.contains('Uvicorn running on') ||
            data.contains('Application startup complete') ||
            data.contains('Iniciando servidor na porta')) {
          _isRunning.value = true;
          _status.value = true;
          _addLog('Servidor iniciado com sucesso na porta $port');
          pythonState.value = BackendInitStep.completed;
        }
      });

      // Escutar stderr
      _pythonProcess!.stderr.transform(utf8.decoder).listen((data) {
        _addLog('ERR: $data');

        // Detectar erros comuns
        if (data.contains('Address already in use') || data.contains('Erro ao iniciar servidor')) {
          _addLog('ERRO: Porta $port já está em uso. Tente encerrar outros processos ou usar outra porta.');
          pythonState.value = BackendInitStep.failed;
        }
      });

      // Monitorar o processo para detectar quando ele encerra
      _pythonProcess!.exitCode.then((exitCode) {
        LoggerUtil.debug('Processo Python encerrou com código: $exitCode');

        if (exitCode < 0) {
          // Se o processo foi terminado com sinal negativo (ex: SIGTERM, SIGKILL)
          _addLog('Processo recebeu sinal de terminação (código $exitCode)');
        } else {
          _addLog('Servidor encerrado (código $exitCode)');
        }

        _isRunning.value = false;
        _pythonProcess = null;
        _status.value = false;
      });

      // Dar um tempo para o servidor iniciar
      await Future.delayed(const Duration(seconds: 2));

      // Definir servidor como em execução, mesmo antes da verificação de saúde
      _isRunning.value = true;
      _status.value = true;
      pythonState.value = BackendInitStep.healthCheck;

      return true;
    } catch (e) {
      LoggerUtil.error('Erro ao iniciar servidor Python', e);
      _addLog('Erro ao iniciar servidor: $e');
      _isRunning.value = false;
      pythonState.value = BackendInitStep.failed;
      return false;
    }
  }

  Future<String?> findPythonPath() async {
    // Tentar primeiro o Python do ambiente virtual
    final pythonExe = await pythonExecutable;
    if (await File(pythonExe).exists()) {
      return pythonExe;
    }

    // Verificar caminhos conhecidos no macOS
    if (Platform.isMacOS) {
      final commonPaths = [
        '/usr/bin/python3',
        '/usr/local/bin/python3',
        '/opt/homebrew/bin/python3',
        '/usr/bin/python',
      ];

      for (final pythonPath in commonPaths) {
        if (await File(pythonPath).exists()) {
          return pythonPath;
        }
      }
    }

    // Em último caso, tentar 'python3' e 'python'
    try {
      final result = await Process.run('python3', ['--version']);
      if (result.exitCode == 0) {
        return 'python3';
      }
    } catch (e) {
      // Tentar 'python' se 'python3' falhar
    }

    return 'python';
  }

  Future<bool> stopServer({bool force = false}) async {
    if (!_isRunning.value && !force) {
      return true;
    }

    try {
      _addLog('Encerrando servidor...');

      // Se o processo ainda existe, tente matá-lo
      if (_pythonProcess != null) {
        try {
          // Primeiro tente finalizar normalmente
          final killed = _pythonProcess!.kill(ProcessSignal.sigterm);

          // Aguarde um tempo para que o processo termine normalmente
          if (killed) {
            await Future.delayed(const Duration(seconds: 2));
          }

          // Verifique se o processo ainda está em execução
          if (!killed || _pythonProcess!.kill(ProcessSignal.sigterm)) {
            _addLog('Servidor não respondeu ao SIGTERM, forçando encerramento...');
            _pythonProcess!.kill(ProcessSignal.sigkill);
            await Future.delayed(const Duration(seconds: 1));
          }
        } catch (e) {
          _addLog('Erro ao encerrar processo: $e');
          // Se force=true, continue mesmo com erro
          if (!force) {
            return false;
          }
        }
      }

      // Tentar finalizar processos Python usando comandos do sistema operacional
      if (Platform.isMacOS || Platform.isLinux) {
        await _killPythonProcesses();
      } else if (Platform.isWindows) {
        await _killPythonProcessesWindows();
      }

      // Definir estado como parado
      _isRunning.value = false;
      _status.value = false;
      _addLog('Servidor encerrado');

      // Limpar a referência ao processo
      _pythonProcess = null;

      return true;
    } catch (e) {
      _addLog('Erro ao encerrar servidor: $e');

      // Se force=true, considere o servidor como parado mesmo com erro
      if (force) {
        _isRunning.value = false;
        _status.value = false;
        _pythonProcess = null;
        return true;
      }

      return false;
    }
  }

  // Método para encerrar todos os processos Python relacionados no macOS/Linux
  Future<void> _killPythonProcesses() async {
    try {
      final scriptPath = await startScriptPath;
      final backendPath = await pythonBackendPath;

      _addLog('Verificando processos Python relacionados...');

      // Primeiro tentar matar processos usando pgrep (mais preciso)
      try {
        final pgrepResult = await Process.run(
          'pgrep',
          ['-f', 'python.*start_backend|python.*microdetect'],
          stdoutEncoding: utf8,
        );

        if (pgrepResult.exitCode == 0 && (pgrepResult.stdout as String).isNotEmpty) {
          final pids = (pgrepResult.stdout as String).trim().split('\n');
          _addLog('Encontrados ${pids.length} processo(s) Python com pgrep');

          for (final pid in pids) {
            if (pid.isNotEmpty) {
              _addLog('Encerrando processo Python PID: $pid via SIGTERM');
              await Process.run('kill', [pid]);
              await Future.delayed(const Duration(milliseconds: 300));

              // Verificar se ainda está em execução e usar SIGKILL se necessário
              final checkResult = await Process.run('ps', ['-p', pid]);
              if (checkResult.exitCode == 0 && (checkResult.stdout as String).contains(pid)) {
                _addLog('Forçando encerramento do processo PID: $pid via SIGKILL');
                await Process.run('kill', ['-9', pid]);
              }
            }
          }

          return; // Se encontrou com pgrep, não precisa continuar
        }
      } catch (e) {
        _addLog('Erro ao usar pgrep: $e - tentando método alternativo');
      }

      // Método alternativo usando ps e filtro manual
      final result = await Process.run(
        'ps',
        ['-ef'],
        stdoutEncoding: utf8,
      );

      if (result.exitCode != 0) {
        _addLog('Erro ao buscar processos: ${result.stderr}');
        return;
      }

      // Filtrar linhas que contém o caminho do script ou palavras-chave relacionadas
      final lines = (result.stdout as String).split('\n');
      final pythonProcesses = lines.where((line) =>
      line.contains('python') &&
          (line.contains('start_backend.py') ||
              line.contains('microdetect') ||
              line.contains(scriptPath) ||
              line.contains(backendPath))
      ).toList();

      if (pythonProcesses.isEmpty) {
        _addLog('Nenhum processo Python relacionado foi encontrado');
        return;
      }

      _addLog('Encontrados ${pythonProcesses.length} processos Python relacionados via ps');

      // Encerrar cada processo encontrado
      for (final processLine in pythonProcesses) {
        final parts = processLine.trim().split(RegExp(r'\s+'));
        if (parts.length > 1) {
          final pid = parts[1];
          _addLog('Encerrando processo Python PID: $pid via SIGTERM');

          // Tentar encerrar de forma normal primeiro
          await Process.run('kill', [pid]);
          await Future.delayed(const Duration(milliseconds: 500));

          // Depois verificar se ainda existe e força encerramento se necessário
          final checkResult = await Process.run('ps', ['-p', pid]);
          if (checkResult.exitCode == 0 && (checkResult.stdout as String).contains(pid)) {
            _addLog('Forçando encerramento do processo PID: $pid via SIGKILL');
            await Process.run('kill', ['-9', pid]);
          }
        }
      }
    } catch (e) {
      _addLog('Erro ao encerrar processos Python: $e');
    }
  }

  // Método para encerrar processos Python no Windows
  Future<void> _killPythonProcessesWindows() async {
    try {
      _addLog('Encerrando processos Python no Windows...');

      // No Windows, tente encerrar todos os processos python.exe relacionados
      await Process.run(
        'taskkill',
        ['/F', '/IM', 'python.exe'],
        runInShell: true,
      );
    } catch (e) {
      _addLog('Erro ao encerrar processos Python no Windows: $e');
    }
  }

  Future<bool> checkServerHealth({int? port}) async {
    try {
      final client = HttpClient();
      client.connectionTimeout = const Duration(seconds: 10);

      final targetPort = port ?? _port.value;
      final url = 'http://${_host.value}:$targetPort/health';

      _addLog('Verificando saúde do servidor em $url');

      final request = await client.getUrl(Uri.parse(url))
          .timeout(const Duration(seconds: 10));

      final response = await request.close()
          .timeout(const Duration(seconds: 10));

      final responseBody = await response.transform(utf8.decoder).join();
      client.close();

      if (response.statusCode == 200) {
        try {
          final data = jsonDecode(responseBody);
          if (data['status'] == 'healthy') {
            _addLog('Servidor respondeu: saudável');
            pythonState.value = BackendInitStep.completed;
            return true;
          }
          _addLog('Servidor respondeu, mas status não é saudável: ${data['status']}');
        } catch (e) {
          // Se não conseguir decodificar o JSON, pelo menos a resposta foi 200
          _addLog('Servidor respondeu com status 200, mas JSON inválido: $responseBody');
          pythonState.value = BackendInitStep.completed;
          return true;
        }
      } else {
        _addLog('Servidor respondeu com status ${response.statusCode}: $responseBody');
      }

      return false;
    } on TimeoutException {
      _addLog('Timeout ao verificar saúde do servidor (servidor pode estar iniciando)');
      return false;
    } on SocketException catch (e) {
      _addLog('Erro de conexão: $e - Servidor provavelmente ainda não está rodando');
      return false;
    } catch (e) {
      _addLog('Erro ao verificar saúde do servidor: $e');
      return false;
    }
  }

// Funções de debugging para verificar o ambiente virtual no PythonService

  Future<bool> createVirtualEnvIfNeeded() async {
    try {
      final backendPath = await pythonBackendPath;
      LoggerUtil.debug(
          '[DEBUG venv] Verificando ambiente virtual em: $backendPath');

      final venvPath = Platform.isWindows
          ? path.join(backendPath, 'venv', 'Scripts', 'python.exe')
          : path.join(backendPath, 'venv', 'bin', 'python');

      LoggerUtil.debug(
          '[DEBUG venv] Procurando Python do ambiente virtual em: $venvPath');

      // Verificar se já existe
      if (await File(venvPath).exists()) {
        LoggerUtil.debug(
            '[DEBUG venv] Ambiente virtual Python já existe e está disponível');
        return true;
      } else {
        LoggerUtil.debug(
            '[DEBUG venv] Executável Python do ambiente virtual não encontrado');
      }

      // Verificar se o diretório venv existe, mesmo que o executável não exista
      final venvDir = Directory(path.join(backendPath, 'venv'));
      if (await venvDir.exists()) {
        LoggerUtil.debug(
            '[DEBUG venv] Diretório venv existe, mas executável Python não encontrado');

        // Verificar conteúdo para entender o que existe
        try {
          final venvContents = await venvDir.list(recursive: false).toList();
          LoggerUtil.debug(
              '[DEBUG venv] Conteúdo do diretório venv (${venvContents
                  .length} itens):');
          for (var entity in venvContents) {
            LoggerUtil.debug('[DEBUG venv] - ${path.basename(entity.path)}');
          }

          // Verificar subdiretórios específicos
          if (Platform.isWindows) {
            final scriptsDir = Directory(path.join(venvDir.path, 'Scripts'));
            if (await scriptsDir.exists()) {
              final scriptContents = await scriptsDir.list().toList();
              LoggerUtil.debug(
                  '[DEBUG venv] Conteúdo do diretório Scripts (${scriptContents
                      .length} itens):');
              for (var entity in scriptContents) {
                LoggerUtil.debug(
                    '[DEBUG venv] - ${path.basename(entity.path)}');
              }
            } else {
              LoggerUtil.debug(
                  '[DEBUG venv] Diretório Scripts não encontrado dentro do venv');
            }
          } else {
            final binDir = Directory(path.join(venvDir.path, 'bin'));
            if (await binDir.exists()) {
              final binContents = await binDir.list().toList();
              LoggerUtil.debug(
                  '[DEBUG venv] Conteúdo do diretório bin (${binContents
                      .length} itens):');
              for (var entity in binContents) {
                LoggerUtil.debug(
                    '[DEBUG venv] - ${path.basename(entity.path)}');
              }
            } else {
              LoggerUtil.debug(
                  '[DEBUG venv] Diretório bin não encontrado dentro do venv');
            }
          }
        } catch (e) {
          LoggerUtil.debug('[DEBUG venv] Erro ao listar conteúdo do venv: $e');
        }

        LoggerUtil.debug(
            '[DEBUG venv] Tentando usar assim mesmo, mas pode estar incompleto');
        return true;
      }

      LoggerUtil.debug(
          '[DEBUG venv] Ambiente virtual não existe, tentando criar...');

      // Encontrar um Python disponível no sistema
      String? systemPython = await _findSystemPython();
      if (systemPython == null) {
        LoggerUtil.debug(
            '[DEBUG venv] Não foi possível encontrar Python no sistema');
        return false;
      }

      LoggerUtil.debug(
          '[DEBUG venv] Python encontrado para criar ambiente: $systemPython');

      // Tenta criar o diretório venv se ele não existir
      if (!await venvDir.exists()) {
        try {
          await venvDir.create(recursive: true);
          LoggerUtil.debug('[DEBUG venv] Diretório venv criado');
        } catch (e) {
          LoggerUtil.debug('[DEBUG venv] Erro ao criar diretório venv: $e');
        }
      }

      // Executar comando para criar ambiente virtual
      try {
        final command = systemPython;
        final args = ['-m', 'venv', path.join(backendPath, 'venv')];

        LoggerUtil.debug(
            '[DEBUG venv] Executando comando: $command ${args.join(' ')}');

        final result = await Process.run(
          command,
          args,
          runInShell: true,
        );

        if (result.exitCode != 0) {
          LoggerUtil.debug('[DEBUG venv] Erro ao criar ambiente virtual:');
          LoggerUtil.debug('[DEBUG venv] - STDOUT: ${result.stdout}');
          LoggerUtil.debug('[DEBUG venv] - STDERR: ${result.stderr}');

          // Verificar módulo venv
          try {
            final checkVenv = await Process.run(
              systemPython,
              ['-c', 'import venv; print("venv module available")'],
            );

            if (checkVenv.exitCode == 0) {
              LoggerUtil.debug('[DEBUG venv] Módulo venv está disponível');
            } else {
              LoggerUtil.debug(
                  '[DEBUG venv] Módulo venv NÃO disponível, tentando instalar...');
              // Em alguns sistemas pode ser necessário instalar o pacote venv separadamente
              if (Platform.isLinux) {
                try {
                  LoggerUtil.debug(
                      '[DEBUG venv] Tentando instalar python3-venv via apt-get');
                  final aptResult = await Process.run(
                      'sudo', ['apt-get', 'install', '-y', 'python3-venv']);
                  LoggerUtil.debug(
                      '[DEBUG venv] Resultado instalação apt: ${aptResult
                          .exitCode}');

                  if (aptResult.exitCode == 0) {
                    // Tentar criar o ambiente novamente
                    final retryResult = await Process.run(
                      systemPython,
                      ['-m', 'venv', path.join(backendPath, 'venv')],
                    );

                    if (retryResult.exitCode == 0) {
                      LoggerUtil.debug(
                          '[DEBUG venv] Ambiente virtual criado com sucesso após instalar venv');
                      return true;
                    }
                  }
                } catch (aptError) {
                  LoggerUtil.debug(
                      '[DEBUG venv] Erro ao instalar python3-venv: $aptError');
                }
              }
            }
          } catch (e) {
            LoggerUtil.debug('[DEBUG venv] Erro ao verificar módulo venv: $e');
          }

          LoggerUtil.debug(
              '[DEBUG venv] Usando Python do sistema como alternativa');
          return true;
        }

        LoggerUtil.debug(
            '[DEBUG venv] Ambiente virtual Python criado com sucesso');

        // Verificar se foi realmente criado
        if (Platform.isWindows) {
          final pythonExe = File(
              path.join(backendPath, 'venv', 'Scripts', 'python.exe'));
          LoggerUtil.debug(
              '[DEBUG venv] Python.exe exists: ${await pythonExe.exists()}');
        } else {
          final pythonBin = File(
              path.join(backendPath, 'venv', 'bin', 'python'));
          LoggerUtil.debug(
              '[DEBUG venv] Python bin exists: ${await pythonBin.exists()}');
        }

        return true;
      } catch (e) {
        LoggerUtil.debug('[DEBUG venv] Exceção ao criar ambiente virtual: $e');
        return true;
      }
    } catch (e) {
      LoggerUtil.debug('[DEBUG venv] Erro ao criar ambiente virtual: $e');
      return false;
    }
  }

  Future<String?> _findSystemPython() async {
    // Verificar caminhos conhecidos
    final pythonPaths = Platform.isWindows
        ? ['python', 'python3', 'C:\\Python39\\python.exe', 'C:\\Python310\\python.exe']
        : ['/usr/bin/python3', '/usr/local/bin/python3', '/opt/homebrew/bin/python3', 'python3', 'python'];

    for (final pythonPath in pythonPaths) {
      try {
        final result = await Process.run(pythonPath, ['--version'], runInShell: true);
        if (result.exitCode == 0) {
          return pythonPath;
        }
      } catch (e) {
        // Continuar tentando outros caminhos
      }
    }

    return null;
  }

  // Adicionar log à lista observável
  void _addLog(String message) {
    // Remover quebras de linha extras e espaços em branco
    final cleanedMessage = message.trim();
    if (cleanedMessage.isEmpty) return;

    // Adicionar à lista observable
    _logs.add(cleanedMessage);

    // Limitar o tamanho da lista para evitar uso excessivo de memória
    if (_logs.length > 100) {
      _logs.removeRange(0, _logs.length - 100);
    }

    // Também logar para debug se necessário
    LoggerUtil.debug('[PythonService] $cleanedMessage');
  }
}