// lib/core/services/port_checker_service.dart
import 'dart:io';
import 'package:get/get.dart';
import '../utils/logger_util.dart';

/// Serviço para verificar e liberar portas em uso
class PortCheckerService extends GetxService {
  // Singleton accessor
  static PortCheckerService get to => Get.find<PortCheckerService>();

  /// Verifica se a porta está em uso e mata o processo que a está utilizando
  Future<bool> checkAndKillProcessOnPort(int port) async {
    try {
      if (Platform.isWindows) {
        return await _checkAndKillProcessWindows(port);
      } else if (Platform.isMacOS || Platform.isLinux) {
        return await _checkAndKillProcessUnix(port);
      } else {
        // Plataforma não suportada
        LoggerUtil.warning('Check port in use not supported on this platform');
        return false;
      }
    } catch (e) {
      LoggerUtil.error('Error checking port in use', e);
      return false;
    }
  }

  /// Verifica se a porta está em uso no Windows e mata o processo
  Future<bool> _checkAndKillProcessWindows(int port) async {
    try {
      // Usar netstat para listar processos que estão usando a porta
      final netstatResult = await Process.run(
          'netstat',
          ['-ano', '|', 'findstr', ':$port'],
          runInShell: true
      );

      if (netstatResult.exitCode != 0 || (netstatResult.stdout as String).isEmpty) {
        // Porta não está em uso
        return true;
      }

      LoggerUtil.info('Port $port is in use on Windows. Trying to kill process.');

      // Analisar saída do netstat para extrair PID
      final lines = (netstatResult.stdout as String).split('\n');
      for (var line in lines) {
        if (line.contains(':$port')) {
          // Extrair o PID (geralmente o último campo)
          final parts = line.trim().split(RegExp(r'\s+'));
          if (parts.isNotEmpty) {
            final pid = parts.last;

            try {
              // Matar o processo usando o PID
              LoggerUtil.info('Killing process with PID $pid on port $port');
              final killResult = await Process.run(
                  'taskkill',
                  ['/F', '/PID', pid],
                  runInShell: true
              );

              if (killResult.exitCode == 0) {
                LoggerUtil.info('Successfully killed process on port $port');
                return true;
              } else {
                LoggerUtil.warning('Failed to kill process on port $port: ${killResult.stderr}');
              }
            } catch (e) {
              LoggerUtil.error('Error killing process on Windows', e);
            }
          }
        }
      }

      return false;
    } catch (e) {
      LoggerUtil.error('Error checking port on Windows', e);
      return false;
    }
  }

  /// Verifica se a porta está em uso no Unix (macOS/Linux) e mata o processo
  Future<bool> _checkAndKillProcessUnix(int port) async {
    try {
      // Usar lsof para listar processos que estão usando a porta
      final lsofResult = await Process.run(
          'lsof',
          ['-i', '-P', '-n', '|', 'grep', '$port'],
          runInShell: true
      );

      if (lsofResult.exitCode != 0 || (lsofResult.stdout as String).isEmpty) {
        // Try directly with grep since pipe might not work in Process.run
        final directResult = await Process.run(
            'lsof',
            ['-i:$port', '-P', '-n'],
            runInShell: true
        );

        if (directResult.exitCode != 0 || (directResult.stdout as String).isEmpty) {
          // Porta não está em uso
          return true;
        }

        LoggerUtil.info('Port $port is in use. Output: ${directResult.stdout}');

        // Analisar saída do lsof para extrair PID
        final lines = (directResult.stdout as String).split('\n');
        final pids = <String>{};

        for (var line in lines) {
          if (line.contains('LISTEN') || line.contains(':$port')) {
            // O segundo campo geralmente é o PID
            final parts = line.trim().split(RegExp(r'\s+'));
            if (parts.length > 1) {
              pids.add(parts[1]);
            }
          }
        }

        // Matar cada processo encontrado
        for (var pid in pids) {
          try {
            LoggerUtil.info('Killing process with PID $pid on port $port');
            final killResult = await Process.run('kill', ['-9', pid]);

            if (killResult.exitCode == 0) {
              LoggerUtil.info('Successfully killed process $pid on port $port');
            } else {
              LoggerUtil.warning('Failed to kill process $pid on port $port: ${killResult.stderr}');
            }
          } catch (e) {
            LoggerUtil.error('Error killing process on Unix', e);
          }
        }

        // Verificar novamente se a porta está livre
        final checkAgainResult = await Process.run('lsof', ['-i:$port', '-P', '-n']);
        return checkAgainResult.exitCode != 0 || (checkAgainResult.stdout as String).isEmpty;
      } else {
        LoggerUtil.info('Port $port is in use. Output: ${lsofResult.stdout}');

        // Analisar saída do lsof para extrair PID
        final lines = (lsofResult.stdout as String).split('\n');
        final pids = <String>{};

        for (var line in lines) {
          if (line.contains('LISTEN') || line.contains(':$port')) {
            // O segundo campo geralmente é o PID
            final parts = line.trim().split(RegExp(r'\s+'));
            if (parts.length > 1) {
              pids.add(parts[1]);
            }
          }
        }

        // Matar cada processo encontrado
        for (var pid in pids) {
          try {
            LoggerUtil.info('Killing process with PID $pid on port $port');
            final killResult = await Process.run('kill', ['-9', pid]);

            if (killResult.exitCode == 0) {
              LoggerUtil.info('Successfully killed process $pid on port $port');
            } else {
              LoggerUtil.warning('Failed to kill process $pid on port $port: ${killResult.stderr}');
            }
          } catch (e) {
            LoggerUtil.error('Error killing process on Unix', e);
          }
        }

        // Verificar novamente se a porta está livre
        final checkAgainResult = await Process.run('lsof', ['-i:$port', '-P', '-n']);
        return checkAgainResult.exitCode != 0 || (checkAgainResult.stdout as String).isEmpty;
      }
    } catch (e) {
      LoggerUtil.error('Error checking port on Unix', e);
      return false;
    }
  }

  /// Verificar se a porta está disponível usando Socket
  Future<bool> isPortAvailable(int port) async {
    try {
      final socket = await ServerSocket.bind(InternetAddress.loopbackIPv4, port, shared: true);
      await socket.close();
      return true;
    } catch (e) {
      LoggerUtil.debug('Port $port is not available: $e');
      return false;
    }
  }
}