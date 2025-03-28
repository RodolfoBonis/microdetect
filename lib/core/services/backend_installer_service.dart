import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import 'package:path/path.dart' as path;
import 'package:archive/archive.dart';
import 'package:path_provider/path_provider.dart';
import 'python_service.dart';
import '../../config/app_directories.dart';
import '../../config/app_assets.dart';
import '../utils/logger_util.dart';
import 'package:flutter/foundation.dart';

class BackendInstallerService extends GetxService {
  // Observable state
  final isInstalling = false.obs;
  final installProgress = 0.0.obs;
  final currentVersion = '1.0.0'.obs;
  final assetVersion = '1.0.0'.obs;
  
  // Singleton para acessar
  static BackendInstallerService get to => Get.find<BackendInstallerService>();
  
  // Diretório onde o backend Python será instalado
  Future<String> get backendPath async {
    // Garantir que o diretório base está inicializado
    await AppDirectories.instance.ensureInitialized();
    
    // Usar o diretório .microdetect da aplicação
    final baseDir = AppDirectories.instance.baseDir;
    final pythonBackendDir = path.join(baseDir.path, 'python_backend');
    
    // Verificar se o diretório existe e criar se necessário
    final dir = Directory(pythonBackendDir);
    if (!await dir.exists()) {
      await dir.create(recursive: true);
    }
    
    return pythonBackendDir;
  }
  
  // Verifica se o backend já está instalado
  Future<bool> isInstalled() async {
    final backend = await backendPath;
    final mainScript = path.join(backend, 'start_backend.py');
    return File(mainScript).exists();
  }
  
  // Obter a versão atual do backend instalado
  Future<String> getCurrentVersion() async {
    try {
      LoggerUtil.debug('Buscando versão atual do backend...');

      // Verifica se o backend está instalado
      final bool installed = await isInstalled();
      if (!installed) {
        currentVersion.value = 'Não instalado';
        LoggerUtil.debug('Backend não está instalado');
        return currentVersion.value;
      }

      // Caminho para o arquivo de versão
      final String versionFilePath = path.join(await backendPath, 'version.txt');
      final File versionFile = File(versionFilePath);

      // Verifica se o arquivo de versão existe
      if (!versionFile.existsSync()) {
        currentVersion.value = 'Desconhecida';
        LoggerUtil.warning('Arquivo de versão não encontrado: $versionFilePath');
        return currentVersion.value;
      }

      // Lê a versão do arquivo e remove espaços em branco
      final String version = await versionFile.readAsString();
      currentVersion.value = version.trim();
      
      LoggerUtil.debug('Versão atual do backend: ${currentVersion.value}');
      return currentVersion.value;
    } catch (e) {
      LoggerUtil.error('Erro ao obter versão atual do backend: $e');
      currentVersion.value = 'Erro: $e';
      return currentVersion.value;
    }
  }
  
  // Verificar se há uma atualização disponível
  Future<bool> isUpdateAvailable() async {
    try {
      LoggerUtil.debug('Verificando se há atualização disponível...');
      
      // Obter versões atual e dos assets (forçar atualização dos valores)
      final String current = await getCurrentVersion();
      final String asset = await getAssetVersion();
      
      // Se houver erro ou versão desconhecida
      if (current.startsWith('Erro:') || 
          current == 'Desconhecida' || 
          current == 'Não instalado' ||
          asset.startsWith('Erro:') || 
          asset == 'Desconhecida') {
        LoggerUtil.warning('Não foi possível comparar versões: atual=$current, asset=$asset');
        return false;
      }
      
      // Comparar as versões (trimming para garantir)
      final bool updateAvailable = current.trim() != asset.trim();
      
      LoggerUtil.info('Verificação de atualização: atual=$current, disponível=$asset, atualização=${updateAvailable ? "disponível" : "não necessária"}');
      return updateAvailable;
    } catch (e) {
      LoggerUtil.error('Erro ao verificar atualização disponível: $e');
      return false;
    }
  }
  
