import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:get/get.dart';
import 'package:path/path.dart' as path;
import '../utils/logger_util.dart';
import '../../config/app_directories.dart';

/// Serviço para corrigir problemas na estrutura de diretórios do backend Python
class BackendFixService extends GetxService {
  /// Instância singleton do serviço
  static BackendFixService get to => Get.find<BackendFixService>();

  /// Verificar se é necessário corrigir a estrutura de diretórios aninhados
  Future<bool> needsStructureFix(String backendPath) async {
    try {
      // Verificar se há um diretório python_backend dentro do python_backend
      final nestedPath = path.join(backendPath, 'python_backend');
      final nestedDir = Directory(nestedPath);

      if (await nestedDir.exists()) {
        // Verificar se o diretório aninhado contém o start_backend.py
        final mainScript = File(path.join(nestedPath, 'start_backend.py'));
        if (await mainScript.exists()) {
          LoggerUtil.warning('Estrutura de diretórios aninhados detectada, necessita correção');
          return true;
        }
      }

      // Verificar se há arquivos essenciais no diretório raiz do backend
      final mainScript = File(path.join(backendPath, 'start_backend.py'));
      if (!await mainScript.exists()) {
        // Se não há script principal no diretório raiz, verificar subdiretórios
        final subdirs = await Directory(backendPath).list().toList();
        for (var entity in subdirs) {
          if (entity is Directory) {
            final subDirScript = File(path.join(entity.path, 'start_backend.py'));
            if (await subDirScript.exists()) {
              LoggerUtil.warning('Script principal encontrado em subdiretório ${path.basename(entity.path)}, necessita correção');
              return true;
            }
          }
        }
      }

      // Verificar se a pasta venv está dentro do python_backend e não fora
      final venvDirOutside = Directory(path.join(path.dirname(backendPath), 'venv'));
      if (await venvDirOutside.exists()) {
        LoggerUtil.warning('Ambiente virtual fora do diretório backend, necessita correção');
        return true;
      }

      // Verificar se há pasta de dados dentro do python_backend que deveria estar fora
      final dataInsideBackend = Directory(path.join(backendPath, 'data'));
      if (await dataInsideBackend.exists()) {
        // A pasta data deve estar no diretório .microdetect, não dentro de python_backend
        LoggerUtil.warning('Diretório de dados dentro do backend, necessita correção');
        return true;
      }

      LoggerUtil.debug('Estrutura de diretórios parece correta');
      return false;
    } catch (e) {
      LoggerUtil.error('Erro ao verificar estrutura de diretórios', e);
      return false;
    }
  }

  /// Corrige a estrutura de diretórios aninhados, movendo arquivos para o nível correto
  Future<bool> fixNestedDirectoryStructure(String backendPath) async {
    try {
      LoggerUtil.info('Corrigindo estrutura de diretórios...');

      // Verificar se há um diretório python_backend dentro do python_backend
      final nestedPath = path.join(backendPath, 'python_backend');
      final nestedDir = Directory(nestedPath);

      // Caminho para o diretório de dados correto (fora do backend)
      final dataDir = AppDirectories.instance.dataDir.path;

      // 1. Verificar diretório aninhado
      if (await nestedDir.exists()) {
        final mainScript = File(path.join(nestedPath, 'start_backend.py'));
        if (await mainScript.exists()) {
          LoggerUtil.info('Movendo arquivos do diretório aninhado para o nível superior...');

          // Mover todos os arquivos e diretórios para o nível superior
          await for (final entity in nestedDir.list()) {
            final baseName = path.basename(entity.path);

            // Pular a pasta data - ela deve ir para o local correto separado
            if (baseName == 'data') continue;

            final targetPath = path.join(backendPath, baseName);

            if (entity is File) {
              // Copiar o arquivo para o nível superior
              await entity.copy(targetPath);
            } else if (entity is Directory) {
              // Copiar o diretório para o nível superior
              await _copyDirectory(entity, Directory(targetPath));
            }
          }

          // Remover o diretório aninhado após mover tudo
          await nestedDir.delete(recursive: true);
        }
      }

      // 2. Verificar ambiente virtual externo e mover para o lugar correto
      final venvDirOutside = Directory(path.join(path.dirname(backendPath), 'venv'));
      final venvDirInside = Directory(path.join(backendPath, 'venv'));

      if (await venvDirOutside.exists() && !await venvDirInside.exists()) {
        LoggerUtil.info('Movendo ambiente virtual para dentro do diretório backend...');

        // Criar o diretório venv dentro do backend e mover conteúdo
        await venvDirInside.create(recursive: true);
        await _copyDirectory(venvDirOutside, venvDirInside);

        // Apagar o venv externo
        await venvDirOutside.delete(recursive: true);
      }

      // 3. Verificar pasta data dentro do backend e mover para o lugar correto fora
      final dataInsideBackend = Directory(path.join(backendPath, 'data'));
      if (await dataInsideBackend.exists()) {
        LoggerUtil.info('Movendo diretório de dados para localização correta...');

        // Garantir que o diretório de dados externo existe
        await Directory(dataDir).create(recursive: true);

        // Copiar conteúdo do diretório de dados para o lugar correto
        await for (final entity in dataInsideBackend.list()) {
          final baseName = path.basename(entity.path);
          final targetPath = path.join(dataDir, baseName);

          if (entity is File) {
            await entity.copy(targetPath);
          } else if (entity is Directory) {
            await _copyDirectory(entity, Directory(targetPath));
          }
        }

        // Remover o diretório data de dentro do backend
        await dataInsideBackend.delete(recursive: true);
      }

      LoggerUtil.info('Estrutura de diretórios corrigida com sucesso');
      return true;
    } catch (e) {
      LoggerUtil.error('Erro ao corrigir estrutura de diretórios', e);
      return false;
    }
  }

  /// Copia um diretório e seu conteúdo para outro local
  Future<void> _copyDirectory(Directory source, Directory dest) async {
    await dest.create(recursive: true);

    await for (final entity in source.list(recursive: false)) {
      final targetPath = path.join(dest.path, path.basename(entity.path));

      if (entity is Directory) {
        await _copyDirectory(entity, Directory(targetPath));
      } else if (entity is File) {
        await entity.copy(targetPath);
      }
    }
  }
}