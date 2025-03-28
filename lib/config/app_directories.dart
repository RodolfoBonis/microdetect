import 'dart:io';
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

  /// Flag para indicar se a inicialização foi concluída
  bool _isInitialized = false;

  /// Inicializa o sistema de diretórios
  Future<void> initialize() async {
    if (_isInitialized) return;
    
    try {
      // Obter o diretório home do usuário
      final Directory homeDir = await _getHomeDirectory();

      // Criar diretório base se não existir
      _baseDir = Directory(p.join(homeDir.path, appDirName));
      if (!await _baseDir!.exists()) {
        await _baseDir!.create(recursive: true);
      }

      // Criar subdiretórios
      _configDir = await _createSubDirectory('config');

      _isInitialized = true;
      print('Diretório base inicializado: ${_baseDir!.path}');
    } catch (e) {
      print('Erro ao inicializar diretórios: $e');
      rethrow;
    }
  }

  /// Obter o diretório home do usuário
  Future<Directory> _getHomeDirectory() async {
    if (Platform.isWindows) {
      return Directory(Platform.environment['USERPROFILE']!);
    } else if (Platform.isMacOS || Platform.isLinux) {
      return Directory(Platform.environment['HOME']!);
    } else {
      throw UnsupportedError(
          'Plataforma não suportada. Apenas Windows, MacOS e Linux são suportados.');
    }
  }

  /// Cria um subdiretório na pasta base
  Future<Directory> _createSubDirectory(String name) async {
    if (_baseDir == null) {
      throw StateError('O diretório base não foi inicializado.');
    }
    
    final dir = Directory(p.join(_baseDir!.path, name));
    if (!await dir.exists()) {
      await dir.create(recursive: true);
    }
    return dir;
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

  /// Caminho para um arquivo de configuração específico
  String getConfigFilePath(String fileName) {
    if (_configDir == null) {
      throw StateError('Diretório de configuração não foi inicializado. Chame initialize() primeiro.');
    }
    return p.join(_configDir!.path, fileName);
  }
}
