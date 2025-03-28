import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:get/get.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../design_system/app_toast.dart';
import '../../config/app_directories.dart';

/// Modelo de entrada de log para persistência
class LogEntry {
  final String level;
  final String message;
  final String? details;
  final DateTime timestamp;

  LogEntry({
    required this.level,
    required this.message,
    this.details,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  Map<String, dynamic> toJson() => {
    'level': level,
    'message': message,
    'details': details,
    'timestamp': timestamp.toIso8601String(),
  };

  factory LogEntry.fromJson(Map<String, dynamic> json) => LogEntry(
    level: json['level'],
    message: json['message'],
    details: json['details'],
    timestamp: DateTime.parse(json['timestamp']),
  );
}

/// Utilitário para logging consistente em toda a aplicação, com suporte a persistência
class LoggerUtil {
  // Configurações de logs
  static bool enableDebugLogs = true;
  static bool enableInfoLogs = true;
  static bool enableWarningLogs = true;
  static bool enableErrorLogs = true;
  
  // Configuração de persistência
  static bool enableLogPersistence = false;
  static const int maxFileLogEntries = 10000; // Limite de entradas no arquivo
  static const int maxSharedPrefsEntries = 100; // Limite de entradas no SharedPreferences
  
  // Caminhos e chaves
  static const String _sharedPrefsKey = 'app_logs';
  static String? _logFilePath;
  static bool _initialized = false;
  
  // Cache de logs recentes (para não precisar ler arquivo/prefs a cada vez)
  static final List<LogEntry> _recentLogs = [];
  
  /// Inicializa o sistema de logs
  static Future<void> initialize() async {
    if (_initialized) return;
    
    try {
      if (enableLogPersistence) {
        // Configurar diretório de logs
        await AppDirectories.instance.ensureInitialized();
        final logsDir = Directory('${AppDirectories.instance.baseDir.path}/logs');
        if (!await logsDir.exists()) {
          await logsDir.create(recursive: true);
        }
        
        // Configurar arquivo de log
        final timestamp = DateTime.now().toIso8601String().replaceAll(':', '-');
        _logFilePath = '${logsDir.path}/app_log_$timestamp.json';
        
        debug('Sistema de logs inicializado: $_logFilePath');
      }
      
      _initialized = true;
    } catch (e) {
      debugPrint('❌ Erro ao inicializar sistema de logs: $e');
    }
  }
  
  /// Ativa ou desativa a persistência de logs
  static Future<void> setEnabled(bool enabled) async {
    final bool oldValue = enableLogPersistence;
    enableLogPersistence = enabled;
    
    if (enabled && !oldValue) {
      // Se estamos ativando a persistência, inicialize o sistema
      await initialize();
      info('Sistema de logs persistentes ativado');
    } else if (!enabled && oldValue) {
      info('Sistema de logs persistentes desativado');
    }
  }
  
  /// Define quais níveis de log estão habilitados
  static void setLogLevels({
    bool? debug,
    bool? info,
    bool? warning,
    bool? error,
  }) {
    if (debug != null) enableDebugLogs = debug;
    if (info != null) enableInfoLogs = info;
    if (warning != null) enableWarningLogs = warning;
    if (error != null) enableErrorLogs = error;
  }
  
  /// Log de nível DEBUG (apenas visível em modo debug)
  static void debug(String message) {
    if (kDebugMode && enableDebugLogs) {
      debugPrint('🔍 DEBUG: $message');
    }
    
    // Persistir se habilitado
    if (enableLogPersistence && enableDebugLogs) {
      _persistLogEntry(LogEntry(
        level: 'DEBUG',
        message: message,
      ));
    }
  }
  
  /// Log de nível INFO
  static void info(String message) {
    if (enableInfoLogs) {
      debugPrint('ℹ️ INFO: $message');
      
      // Mostrar toast somente em modo debug
      if (kDebugMode) {
        AppToast.info('Informação', description: message);
      }
      
      // Persistir se habilitado
      if (enableLogPersistence) {
        _persistLogEntry(LogEntry(
          level: 'INFO',
          message: message,
        ));
      }
    }
  }
  
  /// Log de nível WARNING
  static void warning(String message) {
    if (enableWarningLogs) {
      debugPrint('⚠️ AVISO: $message');
      
      // Mostrar toast somente em modo debug
      if (kDebugMode) {
        AppToast.warning('Aviso', description: message);
      }
      
      // Persistir se habilitado
      if (enableLogPersistence) {
        _persistLogEntry(LogEntry(
          level: 'WARNING',
          message: message,
        ));
      }
    }
  }
  
  /// Log de nível ERROR
  static void error(String message, [dynamic exception]) {
    if (enableErrorLogs) {
      final errorMsg = exception != null ? '$message\nErro: $exception' : message;
      debugPrint('🔴 ERRO: $errorMsg');
      
      // Mostrar toast somente em modo debug
      if (kDebugMode) {
        final description = exception != null ? 'Erro: $exception' : null;
        AppToast.error(message, description: description);
      }
      
      // Persistir se habilitado
      if (enableLogPersistence) {
        _persistLogEntry(LogEntry(
          level: 'ERROR',
          message: message,
          details: exception?.toString(),
        ));
      }
    }
  }
  
  /// Persiste uma entrada de log
  static Future<void> _persistLogEntry(LogEntry entry) async {
    if (!enableLogPersistence) return;
    
    try {
      await initialize();
      
      // Adicionar ao cache de logs recentes
      _recentLogs.add(entry);
      if (_recentLogs.length > maxSharedPrefsEntries) {
        _recentLogs.removeAt(0);
      }
      
      // Persistir em SharedPreferences (logs mais recentes)
      _saveToSharedPreferences();
      
      // Persistir em arquivo (histórico completo)
      _saveToFile(entry);
    } catch (e) {
      debugPrint('❌ Erro ao persistir log: $e');
    }
  }
  
  /// Salva logs no SharedPreferences
  static Future<void> _saveToSharedPreferences() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final recentLogsJson = _recentLogs.map((e) => jsonEncode(e.toJson())).toList();
      await prefs.setStringList(_sharedPrefsKey, recentLogsJson);
    } catch (e) {
      debugPrint('❌ Erro ao salvar logs no SharedPreferences: $e');
    }
  }
  
