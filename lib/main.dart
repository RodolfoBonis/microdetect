import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:microdetect/config/app_directories.dart';
import 'package:microdetect/core/bindings/app_binding.dart';
import 'package:microdetect/core/services/backend_service.dart';
import 'package:microdetect/core/services/python_service.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/features/not-found/pages/not_found_page.dart';
import 'package:microdetect/features/settings/services/settings_initializer.dart';
import 'package:microdetect/features/settings/services/settings_service.dart';
import 'package:microdetect/routes/app_pages.dart';
import 'package:toastification/toastification.dart';

import 'design_system/app_theme.dart';

// Adicionar uma chave global para acessar a aplicação a partir de qualquer lugar
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

void main() async {
  // Garantir que a inicialização do Flutter seja concluída antes de qualquer outra operação
  WidgetsFlutterBinding.ensureInitialized();

  // Inicializar o sistema de diretórios primeiro
  await AppDirectories.instance.initialize();
  
  // Inicializar apenas o novo sistema de configurações
  await SettingsInitializer.initialize();
  
  // Inicializar formatação de data para a localidade atual
  await initializeDateFormatting();

  // Registrar manipuladores para sinais do sistema operacional
  // Isso garante que todos os processos Python sejam encerrados quando o aplicativo for fechado
  if (!kIsWeb) {
    // Manipular sinais de interrupção no sistema operacional
    ProcessSignal.sigint.watch().listen((_) {
      LoggerUtil.info('Recebido sinal SIGINT - Encerrando processos...');
      _cleanupAndExit();
    });
    
    if (!Platform.isWindows) {
      // SIGTERM geralmente é enviado quando o sistema operacional deseja encerrar o processo
      ProcessSignal.sigterm.watch().listen((_) {
        LoggerUtil.info('Recebido sinal SIGTERM - Encerrando processos...');
        _cleanupAndExit();
      });
    }
  }

  // Configurar handler para encerramento da aplicação via teclado
  WidgetsBinding.instance.addPostFrameCallback((_) {
    ServicesBinding.instance.keyboard.addHandler((KeyEvent event) {
      if (event is KeyDownEvent &&
          event.logicalKey == LogicalKeyboardKey.escape) {
        // Se o ESC for pressionado, encerre adequadamente o backend antes de fechar
        _cleanupAndExit();
        return true;
      }
      return false;
    });
  });

  runApp(MicrodetectApp());
}

// Função para limpar recursos e encerrar o aplicativo adequadamente
Future<void> _cleanupAndExit() async {
  try {
    LoggerUtil.info('Preparando para encerrar a aplicação...');
    
    // Tentar obter e parar serviços apenas se já estiverem registrados
    if (Get.isRegistered<BackendService>()) {
      await Get.find<BackendService>().forceStop();
      LoggerUtil.info('BackendService encerrado');
    }
    
    if (Get.isRegistered<PythonService>()) {
      await Get.find<PythonService>().stopServer(force: true);
      LoggerUtil.info('PythonService encerrado');
    }
    
    // Em plataformas que suportam, verificar processos restantes
    if (Platform.isMacOS || Platform.isLinux) {
      await _killRemainingPythonProcesses();
    }
    
    // Encerrar o aplicativo
    LoggerUtil.info('Encerrando aplicação');
    await Future.delayed(const Duration(milliseconds: 500));
    exit(0);
  } catch (e) {
    LoggerUtil.error('Erro ao encerrar aplicação', e);
    exit(1);
  }
}

// Verifica e mata qualquer processo Python relacionado ao backend
Future<void> _killRemainingPythonProcesses() async {
  try {
    // Buscar processos Python
    final result = await Process.run(
      'ps', 
      ['-ef'],
      stdoutEncoding: utf8,
    );
    
    if (result.exitCode == 0) {
      final output = result.stdout as String;
      final lines = output.split('\n');
      
      // Filtra processos do backend
      for (final line in lines) {
        if (line.contains('python') && 
            (line.contains('start_backend.py') || line.contains('microdetect'))) {
          final parts = line.trim().split(RegExp(r'\s+'));
          if (parts.length > 1) {
            final pid = parts[1];
            LoggerUtil.info('Matando processo Python restante: $pid');
            try {
              await Process.run('kill', ['-9', pid]);
            } catch (e) {
              LoggerUtil.error('Erro ao matar processo: $e');
            }
          }
        }
      }
    }
  } catch (e) {
    LoggerUtil.error('Erro ao verificar processos restantes', e);
  }
}

class MicrodetectApp extends StatefulWidget {
  MicrodetectApp({Key? key}) : super(key: key);

  @override
  State<MicrodetectApp> createState() => _MicrodetectAppState();
}

class _MicrodetectAppState extends State<MicrodetectApp> {
  final routeObserver = Get.put<RouteObserver>(RouteObserver<PageRoute>());

  @override
  void initState() {
    super.initState();
    _setupAppCloseHandler();
  }
  
  // Configurar handler para quando o aplicativo for fechado
  void _setupAppCloseHandler() {
    print('Configurando handler para fechar a aplicação...');
    // Isso pode ser usado para registrar handlers adicionais se necessário
    // para diferentes métodos de fechamento da aplicação
  }

  @override
  void dispose() {
    // Garantir que o backend seja parado antes de sair
    if (Get.isRegistered<BackendService>()) {
      Get.find<BackendService>().forceStop();
    }
    
    if (Get.isRegistered<PythonService>()) {
      Get.find<PythonService>().stopServer(force: true);
    }
    
    Get.deleteAll();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Iniciar a aplicação com o sistema de rotas GetX
    return ToastificationWrapper(
      child: GetMaterialApp(
        navigatorKey: navigatorKey,
        title: 'MicroDetect',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: Get.find<SettingsService>().themeMode, // Usar novo sistema de configurações
        navigatorObservers: [
          routeObserver,
        ],
        // Configuração das rotas
        initialRoute: AppRoutes.backendMonitor,
        getPages: AppPages.pageRoutes,
        builder: (context, child) {
          return ScrollConfiguration(
            behavior: const ScrollBehavior().copyWith(overscroll: false),
            child: child!,
          );
        },
        initialBinding: AppBinding(),
        onUnknownRoute: (settings) {
          return MaterialPageRoute(
            builder: (context) => NotFoundPage(title: settings.name ?? 'não encontrado'),
          );
        },
      ),
    );
  }
}