  // Obter a versão disponível nos assets
  Future<String> getAssetVersion() async {
    try {
      LoggerUtil.debug('Buscando versão do backend nos assets...');
      
      // Caminho para o asset ZIP
      final String backendZipPath = AppAssets.pythonBackendZip;

      try {
        // Carregar do asset bundle
        final ByteData data = await rootBundle.load(backendZipPath);
        final List<int> bytes = data.buffer.asUint8List();
        
        // Criar arquivo temporário para extrair o version.txt
        final tempDir = await getTemporaryDirectory();
        final tempPath = path.join(tempDir.path, 'temp_backend_extract');
        
        try {
          // Garantir que o diretório temporário existe
          Directory(tempPath).createSync(recursive: true);
          
          // Descompactar o ZIP
          final archive = ZipDecoder().decodeBytes(bytes);
          
          // Procurar pelo arquivo version.txt
          for (final file in archive) {
            if (path.basename(file.name) == 'version.txt') {
              // Extrair o arquivo
              if (file.isFile) {
                final data = file.content as List<int>;
                final String version = utf8.decode(data).trim();
                assetVersion.value = version;
                LoggerUtil.debug('Versão do backend nos assets: $version');
                return version;
              }
            }
          }
          
          // Se não encontrar o arquivo version.txt
          LoggerUtil.warning('Arquivo version.txt não encontrado no ZIP do asset');
          assetVersion.value = 'Desconhecida';
          return assetVersion.value;
        } finally {
          // Limpar os arquivos temporários
          try {
            if (Directory(tempPath).existsSync()) {
              Directory(tempPath).deleteSync(recursive: true);
            }
          } catch (e) {
            LoggerUtil.warning('Falha ao limpar arquivos temporários: $e');
          }
        }
      } catch (loadError) {
        if (loadError is FlutterError || loadError.toString().contains('Unable to load asset')) {
          LoggerUtil.error('Arquivo de asset não encontrado: $backendZipPath. Erro: $loadError');
          assetVersion.value = 'Arquivo não encontrado nos assets';
          return assetVersion.value;
        } else {
          rethrow; // Repassar outros tipos de erro
        }
      }
    } catch (e) {
      LoggerUtil.error('Erro ao obter versão do backend nos assets: $e');
      assetVersion.value = 'Erro: $e';
      return assetVersion.value;
    }
  }
  
  // Instala o backend Python a partir dos assets
  Future<bool> install() async {
    if (isInstalling.value) return false;
    
    try {
      isInstalling.value = true;
      installProgress.value = 0.0;
      
      // Verificar se já está instalado
      if (await isInstalled()) {
        // Se já instalado, verificar se há atualizações disponíveis
        final updateAvailable = await isUpdateAvailable();
        if (updateAvailable) {
          LoggerUtil.info('Atualização disponível. Atualizando backend...');
          final result = await update();
          isInstalling.value = false;
          return result;
        }
        
        LoggerUtil.info('Backend já está instalado e atualizado');
        isInstalling.value = false;
        return true;
      }
      
      LoggerUtil.info('Instalando backend Python...');
      installProgress.value = 0.1;
      
      // Obter diretório de instalação
      final backendDir = await backendPath;
      final dir = Directory(backendDir);
      
      // Criar diretório se não existir
      if (!await dir.exists()) {
        await dir.create(recursive: true);
      }
      
      installProgress.value = 0.2;
      
      // Tentar carregar o arquivo ZIP do backend dos assets
      final ByteData data;
      try {
        data = await rootBundle.load(AppAssets.pythonBackendZip);
      } catch (e) {
        LoggerUtil.error('Erro ao carregar arquivo ZIP do backend: $e');
        LoggerUtil.error('O arquivo python_backend.zip deve estar incluído nos assets do projeto');
        LoggerUtil.error('Verifique se ele está corretamente referenciado no pubspec.yaml');
        isInstalling.value = false;
        return false;
      }
      
      installProgress.value = 0.4;
      final List<int> bytes = data.buffer.asUint8List();
      
      // Decodificar o arquivo ZIP
      final archive = ZipDecoder().decodeBytes(bytes);
      
      installProgress.value = 0.6;
      
      // Calcular o total de arquivos para extração
      final totalFiles = archive.files.length;
      int filesProcessed = 0;
      
      // Extrair os arquivos para o diretório de destino
      for (final file in archive) {
        final filename = file.name;
        
        if (file.isFile) {
          final data = file.content as List<int>;
          final filePath = path.join(backendDir, filename);
          
          // Criar diretórios pai se necessário
          await Directory(path.dirname(filePath)).create(recursive: true);
          
          // Escrever arquivo
          final outFile = File(filePath);
          await outFile.writeAsBytes(data);
          
          // Tornar executável em sistemas Unix
          if (Platform.isLinux || Platform.isMacOS) {
            if (filename.endsWith('.py') || filename == 'python' || filename.startsWith('bin/')) {
              try {
                await Process.run('chmod', ['+x', filePath]);
              } catch (e) {
                LoggerUtil.warning('Erro ao tornar arquivo executável: $e');
              }
            }
          }
        } else {
          // Criar diretório
          final dirPath = path.join(backendDir, filename);
          await Directory(dirPath).create(recursive: true);
        }
        
        // Atualizar o progresso
        filesProcessed++;
        installProgress.value = 0.6 + (0.3 * filesProcessed / totalFiles);
      }
      
      // Tentar criar ambiente virtual Python
      final pythonService = Get.find<PythonService>();
      final venvCreated = await pythonService.createVirtualEnvIfNeeded();
      if (!venvCreated) {
        LoggerUtil.warning('Não foi possível criar ambiente virtual Python. ' +
                   'O aplicativo tentará usar o Python do sistema.');
      }
      
      installProgress.value = 1.0;
      LoggerUtil.info('Backend Python instalado com sucesso');
      isInstalling.value = false;
      return true;
    } catch (e) {
      LoggerUtil.error('Erro ao instalar backend', e);
      isInstalling.value = false;
      return false;
    }
  }
  
