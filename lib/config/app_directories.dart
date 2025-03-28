import 'dart:io';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

/// Gerenciador de diretórios da aplicação MicroDetect
class AppDirectories {
  // Singleton pattern
  AppDirectories._();

  static final AppDirectories _instance = AppDirectories._();

  static AppDirectories get instance => _instance;

  /// Diretório base da aplicação
  static const String appDirName = '.microdetect';

  /// Diretório principal
  Directory? _baseDir;

  /// Diretório de configurações
  Directory? _configDir;

  /// Diretório de logs
  Directory? _logsDir;

  /// Diretório de dados
  Directory? _dataDir;

  /// Diretório do backend Python
  Directory? _pythonBackendDir;

  /// Flag para indicar se a inicialização foi concluída
  bool _isInitialized = false;

  /// Inicializa o sistema de diretórios
  Future<void> initialize() async {
    if (_isInitialized) return;

    try {
      LoggerUtil.debug('[AppDirectories] Iniciando inicialização de diretórios');

      // Obter o diretório home do usuário
      final Directory homeDir = await _getHomeDirectory();
      LoggerUtil.debug('[AppDirectories] Diretório home obtido: ${homeDir.path}');

      // Criar diretório base se não existir
      _baseDir = Directory(p.join(homeDir.path, appDirName));

      LoggerUtil.debug('[AppDirectories] Verificando diretório base: ${_baseDir!.path}');
      if (!await _baseDir!.exists()) {
        LoggerUtil.debug('[AppDirectories] Criando diretório base...');
        await _baseDir!.create(recursive: true);
      }
      LoggerUtil.debug('[AppDirectories] Diretório base verificado/criado com sucesso');

      // Criar subdiretórios principais
      LoggerUtil.debug('[AppDirectories] Criando subdiretórios principais...');
      _configDir = await _createSubDirectory('config');
      _logsDir = await _createSubDirectory('logs');
      _dataDir = await _createSubDirectory('data');
      _pythonBackendDir = await _createSubDirectory('python_backend');

      // Criar subdiretórios de dados
      LoggerUtil.debug('[AppDirectories] Criando subdiretórios de dados...');
      await _createSubDirectory('data/datasets');
      await _createSubDirectory('data/models');
      await _createSubDirectory('data/gallery');
      await _createSubDirectory('data/temp');
      await _createSubDirectory('data/annotations');
      await _createSubDirectory('data/training');

      _isInitialized = true;
      LoggerUtil.debug('[AppDirectories] Inicialização concluída com sucesso: ${_baseDir!.path}');
    } catch (e) {
      LoggerUtil.error('[AppDirectories] Erro ao inicializar diretórios: $e');
      rethrow;
    }
  }

  /// Obter o diretório home do usuário
  Future<Directory> _getHomeDirectory() async {
    try {
      if (Platform.isWindows) {
        return Directory(Platform.environment['USERPROFILE']!);
      } else if (Platform.isMacOS || Platform.isLinux) {
        return Directory(Platform.environment['HOME']!);
      } else {
        throw UnsupportedError(
            'Plataforma não suportada. Apenas Windows, MacOS e Linux são suportados.');
      }
    } catch (e) {
      LoggerUtil.error('[AppDirectories] Erro ao obter diretório home: $e');

      // Fallback para o diretório de documentos como último recurso
      final appDocsDir = await getApplicationDocumentsDirectory();
      LoggerUtil.debug('[AppDirectories] Usando diretório de fallback: ${appDocsDir.path}');
      return appDocsDir;
    }
  }

  /// Cria um subdiretório na pasta base
  Future<Directory> _createSubDirectory(String name) async {
    if (_baseDir == null) {
      throw StateError('O diretório base não foi inicializado.');
    }

    try {
      final subdir = p.join(_baseDir!.path, name);
      LoggerUtil.debug('[AppDirectories] Criando subdiretório: $subdir');

      final dir = Directory(subdir);
      if (!await dir.exists()) {
        await dir.create(recursive: true);
      }

      LoggerUtil.debug('[AppDirectories] Subdiretório criado/verificado: $subdir');
      return dir;
    } catch (e) {
      LoggerUtil.error('[AppDirectories] Erro ao criar subdiretório $name: $e');
      rethrow;
    }
  }

  /// Verifica se já foi inicializado, se não, inicializa
  Future<void> ensureInitialized() async {
    if (!_isInitialized) {
      await initialize();
    }
  }

