import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:file_picker/file_picker.dart';
import 'package:microdetect/core/enums/backend_status_enum.dart';
import '../controllers/backend_monitor_controller.dart';
import '../../../core/services/backend_service.dart';
import '../../../core/services/backend_installer_service.dart';
import '../../../core/utils/logger_util.dart';
import '../../../design_system/app_colors.dart';
import '../../../design_system/app_typography.dart';
import 'dart:io';
import 'package:path/path.dart' as path;

/// Widget que exibe o status do backend e oferece controles
class BackendStatusWidget extends GetView<BackendMonitorController> {
  final bool isDarkMode;

  Color get _titleColor => isDarkMode ? AppColors.neutralLight : AppColors.neutralDark;
  Color get _statusTextColor => isDarkMode ? AppColors.neutralLight : AppColors.neutralDark;

  const BackendStatusWidget({Key? key, required this.isDarkMode}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Acessando o BackendService através do padrão singleton do GetX
    final BackendService backendService = BackendService.to;
    
    return Obx(() {
      // Determinar cor do status
      Color statusColor;
      switch (controller.status.value) {
        case BackendStatus.running:
          statusColor = AppColors.success;
          break;
        case BackendStatus.initializing:
        case BackendStatus.starting:
        case BackendStatus.checking:
          statusColor = AppColors.warning;
          break;
        case BackendStatus.error:
          statusColor = AppColors.error;
          break;
        case BackendStatus.stopping:
        case BackendStatus.stopped:
          statusColor = AppColors.neutralDark;
          break;
        case BackendStatus.unknown:
          statusColor = AppColors.grey;
          break;
      }

      // Texto do status
      String statusText;
      switch (controller.status.value) {
        case BackendStatus.running:
          statusText = 'Em execução';
          break;
        case BackendStatus.initializing:
          statusText = 'Inicializando...';
          break;
        case BackendStatus.starting:
          statusText = 'Iniciando...';
          break;
        case BackendStatus.checking:
          statusText = 'Verificando...';
          break;
        case BackendStatus.error:
          statusText = 'Erro';
          break;
        case BackendStatus.stopping:
          statusText = 'Parando...';
          break;
        case BackendStatus.stopped:
          statusText = 'Parado';
          break;
        case BackendStatus.unknown:
          statusText = 'Desconhecido';
          break;
      }

      return Card(
        elevation: 1,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Serviço Python',
                    style: AppTypography.textTheme.titleMedium?.copyWith(
                      color: _titleColor,
                    ),
                  ),
                  _buildVersionButton(context),
                ],
              ),
              const SizedBox(height: 16),
              
              // Status
              Row(
                children: [
                  Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      color: statusColor,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    statusText,
                    style: AppTypography.textTheme.bodyMedium?.copyWith(
                      color: _statusTextColor,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    controller.statusMessage.value,
                    style: AppTypography.textTheme.bodyMedium?.copyWith(
                      color: _statusTextColor,
                    ),
                  ),
                ],
              ),
              
              const SizedBox(height: 16),
              
              // Botões de controle
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  // Botão de diagnóstico
                  OutlinedButton(
                    onPressed: () => _showDiagnosticsDialog(context),
                    child: const Text('Diagnóstico'),
                  ),
                  const SizedBox(width: 8),
                  
                  // Botão para tentar resolver automaticamente os problemas
                  if (controller.status.value == BackendStatus.error)
                    OutlinedButton(
                      onPressed: () async {
                        final result = await backendService.cleanAndReinitialize();
                        LoggerUtil.info(
                          result 
                              ? 'Backend reinicializado com sucesso' 
                              : 'Não foi possível reinicializar automaticamente'
                        );
                      },
                      child: const Text('Reparar'),
                    ),
                  
                  // Espaçador só adicionado se houver botão de reparação
                  if (controller.status.value == BackendStatus.error)
                    const SizedBox(width: 8),
                    
                  // Botão para atualizar o backend
                  if (controller.status.value == BackendStatus.error)
                    OutlinedButton(
                      onPressed: controller.isInitializing.value
                          ? null
                          : () => _showUpdateDialog(context),
                      child: const Text('Atualizar Backend'),
                    ),
                  const SizedBox(width: 8),
                  OutlinedButton(
                    onPressed: controller.isInitializing.value
                        ? null
                        : () => controller.restartBackend(),
                    child: const Text('Reiniciar'),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    onPressed: controller.isInitializing.value
                        ? null
                        : controller.isRunning.value
                            ? () => backendService.stop()
                            : () => backendService.initialize(),
                    child: Text(
                      controller.isRunning.value ? 'Parar' : 'Iniciar',
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      );
    });
  }
  
  // Widget para exibir e verificar a versão
  Widget _buildVersionButton(BuildContext context) {
    return TextButton.icon(
      icon: const Icon(Icons.info_outline, size: 18),
      label: const Text('Versão'),
      style: TextButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
      onPressed: () => _checkForUpdates(context),
    );
  }
  
  // Verificar atualizações disponíveis
  Future<void> _checkForUpdates(BuildContext context) async {
    // Mostrar diálogo de loading
    Get.dialog(
      const AlertDialog(
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Verificando versão...'),
          ],
        ),
      ),
      barrierDismissible: false,
    );
    
    try {
      // Obter o instalador usando o padrão singleton
      final installer = BackendInstallerService.to;
      
      // Obter versões - agora já observáveis
      await installer.getCurrentVersion();
      await installer.getAssetVersion();
      final updateAvailable = await installer.isUpdateAvailable();
      
      // Fechar diálogo de loading
      Get.back();
      
      // Mostrar diálogo com as informações de versão e opção de atualizar
      Get.dialog(
        AlertDialog(
          title: const Text('Informações de Versão'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Obx(() => Text('Versão instalada: ${installer.currentVersion.value}')),
              const SizedBox(height: 8),
              Obx(() => Text('Versão disponível: ${installer.assetVersion.value}')),
              const SizedBox(height: 16),
              updateAvailable
                  ? const Text(
                      'Há uma nova versão disponível! Deseja atualizar?',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    )
                  : const Text(
                      'Você está utilizando a versão mais recente.',
                      style: TextStyle(color: AppColors.success),
                    ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Get.back(),
              child: const Text('Fechar'),
            ),
            if (updateAvailable)
              ElevatedButton(
                onPressed: () async {
                  // Fechar diálogo atual
                  Get.back();
                  
                  // Mostrar diálogo de progresso
                  Get.dialog(
                    AlertDialog(
                      content: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const CircularProgressIndicator(),
                          const SizedBox(height: 16),
                          const Text('Atualizando backend...'),
                          const SizedBox(height: 8),
                          // Mostrar progresso de instalação
                          Obx(() => LinearProgressIndicator(
                            value: installer.installProgress.value,
                          )),
                          const SizedBox(height: 8),
                          Obx(() => Text(
                            '${(installer.installProgress.value * 100).toInt()}%'
                          )),
                        ],
                      ),
                    ),
                    barrierDismissible: false,
                  );
                  
                  // Atualizar backend
                  final success = await installer.update();
                  
                  // Fechar diálogo de progresso
                  Get.back();
                  
                  // Mostrar resultado
                  LoggerUtil.info(
                    success
                        ? 'Backend atualizado com sucesso! Reiniciando...'
                        : 'Falha ao atualizar backend.'
                  );
                  
                  // Se atualização foi bem sucedida, reiniciar o backend
                  if (success) {
                    controller.restartBackend();
                  }
                },
                child: const Text('Atualizar'),
              ),
          ],
        ),
      );
    } catch (e) {
      // Fechar diálogo de loading em caso de erro
      Get.back();
      
      // Mostrar erro
      LoggerUtil.error('Erro ao verificar versões', e);
    }
  }
  
  // Diálogo para atualizar o backend
  Future<void> _showUpdateDialog(BuildContext context) async {
    // Acesso ao backend service pela singleton
    final backendService = BackendService.to;
    
    // Tentar encontrar o caminho do backend Python automaticamente
    String? detectedBackendPath = await _detectBackendPath();
    
    Get.dialog(
      AlertDialog(
        title: const Text('Atualizar Backend Python'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Selecione a pasta que contém o backend Python para atualizar a instalação atual.',
              style: TextStyle(fontSize: 14),
            ),
            const SizedBox(height: 12),
            const Text(
              'Nota: A pasta deve conter o arquivo "start_backend.py" e a estrutura de diretórios necessária.',
              style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic),
            ),
            
            // Mostrar caminho detectado se houver
            if (detectedBackendPath != null) ...[
              const SizedBox(height: 16),
              const Text(
                'Backend detectado em:',
                style: TextStyle(fontWeight: FontWeight.w500, fontSize: 14),
              ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: Text(
                  detectedBackendPath,
                  style: const TextStyle(
                    fontSize: 12,
                    fontFamily: 'monospace',
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Center(
                child: ElevatedButton(
                  onPressed: () async {
                    Get.back();
                    
                    // Atualizar backend com o caminho detectado
                    final success = await backendService.updateBackendFromSource(detectedBackendPath);
                    
                    LoggerUtil.info(
                      success 
                          ? 'Backend Python atualizado com sucesso'
                          : 'Falha ao atualizar o backend Python'
                    );
                  },
                  child: const Text('Usar Pasta Detectada'),
                ),
              ),
              const SizedBox(height: 16),
              const Center(
                child: Text(
                  'ou',
                  style: TextStyle(fontStyle: FontStyle.italic),
                ),
              ),
              const SizedBox(height: 8),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () async {
              Get.back();
              
              // Selecionar diretório do backend Python
              String? selectedDirectory = await FilePicker.platform.getDirectoryPath(
                dialogTitle: 'Selecione a pasta do backend Python',
              );
              
              if (selectedDirectory != null) {
                // Verificar se o diretório contém start_backend.py
                final scriptFile = File('$selectedDirectory/start_backend.py');
                if (!await scriptFile.exists()) {
                  LoggerUtil.error(
                    'Pasta inválida: Não contém start_backend.py'
                  );
                  return;
                }
                
                // Atualizar o backend
                final success = await backendService.updateBackendFromSource(selectedDirectory);
                
                LoggerUtil.info(
                  success 
                      ? 'Backend Python atualizado com sucesso'
                      : 'Falha ao atualizar o backend Python'
                );
              }
            },
            child: const Text('Selecionar Pasta Manualmente'),
          ),
        ],
      ),
    );
  }
  
  /// Detecta automaticamente o caminho do backend Python
  Future<String?> _detectBackendPath() async {
    try {
      final projectDirs = [
        // Pasta anexada explicitamente (enviada pelo usuário)
        '/Users/rodolfodebonis/Documents/projects/microdetect/python_backend',
        
        // Projeto atual (provável localização em desenvolvimento)
        '${Directory.current.path}/python_backend',
        
        // Pasta do usuário/Documents/projects/microdetect/python_backend
        if (Platform.environment['HOME'] != null)
          '${Platform.environment['HOME']}/Documents/projects/microdetect/python_backend',
          
        // Pasta do aplicativo (se estiver em execução como aplicativo)
        '${path.dirname(Platform.resolvedExecutable)}/python_backend',
        '${path.dirname(path.dirname(Platform.resolvedExecutable))}/python_backend',
        
        // Recursos do macOS
        if (Platform.isMacOS)
          '${path.dirname(path.dirname(Platform.resolvedExecutable))}/Resources/python_backend',
          
        // Pasta do usuário
        if (Platform.environment['HOME'] != null)
          '${Platform.environment['HOME']}/microdetect/python_backend',
      ];
      
      // Verificar cada diretório
      for (final dir in projectDirs) {
        final directory = Directory(dir);
        if (await directory.exists()) {
          // Verificar se contém start_backend.py
          final script = File('$dir/start_backend.py');
          if (await script.exists()) {
            return dir;
          }
        }
      }
      
      return null;
    } catch (e) {
      LoggerUtil.error('Erro ao detectar backend', e);
      return null;
    }
  }

  // Diálogo para mostrar diagnóstico
  Future<void> _showDiagnosticsDialog(BuildContext context) async {
    // Iniciar diagnóstico
    Get.dialog(
      const AlertDialog(
        title: Text('Diagnóstico do Backend'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Coletando informações...'),
          ],
        ),
      ),
      barrierDismissible: false,
    );
    
    // Executar diagnóstico
    await controller.runDiagnostics();
    
    // Fechar diálogo de carregamento
    Get.back();
    
    // Mostrar resultados usando diagnosticResult observável
    Get.dialog(
      AlertDialog(
        title: const Text('Diagnóstico do Backend'),
        content: Obx(() {
          if (controller.lastDiagnosticResult.value == null) {
            return const Center(child: Text('Nenhuma informação disponível'));
          }
          
          final diagnostics = controller.lastDiagnosticResult.value!;
          
          return SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Status atual
                _buildDiagnosticSection(
                  'Status Atual', 
                  diagnostics['currentStatus'] ?? {},
                ),
                const Divider(),
                
                // Instalação
                _buildDiagnosticSection(
                  'Instalação', 
                  {
                    'Status': diagnostics['isInstalled'] == true ? 'Instalado' : 'Não instalado',
                    'Problemas': _formatIssues(diagnostics['issues']),
                  },
                ),
                const Divider(),
                
                // Python
                _buildDiagnosticSection(
                  'Python', 
                  {
                    'Disponível': diagnostics['pythonAvailable'] == true ? 'Sim' : 'Não',
                    'Caminho': diagnostics['pythonPath'] ?? 'Não encontrado',
                  },
                ),
                const Divider(),
                
                // Detalhes da instalação
                _buildDiagnosticSection(
                  'Detalhes da Instalação', 
                  diagnostics['details'] ?? {},
                ),
                
                // Opções de recuperação
                if (diagnostics['isInstalled'] == false)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Divider(),
                      const Text(
                        'Opções de Recuperação',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Você pode tentar atualizar o backend a partir da pasta do projeto:',
                        style: TextStyle(fontSize: 14),
                      ),
                      const SizedBox(height: 12),
                      Center(
                        child: ElevatedButton(
                          onPressed: () {
                            Get.back();
                            _showUpdateDialog(context);
                          },
                          child: const Text('Atualizar Backend'),
                        ),
                      ),
                    ],
                  ),
              ],
            ),
          );
        }),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: const Text('Fechar'),
          ),
        ],
      ),
    );
  }
  
  // Formatar problemas de forma segura
  String _formatIssues(dynamic issues) {
    if (issues == null) {
      return 'Nenhum problema encontrado';
    }
    
    if (issues is Set && issues.isNotEmpty) {
      return issues.join('\n');
    }
    
    if (issues is List && issues.isNotEmpty) {
      return issues.join('\n');
    }
    
    return 'Nenhum problema encontrado';
  }
  
  // Construir uma seção de diagnóstico
  Widget _buildDiagnosticSection(String title, Map<dynamic, dynamic> data) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        const SizedBox(height: 8),
        ...data.entries.map((entry) {
          var value = entry.value;
          // Formatar valores booleanos
          if (value is bool) {
            value = value ? 'Sim' : 'Não';
          }
          
          return Padding(
            padding: const EdgeInsets.only(left: 8.0, bottom: 4.0),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${entry.key}: ',
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
                Expanded(
                  child: Text(
                    value.toString(),
                    style: const TextStyle(
                      fontFamily: 'monospace',
                    ),
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ],
    );
  }
}