  // Atualiza o backend Python para uma nova versão
  Future<bool> update() async {
    if (isInstalling.value) return false;
    
    try {
      isInstalling.value = true;
      installProgress.value = 0.0;
      
      LoggerUtil.info('Atualizando backend Python...');
      
      // Remover instalação existente
      final backendDir = await backendPath;
      final dir = Directory(backendDir);
      
      if (await dir.exists()) {
        await dir.delete(recursive: true);
      }
      
      // Reinstalar
      final result = await install();
      isInstalling.value = false;
      return result;
    } catch (e) {
      LoggerUtil.error('Erro ao atualizar backend', e);
      isInstalling.value = false;
      return false;
    }
  }

  // Cria as pastas de dados necessárias
  Future<bool> setupDataDirectories() async {
    try {
      final backendDir = await backendPath;

      // Criar diretórios de dados
      final dataDirs = [
        'data',
        'data/datasets',
        'data/models',
        'data/gallery',
        'data/temp',
        'data/annotations',
        'data/training'
      ];

      for (final dirName in dataDirs) {
        final dir = Directory(path.join(backendDir, dirName));
        await dir.create(recursive: true);
      }

      LoggerUtil.debug('Diretórios de dados configurados com sucesso');
      return true;
    } catch (e) {
      LoggerUtil.error('Erro ao criar diretórios de dados', e);
      return false;
    }
  }
  
  // Desinstalar o backend Python
  Future<bool> uninstall() async {
    try {
      final backendDir = await backendPath;
      final dir = Directory(backendDir);
      
      if (await dir.exists()) {
        await dir.delete(recursive: true);
      }
      
      LoggerUtil.info('Backend Python desinstalado com sucesso');
      return true;
    } catch (e) {
      LoggerUtil.error('Erro ao desinstalar backend', e);
      return false;
    }
  }
  
  // Método para atualizar manualmente o backend Python a partir de um diretório fonte
  Future<bool> updateFromSource(String sourceDirPath) async {
    if (isInstalling.value) return false;
    
    try {
      isInstalling.value = true;
      installProgress.value = 0.0;
      
      // Verificar se o caminho de origem existe e contém files
      final sourceDir = Directory(sourceDirPath);
      if (!await sourceDir.exists()) {
        LoggerUtil.error('Diretório fonte não encontrado: $sourceDirPath');
        isInstalling.value = false;
        return false;
      }
      
      // Verificar se contém start_backend.py
      final startScript = File(path.join(sourceDir.path, 'start_backend.py'));
      if (!await startScript.exists()) {
        LoggerUtil.error('Diretório fonte não contém start_backend.py');
        isInstalling.value = false;
        return false;
      }
      
      final backendDir = await backendPath;
      final backendDirObj = Directory(backendDir);
      
      // Apagar diretório destino se existir
      if (await backendDirObj.exists()) {
        LoggerUtil.info('Limpando diretório de instalação anterior');
        await backendDirObj.delete(recursive: true);
        await backendDirObj.create(recursive: true);
      }
      
      // Copiar arquivos recursivamente
      LoggerUtil.info('Copiando arquivos do backend...');
      await _copyFiles(sourceDir.path, backendDir);
      
      LoggerUtil.info('Backend atualizado manualmente com sucesso');
      isInstalling.value = false;
      return true;
    } catch (e) {
      LoggerUtil.error('Erro ao atualizar manualmente o backend: $e');
      isInstalling.value = false;
      return false;
    }
  }
  