  /// Salva log em arquivo
  static Future<void> _saveToFile(LogEntry entry) async {
    if (_logFilePath == null) return;
    
    try {
      final file = File(_logFilePath!);
      final bool fileExists = await file.exists();
      
      if (!fileExists) {
        // Criar novo arquivo com array vazio
        await file.writeAsString('[]');
      }
      
      // Ler conteúdo atual
      String content = await file.readAsString();
      List<dynamic> logs = [];
      
      try {
        logs = jsonDecode(content);
      } catch (e) {
        // Se o arquivo estiver corrompido, iniciar novo
        logs = [];
      }
      
      // Adicionar nova entrada e limitar tamanho
      logs.add(entry.toJson());
      if (logs.length > maxFileLogEntries) {
        logs = logs.sublist(logs.length - maxFileLogEntries);
      }
      
      // Salvar de volta no arquivo
      await file.writeAsString(jsonEncode(logs));
    } catch (e) {
      debugPrint('❌ Erro ao salvar log em arquivo: $e');
    }
  }
  
  /// Obtém os logs recentes
  static Future<List<LogEntry>> getRecentLogs() async {
    if (_recentLogs.isNotEmpty) {
      return List.from(_recentLogs);
    }
    
    try {
      final prefs = await SharedPreferences.getInstance();
      final logsJson = prefs.getStringList(_sharedPrefsKey) ?? [];
      
      return logsJson
          .map((e) => LogEntry.fromJson(jsonDecode(e)))
          .toList();
    } catch (e) {
      debugPrint('❌ Erro ao obter logs recentes: $e');
      return [];
    }
  }
  
  /// Obtém logs completos do arquivo
  static Future<List<LogEntry>> getAllLogs() async {
    if (_logFilePath == null) return [];
    
    try {
      final file = File(_logFilePath!);
      if (!await file.exists()) {
        return [];
      }
      
      final content = await file.readAsString();
      final List<dynamic> logsJson = jsonDecode(content);
      
      return logsJson
          .map((e) => LogEntry.fromJson(e))
          .toList();
    } catch (e) {
      debugPrint('❌ Erro ao obter todos os logs: $e');
      return [];
    }
  }
  
  /// Exporta logs para um arquivo específico
  static Future<String?> exportLogs(String exportPath) async {
    try {
      final logs = await getAllLogs();
      if (logs.isEmpty) {
        return null;
      }
      
      // Formatar logs para exportação
      final formattedLogs = logs.map((log) => 
        '${log.timestamp} [${log.level}] ${log.message}${log.details != null ? ' - Detalhes: ${log.details}' : ''}'
      ).join('\n');
      
      // Salvar no arquivo de exportação
      final file = File(exportPath);
      await file.writeAsString(formattedLogs);
      
      return exportPath;
    } catch (e) {
      debugPrint('❌ Erro ao exportar logs: $e');
      return null;
    }
  }
  
  /// Limpa todos os logs
  static Future<void> clearLogs() async {
    try {
      // Limpar cache
      _recentLogs.clear();
      
      // Limpar SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_sharedPrefsKey);
      
      // Limpar arquivo
      if (_logFilePath != null) {
        final file = File(_logFilePath!);
        if (await file.exists()) {
          await file.writeAsString('[]');
        }
      }
      
      debug('Todos os logs foram limpos');
    } catch (e) {
      debugPrint('❌ Erro ao limpar logs: $e');
    }
  }
} 