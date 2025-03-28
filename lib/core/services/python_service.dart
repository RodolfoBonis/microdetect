import 'dart:async';
import 'dart:io';
import 'dart:convert';
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
  final currentVersion = ''.obs;
  final latestVersion = ''.obs;

  // Private variables
  Process? _pythonProcess;
  String? _pythonPath;
  String? _pipPath;
  String? _microdetectPath;

  // AWS CodeArtifact configuration
  final String _awsRegion = '';
  final String _codeArtifactDomain = '';
  final String _codeArtifactRepository = '';
  final String _codeArtifactOwner = ''; // AWS Account ID

  // Getters
  bool get isRunning => _isRunning.value;
  String get baseUrl => 'http://${_host.value}:${_port.value}';
  int get port => _port.value;
  List<String> get logs => _logs.toList();
  Stream<bool> get statusStream => _status.stream;

  // Diretório para os dados do aplicativo
  Future<String> get appDataDir async {
    await AppDirectories.instance.ensureInitialized();
    return AppDirectories.instance.dataDir.path;
  }

  @override
  void onInit() {
    super.onInit();
    // Localizar executáveis Python durante inicialização
    _initializePythonEnvironment();
  }

  @override
  void onClose() {
    stopServer(force: true);
    super.onClose();
  }

  /// Inicializa o ambiente Python localizando executáveis
  Future<void> _initializePythonEnvironment() async {
    _addLog('Inicializando ambiente Python...');

    try {
      // Localizar o Python
      _pythonPath = await _findPythonExecutable();
      if (_pythonPath != null) {
        _addLog('Python encontrado: $_pythonPath');
      } else {
        _addLog('AVISO: Python não encontrado no sistema');
      }

      // Localizar PIP
      _pipPath = await _findPipExecutable();
      if (_pipPath != null) {
        _addLog('Pip encontrado: $_pipPath');
      } else {
        _addLog('AVISO: Pip não encontrado no sistema');
      }

      // Verificar se o microdetect está instalado
      await checkCurrentVersion();

      // Localizar comando microdetect (se instalado)
      if (currentVersion.value.isNotEmpty) {
        _microdetectPath = await _findMicrodetectExecutable();
        if (_microdetectPath != null) {
          _addLog('Microdetect encontrado: $_microdetectPath');
        } else {
          _addLog('AVISO: Executable microdetect não encontrado');
        }
      }
    } catch (e) {
      _addLog('Erro ao inicializar ambiente Python: $e');
    }
  }

  Future<bool> pythonIsAvailable() async {
    final pythonExecutable = await _findPythonExecutable();

    return pythonExecutable != null;
  }

  Future<bool> pipIsAvailble() async {
    final pipExecutable = await _findPipExecutable();

    return pipExecutable != null;
  }

  /// Localiza o executável Python no sistema
  Future<String?> _findPythonExecutable() async {
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
        r'C:\Program Files (x86)\Python39\python.exe',
        r'C:\Program Files (x86)\Python310\python.exe',
        r'C:\Program Files (x86)\Python311\python.exe',
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

    // Verificar se o executável existe diretamente (para caminhos absolutos)
    for (final command in possibleCommands) {
      if (command.startsWith('/') || command.contains(':')) {
        if (await File(command).exists()) {
          // Testar se realmente é o Python executando uma verificação de versão
          try {
            final result = await Process.run(
                command,
                ['--version'],
                stdoutEncoding: utf8,
                stderrEncoding: utf8
            );

            if (result.exitCode == 0 &&
                (result.stdout.toString().toLowerCase().contains('python') ||
                    result.stderr.toString().toLowerCase().contains('python'))) {
              return command;
            }
          } catch (_) {
            // Continuar para a próxima tentativa
          }
        }
      }
    }

    // Verificar comandos usando where/which
    final whereCommand = Platform.isWindows ? 'where' : 'which';

    for (final command in possibleCommands) {
      if (!command.startsWith('/') && !command.contains(':')) {
        try {
          final result = await Process.run(
              whereCommand,
              [command],
              stdoutEncoding: utf8,
              stderrEncoding: utf8
          );

          if (result.exitCode == 0) {
            // Pegar a primeira linha da saída (pode haver múltiplos caminhos)
            final foundPath = result.stdout.toString().trim().split('\n').first;

            // Verificar se o arquivo existe
            if (await File(foundPath).exists()) {
              return foundPath;
            }
          }
        } catch (_) {
          // Continuar para a próxima tentativa
        }
      }
    }

    // Se chegamos aqui, não conseguimos encontrar o Python
    return null;
  }

  /// Localiza o executável pip no sistema
  Future<String?> _findPipExecutable() async {
    // Se já temos o Python, tente usar o pip via módulo Python
    if (_pythonPath != null) {
      try {
        return _pythonPath; // Usaremos -m pip para execução
      } catch (_) {
        // Continuar com outras tentativas
      }
    }

    List<String> possibleCommands = [];

    if (Platform.isWindows) {
      possibleCommands = [
        'pip',
        'pip3',
        r'C:\Python39\Scripts\pip.exe',
        r'C:\Python310\Scripts\pip.exe',
        r'C:\Python311\Scripts\pip.exe',
        r'C:\Program Files\Python39\Scripts\pip.exe',
        r'C:\Program Files\Python310\Scripts\pip.exe',
        r'C:\Program Files\Python311\Scripts\pip.exe',
      ];
    } else {
      // macOS e Linux
      possibleCommands = [
        '/usr/bin/pip3',
        '/usr/local/bin/pip3',
        '/opt/homebrew/bin/pip3',
        '/usr/bin/pip',
        'pip3',
        'pip',
      ];
    }

    // Verificar se o executável existe diretamente
    for (final command in possibleCommands) {
      if (command.startsWith('/') || command.contains(':')) {
        if (await File(command).exists()) {
          try {
            final result = await Process.run(
                command,
                ['--version'],
                stdoutEncoding: utf8,
                stderrEncoding: utf8
            );

            if (result.exitCode == 0 &&
                result.stdout.toString().toLowerCase().contains('pip')) {
              return command;
            }
          } catch (_) {
            // Continuar para a próxima tentativa
          }
        }
      }
    }

    // Verificar comandos usando where/which
    final whereCommand = Platform.isWindows ? 'where' : 'which';

    for (final command in possibleCommands) {
      if (!command.startsWith('/') && !command.contains(':')) {
        try {
          final result = await Process.run(
              whereCommand,
              [command],
              stdoutEncoding: utf8,
              stderrEncoding: utf8
          );

          if (result.exitCode == 0) {
            final foundPath = result.stdout.toString().trim().split('\n').first;
            if (await File(foundPath).exists()) {
              return foundPath;
            }
          }
        } catch (_) {
          // Continuar para a próxima tentativa
        }
      }
    }

    // Se chegamos aqui, não conseguimos encontrar o pip
    return null;
  }

  /// Localiza o executável microdetect
  Future<String?> _findMicrodetectExecutable() async {
    List<String> possibleCommands = [];

    if (Platform.isWindows) {
      possibleCommands = [
        'microdetect',
        r'C:\Python39\Scripts\microdetect.exe',
        r'C:\Python310\Scripts\microdetect.exe',
        r'C:\Python311\Scripts\microdetect.exe',
        r'C:\Program Files\Python39\Scripts\microdetect.exe',
        r'C:\Program Files\Python310\Scripts\microdetect.exe',
        r'C:\Program Files\Python311\Scripts\microdetect.exe',
      ];
    } else {
      // macOS e Linux
      possibleCommands = [
        '/usr/bin/microdetect',
        '/usr/local/bin/microdetect',
        '/opt/homebrew/bin/microdetect',
        'microdetect',
      ];
    }

    // Verificar se o executável existe diretamente
    for (final command in possibleCommands) {
      if (command.startsWith('/') || command.contains(':')) {
        if (await File(command).exists()) {
          try {
            final result = await Process.run(
                command,
                ['version'],
                stdoutEncoding: utf8,
                stderrEncoding: utf8
            );

            if (result.exitCode == 0 &&
                result.stdout.toString().toLowerCase().contains('microdetect')) {
              return command;
            }
          } catch (_) {
            // Continuar para a próxima tentativa
          }
        }
      }
    }

    // Verificar comandos usando where/which
    final whereCommand = Platform.isWindows ? 'where' : 'which';

    for (final command in possibleCommands) {
      if (!command.startsWith('/') && !command.contains(':')) {
        try {
          final result = await Process.run(
              whereCommand,
              [command],
              stdoutEncoding: utf8,
              stderrEncoding: utf8
          );

          if (result.exitCode == 0) {
            final foundPath = result.stdout.toString().trim().split('\n').first;
            if (await File(foundPath).exists()) {
              return foundPath;
            }
          }
        } catch (_) {
          // Continuar para a próxima tentativa
        }
      }
    }

    // Se temos Python mas não encontramos o microdetect diretamente,
    // podemos usar o módulo como fallback
    if (_pythonPath != null) {
      return _pythonPath; // Usaremos -m microdetect para execução
    }

    return null;
  }

  /// Executa um comando pip com o caminho completo do executável
  Future<ProcessResult> _runPipCommand(List<String> args, {Map<String, String>? environment}) async {
    if (_pipPath == null) {
      // Se não encontramos o pip diretamente, usar python -m pip
      if (_pythonPath == null) {
        throw Exception('Python não encontrado no sistema');
      }

      // Definir ambiente base para evitar interação
      final Map<String, String> baseEnvironment = {
        'PIP_NO_INPUT': '1',
        'PYTHONIOENCODING': 'utf-8',
        'PYTHONUNBUFFERED': '1',
      };

      // Mesclar com o ambiente fornecido
      final completeEnvironment = {...baseEnvironment};
      if (environment != null) {
        completeEnvironment.addAll(environment);
      }

      // Verificar se a execução é em modo não interativo
      final isInteractive = stdout.hasTerminal && stdin.hasTerminal;
      if (!isInteractive) {
        _addLog('Executando pip em modo não interativo');
        completeEnvironment['PIP_NO_INPUT'] = '1';
        // Evitar requisitos específicos de entrada em terminais não interativos
        if (!args.contains('--no-input') && !args.contains('--quiet')) {
          args = [...args, '--no-input', '--quiet'];
        }
      }

      return Process.run(
          _pythonPath!,
          ['-m', 'pip', ...args],
          stdoutEncoding: utf8,
          stderrEncoding: utf8,
          environment: completeEnvironment,
          runInShell: true // Usar runInShell para melhor tratamento das saídas
      );
    } else if (_pipPath == _pythonPath) {
      // Se estamos usando python -m pip
      final Map<String, String> baseEnvironment = {
        'PIP_NO_INPUT': '1',
        'PYTHONIOENCODING': 'utf-8',
        'PYTHONUNBUFFERED': '1',
      };

      final completeEnvironment = {...baseEnvironment};
      if (environment != null) {
        completeEnvironment.addAll(environment);
      }

      final isInteractive = stdout.hasTerminal && stdin.hasTerminal;
      if (!isInteractive) {
        if (!args.contains('--no-input') && !args.contains('--quiet')) {
          args = [...args, '--no-input', '--quiet'];
        }
      }

      return Process.run(
          _pythonPath!,
          ['-m', 'pip', ...args],
          stdoutEncoding: utf8,
          stderrEncoding: utf8,
          environment: completeEnvironment,
          runInShell: true
      );
    } else {
      // Usar o pip diretamente
      final Map<String, String> baseEnvironment = {
        'PIP_NO_INPUT': '1',
        'PYTHONIOENCODING': 'utf-8',
        'PYTHONUNBUFFERED': '1',
      };

      final completeEnvironment = {...baseEnvironment};
      if (environment != null) {
        completeEnvironment.addAll(environment);
      }

      final isInteractive = stdout.hasTerminal && stdin.hasTerminal;
      if (!isInteractive) {
        if (!args.contains('--no-input') && !args.contains('--quiet')) {
          args = [...args, '--no-input', '--quiet'];
        }
      }

      return Process.run(
          _pipPath!,
          args,
          stdoutEncoding: utf8,
          stderrEncoding: utf8,
          environment: completeEnvironment,
          runInShell: true
      );
    }
  }

  Future<ProcessResult> runPipCommandDirectly(List<String> args, Map<String, String>? environment) async {
    return _runPipCommand(args, environment: environment);
  }

  /// Executa um comando microdetect com o caminho completo do executável
  Future<Process> _startMicrodetectCommand(List<String> args, {Map<String, String>? environment}) async {
    if (_microdetectPath == null) {
      throw Exception('Microdetect não encontrado no sistema');
    }

    if (_microdetectPath == _pythonPath) {
      // Se estamos usando python -m microdetect
      return Process.start(
          _pythonPath!,
          ['-m', 'microdetect', ...args],
          environment: environment
      );
    } else {
      // Usar o microdetect diretamente
      return Process.start(
          _microdetectPath!,
          args,
          environment: environment
      );
    }
  }

  /// Método legado para compatibilidade com BackendInstallerService
  Future<bool> createVirtualEnvIfNeeded() async {
    // Essa função não é mais necessária com a abordagem pip, mas mantida por compatibilidade
    try {
      // Verificar se os executáveis Python foram localizados
      if (_pythonPath == null) {
        _pythonPath = await _findPythonExecutable();
        if (_pythonPath == null) {
          _addLog('Python não encontrado no sistema');
          return false;
        }
      }

      if (_pipPath == null) {
        _pipPath = await _findPipExecutable();
        if (_pipPath == null && _pythonPath != null) {
          // Tentar usar python -m pip se o pip não for encontrado diretamente
          _pipPath = _pythonPath;
        }
      }

      // Verificar se o pacote microdetect está instalado
      await checkCurrentVersion();
      if (currentVersion.value.isEmpty) {
        _addLog('Pacote microdetect não instalado, tentando instalar...');
        return await installOrUpdate();
      }

      return true;
    } catch (e) {
      _addLog('Erro ao verificar ambiente Python: $e');
      return false;
    }
  }

  /// Verifica a versão atual do pacote instalado
  Future<void> checkCurrentVersion() async {
    try {
      if (_pipPath == null) {
        await _initializePythonEnvironment();
        if (_pipPath == null) {
          _addLog('Pip não encontrado, não é possível verificar a versão do microdetect');
          currentVersion.value = '';
          return;
        }
      }

      final result = await _runPipCommand(['show', 'microdetect']);

      if (result.exitCode == 0) {
        // Extrair versão da saída do pip show (formato: "Version: X.Y.Z")
        final output = result.stdout.toString();
        final versionMatch = RegExp(r'Version:\s+(\d+\.\d+\.\d+)').firstMatch(output);

        if (versionMatch != null) {
          currentVersion.value = versionMatch.group(1)!;
          _addLog('Versão atual do microdetect: ${currentVersion.value}');
        } else {
          _addLog('Não foi possível determinar a versão atual do microdetect');
          currentVersion.value = '';
        }
      } else {
        _addLog('Pacote microdetect não está instalado');
        currentVersion.value = '';
      }
    } catch (e) {
      _addLog('Erro ao verificar versão atual: $e');
      currentVersion.value = '';
    }
  }

  /// Verifica se há atualizações disponíveis no CodeArtifact
  Future<bool> checkForUpdates() async {
    try {
      _addLog('Verificando atualizações disponíveis...');

      if (_pipPath == null) {
        await _initializePythonEnvironment();
        if (_pipPath == null) {
          _addLog('Pip não encontrado, não é possível verificar atualizações');
          return false;
        }
      }

      // Primeiro obter o token de autenticação da AWS
      final token = await _getAwsAuthToken();
      if (token == null) {
        _addLog('Não foi possível obter token de autenticação AWS');
        return false;
      }

      // Index URL para o CodeArtifact
      final indexUrl = 'https://$_codeArtifactDomain-$_codeArtifactOwner.d.codeartifact.$_awsRegion.amazonaws.com/pypi/$_codeArtifactRepository/simple/';

      // Verifica a versão mais recente disponível
      final result = await _runPipCommand(
          ['install', 'microdetect==', '--no-deps', '--dry-run', '--index-url', indexUrl, '--extra-index-url', 'https://pypi.org/simple'],
          environment: {'AWS_CODEARTIFACT_TOKEN': token}
      );

      // Analisar a saída para encontrar a versão mais recente disponível
      final output = result.stderr.toString();
      final versionMatch = RegExp(r'microdetect (\d+\.\d+\.\d+)').firstMatch(output);

      if (versionMatch != null) {
        latestVersion.value = versionMatch.group(1)!;
        _addLog('Versão mais recente disponível: ${latestVersion.value}');

        // Verificar se a versão mais recente é diferente da atual
        final hasUpdate = currentVersion.value != latestVersion.value;
        _addLog(hasUpdate
            ? 'Atualização disponível: ${currentVersion.value} -> ${latestVersion.value}'
            : 'Versão já atualizada: ${currentVersion.value}');

        return hasUpdate;
      } else {
        _addLog('Não foi possível determinar a versão mais recente');
        return false;
      }
    } catch (e) {
      _addLog('Erro ao verificar atualizações: $e');
      return false;
    }
  }

  /// Obtém um token de autenticação para AWS CodeArtifact
  Future<String?> _getAwsAuthToken() async {
    try {
      // Verificar se o comando AWS está disponível
      final awsPath = await _findAwsExecutable();
      if (awsPath == null) {
        _addLog('AWS CLI não encontrado no sistema');
        return null;
      }

      final result = await Process.run(
          awsPath,
          ['codeartifact', 'get-authorization-token',
            '--domain', _codeArtifactDomain,
            '--domain-owner', _codeArtifactOwner,
            '--query', 'authorizationToken',
            '--output', 'text'],
          stdoutEncoding: utf8,
          stderrEncoding: utf8
      );

      if (result.exitCode != 0) {
        _addLog('Erro ao obter token AWS: ${result.stderr}');
        return null;
      }

      return result.stdout.toString().trim();
    } catch (e) {
      _addLog('Erro ao obter token AWS: $e');
      return null;
    }
  }

  /// Encontra o executável AWS CLI
  Future<String?> _findAwsExecutable() async {
    List<String> possibleCommands = [];

    if (Platform.isWindows) {
      possibleCommands = [
        'aws',
        r'C:\Program Files\Amazon\AWSCLIV2\aws.exe',
        r'C:\Program Files (x86)\Amazon\AWSCLIV2\aws.exe',
      ];
    } else {
      // macOS e Linux
      possibleCommands = [
        '/usr/bin/aws',
        '/usr/local/bin/aws',
        '/opt/homebrew/bin/aws',
        'aws',
      ];
    }

    // Verificar se o executável existe diretamente
    for (final command in possibleCommands) {
      if (command.startsWith('/') || command.contains(':')) {
        if (await File(command).exists()) {
          return command;
        }
      }
    }

    // Verificar comandos usando where/which
    final whereCommand = Platform.isWindows ? 'where' : 'which';

    for (final command in possibleCommands) {
      if (!command.startsWith('/') && !command.contains(':')) {
        try {
          final result = await Process.run(
              whereCommand,
              [command],
              stdoutEncoding: utf8,
              stderrEncoding: utf8
          );

          if (result.exitCode == 0) {
            final foundPath = result.stdout.toString().trim().split('\n').first;
            if (await File(foundPath).exists()) {
              return foundPath;
            }
          }
        } catch (_) {
          // Continuar para a próxima tentativa
        }
      }
    }

    return null;
  }

  /// Configura as credenciais da AWS
  Future<bool> _configureAwsCredentials(String accessKeyId, String secretAccessKey) async {
    try {
      final awsPath = await _findAwsExecutable();
      if (awsPath == null) {
        _addLog('AWS CLI não encontrado no sistema');
        return false;
      }

      // Configurar AWS CLI
      await Process.run(
          awsPath,
          ['configure', 'set', 'aws_access_key_id', accessKeyId],
          stdoutEncoding: utf8,
          stderrEncoding: utf8
      );

      await Process.run(
          awsPath,
          ['configure', 'set', 'aws_secret_access_key', secretAccessKey],
          stdoutEncoding: utf8,
          stderrEncoding: utf8
      );

      await Process.run(
          awsPath,
          ['configure', 'set', 'region', _awsRegion],
          stdoutEncoding: utf8,
          stderrEncoding: utf8
      );

      return true;
    } catch (e) {
      _addLog('Erro ao configurar credenciais AWS: $e');
      return false;
    }
  }

  /// Instala ou atualiza o pacote microdetect via pip
  Future<bool> installOrUpdate({bool force = false}) async {
    try {
      _addLog('Instalando/atualizando pacote microdetect...');

      if (_pipPath == null) {
        await _initializePythonEnvironment();
        if (_pipPath == null) {
          _addLog('Pip não encontrado, não é possível instalar o microdetect');
          return false;
        }
      }

      // Verificar versão atual
      if (!force) {
        await checkCurrentVersion();
      }

      // Criar mapa de ambiente que evita a solicitação de entrada interativa
      final environment = {
        'PIP_NO_INPUT': '1',           // Evita que o pip solicite qualquer entrada
        'PIP_DISABLE_PIP_VERSION_CHECK': '1', // Evita verificação de versão do pip
        'PYTHONIOENCODING': 'utf-8',   // Garante codificação correta
        'PYTHONUNBUFFERED': '1',       // Evita buffering da saída
      };

      // Usar o PyPI padrão em vez do AWS CodeArtifact para evitar problemas de autenticação
      _addLog('Instalando pacote microdetect do PyPI...');

      // Instalar com opções seguras para evitar entrada interativa
      final result = await _runPipCommand(
          ['install', 'microdetect', '--upgrade', '--no-input', '--quiet',
            '--user', '--no-cache-dir', '--default-timeout', '60',
            '--retries', '3', '--index-url', 'https://pypi.org/simple'],
          environment: environment
      );

      if (result.exitCode == 0) {
        _addLog('Pacote microdetect instalado/atualizado com sucesso');

        // Atualizar versão atual e procurar o executável microdetect
        await checkCurrentVersion();
        _microdetectPath = await _findMicrodetectExecutable();

        return true;
      } else {
        // Tentar novamente com configuração mais simples em caso de falha
        _addLog('Primeira tentativa falhou, tentando com opções mais simples...');

        final secondAttempt = await _runPipCommand(
            ['install', 'microdetect', '--user', '--no-input'],
            environment: environment
        );

        if (secondAttempt.exitCode == 0) {
          _addLog('Pacote microdetect instalado com sucesso na segunda tentativa');

          await checkCurrentVersion();
          _microdetectPath = await _findMicrodetectExecutable();

          return true;
        }

        _addLog('Erro ao instalar pacote: ${result.stderr}');
        return false;
      }
    } catch (e) {
      _addLog('Erro ao instalar/atualizar pacote: $e');
      return false;
    }
  }

  /// Inicia o servidor microdetect
  Future<bool> startServer({int port = 8000}) async {
    if (_isRunning.value) {
      _addLog('Servidor já está rodando');
      return true;
    }

    try {
      _port.value = port;
      pythonState.value = BackendInitStep.serverStartup;

      // Obter diretório de dados
      final dataDir = await appDataDir;

      _addLog('Iniciando servidor microdetect na porta $port...');
      _addLog('Diretório de dados: $dataDir');

      // CORREÇÃO: Tentar vários métodos para iniciar o servidor

      // 1. Primeiro, tentar localizar o executável microdetect (método preferido)
      String? microdetectExe = await _findExecutableInPath('microdetect');

      if (microdetectExe != null) {
        _addLog('Executável microdetect encontrado: $microdetectExe');

        // Iniciar processo usando o executável diretamente
        _pythonProcess = await Process.start(
            microdetectExe,
            ['start-server', '--port', port.toString(), '--data-dir', dataDir],
            environment: {
              'PYTHONUNBUFFERED': '1',
            }
        );
      }
      // 2. Se não encontrar, tentar via python -m microdetect.server
      else if (_pythonPath != null) {
        _addLog('Executável microdetect não encontrado. Tentando via módulo Python...');

        _pythonProcess = await Process.start(
            _pythonPath!,
            ['-m', 'microdetect.server', 'start-server', '--port', port.toString(), '--data-dir', dataDir],
            environment: {
              'PYTHONUNBUFFERED': '1',
            }
        );
      } else {
        throw Exception('Nem Python nem microdetect encontrados no sistema');
      }

      // Capturar saída padrão
      _pythonProcess!.stdout
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((data) {
        _addLog(data);

        // Detectar quando o servidor está rodando
        if (data.contains('Application startup complete') ||
            data.contains('Uvicorn running on') ||
            data.contains('Iniciando servidor na porta')) {
          _isRunning.value = true;
          _status.value = true;
          pythonState.value = BackendInitStep.completed;
        }
      });

      // Capturar saída de erro
      _pythonProcess!.stderr
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((data) {
        _addLog('ERROR: $data');

        // Detectar erros comuns
        if (data.contains('Address already in use')) {
          _addLog('ERRO: Porta $port já está em uso');
          pythonState.value = BackendInitStep.failed;
        }
      });

      // Monitorar encerramento do processo
      _pythonProcess!.exitCode.then((exitCode) {
        _addLog('Servidor encerrado com código $exitCode');
        _isRunning.value = false;
        _status.value = false;
        _pythonProcess = null;
      });

      // Aguardar um tempo para o servidor iniciar
      await Future.delayed(const Duration(seconds: 5));

      // Verificar saúde do servidor
      final isHealthy = await checkServerHealth();

      if (isHealthy) {
        _addLog('Servidor iniciado com sucesso e está respondendo');
        _isRunning.value = true;
        _status.value = true;
        pythonState.value = BackendInitStep.completed;
        return true;
      } else if (_isRunning.value) {
        // Se o processo está rodando, mas não responde à verificação de saúde,
        // ainda consideramos como em execução mas logamos um aviso
        _addLog('Servidor iniciado, mas não está respondendo ao health check');
        return true;
      } else {
        _addLog('Erro ao iniciar servidor, processo não está em execução');
        pythonState.value = BackendInitStep.failed;
        return false;
      }
    } catch (e) {
      _addLog('Erro ao iniciar servidor: $e');
      pythonState.value = BackendInitStep.failed;
      return false;
    }
  }

  Future<String?> _findExecutableInPath(String executableName) async {
    final String command = Platform.isWindows ? 'where' : 'which';
    try {
      final result = await Process.run(command, [executableName]);
      if (result.exitCode == 0 && result.stdout.toString().trim().isNotEmpty) {
        return result.stdout.toString().trim().split('\n').first;
      }
    } catch (e) {
      _addLog('Erro ao procurar executável $executableName: $e');
    }
    return null;
  }

  /// Verifica a saúde do servidor
  Future<bool> checkServerHealth() async {
    try {
      final client = HttpClient();
      client.connectionTimeout = const Duration(seconds: 5);

      final url = 'http://${_host.value}:${_port.value}/health';

      final request = await client.getUrl(Uri.parse(url))
          .timeout(const Duration(seconds: 5));

      final response = await request.close()
          .timeout(const Duration(seconds: 5));

      final responseBody = await response.transform(utf8.decoder).join();
      client.close();

      if (response.statusCode == 200) {
        try {
          final data = jsonDecode(responseBody);
          return data['status'] == 'healthy';
        } catch (e) {
          // Se não conseguir decodificar o JSON, pelo menos respondeu com 200
          return true;
        }
      }

      return false;
    } on TimeoutException {
      _addLog('Timeout ao verificar saúde do servidor');
      return false;
    } on SocketException {
      _addLog('Erro de conexão ao verificar saúde do servidor');
      return false;
    } catch (e) {
      _addLog('Erro ao verificar saúde do servidor: $e');
      return false;
    }
  }

  /// Para o servidor microdetect
  Future<bool> stopServer({bool force = false}) async {
    if (!_isRunning.value && !force) {
      return true;
    }

    try {
      _addLog('Parando servidor...');

      if (_pythonProcess != null) {
        // Tentar parar o processo de forma limpa
        _pythonProcess!.kill();

        // Aguardar o processo encerrar
        await Future.delayed(const Duration(seconds: 2));

        // Se force=true e o processo ainda estiver rodando, usar SIGKILL
        if (force && _pythonProcess != null) {
          _pythonProcess!.kill(ProcessSignal.sigkill);
        }
      }

      // Em sistemas Unix, verificar e matar processos relacionados
      if (Platform.isLinux || Platform.isMacOS) {
        await _killRelatedProcesses();
      } else if (Platform.isWindows) {
        await _killWindowsProcesses();
      }

      _isRunning.value = false;
      _status.value = false;
      _pythonProcess = null;

      return true;
    } catch (e) {
      _addLog('Erro ao parar servidor: $e');

      if (force) {
        _isRunning.value = false;
        _status.value = false;
        _pythonProcess = null;
        return true;
      }

      return false;
    }
  }

  /// Mata processos relacionados em sistemas Unix
  Future<void> _killRelatedProcesses() async {
    try {
      // Procurar por processos microdetect ou python que contenham microdetect
      final result = await Process.run(
          'ps',
          ['-ef'],
          stdoutEncoding: utf8
      );

      if (result.exitCode == 0) {
        final output = result.stdout as String;
        final lines = output.split('\n');

        for (final line in lines) {
          if ((line.contains('python') && line.contains('microdetect')) ||
              line.contains('microdetect start-server')) {

            // Extrair o PID (geralmente o segundo campo)
            final parts = line.trim().split(RegExp(r'\s+'));
            if (parts.length > 1) {
              final pid = parts[1];
              _addLog('Matando processo relacionado PID: $pid');

              await Process.run('kill', ['-9', pid]);
            }
          }
        }
      }
    } catch (e) {
      _addLog('Erro ao matar processos relacionados: $e');
    }
  }

  /// Mata processos relacionados no Windows
  Future<void> _killWindowsProcesses() async {
    try {
      // Encerrar processos microdetect
      await Process.run(
          'taskkill',
          ['/F', '/IM', 'microdetect.exe'],
          runInShell: true
      );

      // Procurar processos Python que possam estar executando microdetect
      final result = await Process.run(
          'tasklist',
          ['/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
          stdoutEncoding: utf8,
          runInShell: true
      );

      if (result.exitCode == 0 && (result.stdout as String).contains('python.exe')) {
        await Process.run(
            'taskkill',
            ['/F', '/IM', 'python.exe'],
            runInShell: true
        );
      }
    } catch (e) {
      _addLog('Erro ao matar processos Windows: $e');
    }
  }

  /// Adiciona log à lista observável
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