  // Método auxiliar para copiar arquivos recursivamente
  Future<void> _copyFiles(String sourcePath, String destPath) async {
    try {
      final sourceDir = Directory(sourcePath);
      final destDir = Directory(destPath);
      
      // Criar diretório destino se não existir
      if (!await destDir.exists()) {
        await destDir.create(recursive: true);
      }
      
      // Listar todos os arquivos e diretórios na origem
      final entities = await sourceDir.list(recursive: false).toList();
      
      // Copiar cada entidade
      for (var entity in entities) {
        final String name = path.basename(entity.path);
        final String newPath = path.join(destPath, name);
        
        if (entity is File) {
          // Copiar arquivo
          await entity.copy(newPath);
          
          // Dar permissão de execução para arquivos Python em sistemas Unix
          if ((Platform.isLinux || Platform.isMacOS) && 
              (newPath.endsWith('.py') || name == 'python')) {
            try {
              await Process.run('chmod', ['+x', newPath]);
            } catch (e) {
              LoggerUtil.warning('Não foi possível definir permissão de execução: $e');
            }
          }
        } else if (entity is Directory) {
          // Copiar diretório recursivamente
          await _copyFiles(entity.path, newPath);
        }
      }
    } catch (e) {
      LoggerUtil.error('Erro ao copiar arquivos: $e');
      rethrow;
    }
  }
  
  // Verifica detalhadamente o status da instalação
  Future<Map<String, dynamic>> checkInstallationStatus() async {
    try {
      final Map<String, dynamic> status = {
        'isInstalled': false,
        'details': <String, dynamic>{},
        'issues': <String>[],
      };
      
      // 1. Verifica se o diretório base existe
      final backendDir = await backendPath;
      final backendDirExists = await Directory(backendDir).exists();
      status['details']['backendDirExists'] = backendDirExists;
      
      if (!backendDirExists) {
        status['issues'].add('Diretório do backend não existe');
        return status;
      }
      
      // 2. Verifica se o script principal existe
      final mainScript = path.join(backendDir, 'start_backend.py');
      final mainScriptExists = await File(mainScript).exists();
      status['details']['mainScriptExists'] = mainScriptExists;
      
      if (!mainScriptExists) {
        status['issues'].add('Script principal (start_backend.py) não encontrado');
      }
      
      // 3. Verifica se o diretório do app existe
      final appDir = path.join(backendDir, 'app');
      final appDirExists = await Directory(appDir).exists();
      status['details']['appDirExists'] = appDirExists;
      
      if (!appDirExists) {
        status['issues'].add('Diretório app/ não encontrado');
      }
      
      // 4. Verifica se o arquivo requirements.txt existe
      final reqFile = path.join(backendDir, 'requirements.txt');
      final reqFileExists = await File(reqFile).exists();
      status['details']['requirementsExists'] = reqFileExists;
      
      if (!reqFileExists) {
        status['issues'].add('Arquivo requirements.txt não encontrado');
      }
      
      // 5. Verifica se o ambiente virtual existe
      final venvDir = path.join(backendDir, 'venv');
      final venvDirExists = await Directory(venvDir).exists();
      status['details']['venvExists'] = venvDirExists;
      
      if (!venvDirExists) {
        status['issues'].add('Ambiente virtual não encontrado');
      }
      
      // 6. Verifica se a pasta data existe
      final dataDir = path.join(backendDir, 'data');
      final dataDirExists = await Directory(dataDir).exists();
      status['details']['dataDirExists'] = dataDirExists;
      
      if (!dataDirExists) {
        status['issues'].add('Diretório de dados não encontrado');
      }
      
      // Status final da instalação
      status['isInstalled'] = mainScriptExists && appDirExists;
      
      return status;
    } catch (e) {
      LoggerUtil.error('Erro ao verificar status de instalação', e);
      return {
        'isInstalled': false,
        'details': {},
        'issues': ['Erro ao verificar status: $e'],
      };
    }
  }
} 