  /// Getters para os diretórios
  Directory get baseDir {
    if (_baseDir == null) {
      throw StateError('Diretório base não foi inicializado. Chame initialize() primeiro.');
    }
    return _baseDir!;
  }

  Directory get configDir {
    if (_configDir == null) {
      throw StateError('Diretório de configuração não foi inicializado. Chame initialize() primeiro.');
    }
    return _configDir!;
  }

  Directory get logsDir {
    if (_logsDir == null) {
      throw StateError('Diretório de logs não foi inicializado. Chame initialize() primeiro.');
    }
    return _logsDir!;
  }

  Directory get dataDir {
    if (_dataDir == null) {
      throw StateError('Diretório de dados não foi inicializado. Chame initialize() primeiro.');
    }
    return _dataDir!;
  }

  Directory get pythonBackendDir {
    if (_pythonBackendDir == null) {
      throw StateError('Diretório do backend Python não foi inicializado. Chame initialize() primeiro.');
    }
    return _pythonBackendDir!;
  }

  /// Caminho para um arquivo de configuração específico
  String getConfigFilePath(String fileName) {
    if (_configDir == null) {
      throw StateError('Diretório de configuração não foi inicializado. Chame initialize() primeiro.');
    }
    return p.join(_configDir!.path, fileName);
  }

  /// Caminho para um diretório de dados específico
  String getDataDirPath(String subDir) {
    if (_dataDir == null) {
      throw StateError('Diretório de dados não foi inicializado. Chame initialize() primeiro.');
    }
    return p.join(_dataDir!.path, subDir);
  }

  /// Verifica a estrutura de diretórios e imprime detalhes (para debugging)
  Future<Map<String, dynamic>> inspectDirectoryStructure() async {
    try {
      await ensureInitialized();

      final result = <String, dynamic>{
        'base_dir': _baseDir?.path ?? 'não inicializado',
        'exists': <String, bool>{},
        'contents': <String, List<String>>{}
      };

      // Verificar quais diretórios existem
      result['exists']['base'] = await _baseDir!.exists();
      result['exists']['config'] = await _configDir!.exists();
      result['exists']['logs'] = await _logsDir!.exists();
      result['exists']['data'] = await _dataDir!.exists();
      result['exists']['python_backend'] = await _pythonBackendDir!.exists();

      // Listar conteúdo dos diretórios
      if (await _baseDir!.exists()) {
        result['contents']['base'] = await _baseDir!.list()
            .map((entity) => p.basename(entity.path))
            .toList();
      }

      if (await _dataDir!.exists()) {
        result['contents']['data'] = await _dataDir!.list()
            .map((entity) => p.basename(entity.path))
            .toList();
      }

      if (await _pythonBackendDir!.exists()) {
        result['contents']['python_backend'] = await _pythonBackendDir!.list()
            .map((entity) => p.basename(entity.path))
            .toList();

        // Verificar script principal
        final mainScriptPath = p.join(_pythonBackendDir!.path, 'start_backend.py');
        result['exists']['main_script'] = await File(mainScriptPath).exists();
      }

      // Imprimir o relatório para debug
      LoggerUtil.debug('[AppDirectories] Relatório de diretórios:');
      LoggerUtil.debug('[AppDirectories] - Base: ${result['base_dir']} (exists: ${result['exists']['base']})');
      LoggerUtil.debug('[AppDirectories] - Config: ${_configDir?.path} (exists: ${result['exists']['config']})');
      LoggerUtil.debug('[AppDirectories] - Logs: ${_logsDir?.path} (exists: ${result['exists']['logs']})');
      LoggerUtil.debug('[AppDirectories] - Data: ${_dataDir?.path} (exists: ${result['exists']['data']})');
      LoggerUtil.debug('[AppDirectories] - Python Backend: ${_pythonBackendDir?.path} (exists: ${result['exists']['python_backend']})');

      if (result['contents'].containsKey('base')) {
        LoggerUtil.debug('[AppDirectories] - Conteúdo Base: ${result['contents']['base'].join(', ')}');
      }

      if (result['contents'].containsKey('data')) {
        LoggerUtil.debug('[AppDirectories] - Conteúdo Data: ${result['contents']['data'].join(', ')}');
      }

      if (result['contents'].containsKey('python_backend')) {
        LoggerUtil.debug('[AppDirectories] - Conteúdo Python Backend: ${result['contents']['python_backend'].join(', ')}');
      }

      return result;
    } catch (e) {
      LoggerUtil.error('[AppDirectories] Erro ao inspecionar diretórios: $e');
      return {'error': e.toString()};
    }
  }
}