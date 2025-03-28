import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:get/get.dart';
import 'package:path/path.dart' as path;
import '../utils/logger_util.dart';

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
      LoggerUtil.info('Corrigindo estrutura de diretórios aninhados...');
      
      // Verificar se há um diretório python_backend dentro do python_backend
      final nestedPath = path.join(backendPath, 'python_backend');
      final nestedDir = Directory(nestedPath);
      
      if (!await nestedDir.exists()) {
        LoggerUtil.debug('Nenhum diretório aninhado encontrado, nada a corrigir');
        return true;
      }
      
      // Verificar se o diretório aninhado contém o start_backend.py
      final mainScript = File(path.join(nestedPath, 'start_backend.py'));
      if (!await mainScript.exists()) {
        LoggerUtil.debug('O diretório aninhado não contém start_backend.py, nada a corrigir');
        return true;
      }
      
      LoggerUtil.info('Movendo arquivos do diretório aninhado para o nível superior...');
      
      // Mover todos os arquivos e diretórios para o nível superior
      await for (final entity in nestedDir.list()) {
        final baseName = path.basename(entity.path);
        final targetPath = path.join(backendPath, baseName);
        
        LoggerUtil.debug('Movendo ${entity.path} para $targetPath');
        
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