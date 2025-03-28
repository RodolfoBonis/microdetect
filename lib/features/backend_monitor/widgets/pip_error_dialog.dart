// lib/features/backend_monitor/widgets/pip_error_dialog.dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/enums/backend_status_enum.dart';
import 'package:microdetect/core/services/backend_service.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';

/// Diálogo para exibir erros do pip e oferecer opções avançadas
class PipErrorDialog extends StatefulWidget {
  final String errorMessage;

  const PipErrorDialog({
    Key? key,
    required this.errorMessage,
  }) : super(key: key);

  @override
  State<PipErrorDialog> createState() => _PipErrorDialogState();

  /// Mostra o diálogo com os logs de erro
  static Future<void> show(String errorMessage) async {
    return Get.dialog(
      PipErrorDialog(errorMessage: errorMessage),
      barrierDismissible: false,
    );
  }
}

class _PipErrorDialogState extends State<PipErrorDialog> {
  bool _showAdvancedOptions = false;
  bool _useSystemPython = true;
  bool _skipDependencyCheck = false;
  bool _useUserInstall = true;
  bool _forceReinstall = false;
  bool _isInstalling = false;
  String _customPipArgs = '--no-cache-dir';

  // Controlador para o campo de texto
  final TextEditingController _customPipArgsController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _customPipArgsController.text = _customPipArgs;
  }

  @override
  void dispose() {
    _customPipArgsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Row(
        children: [
          Icon(Icons.error_outline, color: AppColors.error),
          const SizedBox(width: 8),
          const Text('Erro na Instalação do Pip'),
        ],
      ),
      content: SizedBox(
        width: 600,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Ocorreu um erro durante a instalação do backend Python. '
                    'Veja os detalhes abaixo:',
              ),
              const SizedBox(height: 16),

              // Logs de erro em um container com scroll
              Container(
                padding: const EdgeInsets.all(12),
                height: 150,
                decoration: BoxDecoration(
                  color: Colors.black87,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: SingleChildScrollView(
                  child: SelectableText(
                    widget.errorMessage,
                    style: const TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 12,
                      color: Colors.white,
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Toggle para opções avançadas
              InkWell(
                onTap: () {
                  setState(() {
                    _showAdvancedOptions = !_showAdvancedOptions;
                  });
                },
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Row(
                    children: [
                      Icon(
                        _showAdvancedOptions
                            ? Icons.keyboard_arrow_down
                            : Icons.keyboard_arrow_right,
                        size: 20,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        'Opções Avançadas',
                        style: AppTypography.bodyMedium(context).copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Opções avançadas condicionais
              if (_showAdvancedOptions) ...[
                const SizedBox(height: 8),

                // Checkbox para usar Python do sistema
                CheckboxListTile(
                  title: const Text('Usar Python do sistema'),
                  subtitle: const Text(
                    'Tenta encontrar uma instalação de Python existente no sistema em vez de usar o ambiente virtual',
                    style: TextStyle(fontSize: 12),
                  ),
                  value: _useSystemPython,
                  onChanged: (value) {
                    setState(() {
                      _useSystemPython = value ?? true;
                    });
                  },
                  controlAffinity: ListTileControlAffinity.leading,
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                ),

                // Checkbox para ignorar verificação de dependências
                CheckboxListTile(
                  title: const Text('Ignorar verificação de dependências'),
                  subtitle: const Text(
                    'Instala apenas o pacote principal sem verificar dependências',
                    style: TextStyle(fontSize: 12),
                  ),
                  value: _skipDependencyCheck,
                  onChanged: (value) {
                    setState(() {
                      _skipDependencyCheck = value ?? false;
                    });
                  },
                  controlAffinity: ListTileControlAffinity.leading,
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                ),

                // Checkbox para instalação de usuário
                CheckboxListTile(
                  title: const Text('Instalar para o usuário atual'),
                  subtitle: const Text(
                    'Usa a flag --user para instalar sem privilégios de administrador',
                    style: TextStyle(fontSize: 12),
                  ),
                  value: _useUserInstall,
                  onChanged: (value) {
                    setState(() {
                      _useUserInstall = value ?? true;
                    });
                  },
                  controlAffinity: ListTileControlAffinity.leading,
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                ),

                // Checkbox para forçar reinstalação
                CheckboxListTile(
                  title: const Text('Forçar reinstalação'),
                  subtitle: const Text(
                    'Reinstala mesmo que já exista uma versão instalada',
                    style: TextStyle(fontSize: 12),
                  ),
                  value: _forceReinstall,
                  onChanged: (value) {
                    setState(() {
                      _forceReinstall = value ?? false;
                    });
                  },
                  controlAffinity: ListTileControlAffinity.leading,
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                ),

                // Campo para argumentos personalizados
                const SizedBox(height: 8),
                const Text(
                  'Argumentos adicionais para o pip:',
                  style: TextStyle(fontSize: 14),
                ),
                const SizedBox(height: 4),
                TextField(
                  controller: _customPipArgsController,
                  decoration: InputDecoration(
                    hintText: 'Ex: --timeout 100 --retries 5',
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 8,
                    ),
                  ),
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 13),
                  onChanged: (value) {
                    _customPipArgs = value;
                  },
                ),

                const SizedBox(height: 8),
                const Text(
                  'Sugestões de argumentos úteis:',
                  style: TextStyle(fontSize: 12),
                ),
                const SizedBox(height: 4),
                Wrap(
                  spacing: 8,
                  children: [
                    _buildSuggestionChip('--no-cache-dir'),
                    _buildSuggestionChip('--timeout 100'),
                    _buildSuggestionChip('--retries 5'),
                    _buildSuggestionChip('--trusted-host pypi.org'),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isInstalling ? null : () => Get.back(),
          child: const Text('Cancelar'),
        ),
        ElevatedButton(
          onPressed: _isInstalling ? null : _retryInstallation,
          child: _isInstalling
              ? Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              ),
              const SizedBox(width: 8),
              const Text('Instalando...'),
            ],
          )
              : const Text('Tentar Novamente'),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.primary,
            foregroundColor: Colors.white,
          ),
        ),
      ],
    );
  }

  /// Constrói um chip de sugestão de argumento
  Widget _buildSuggestionChip(String suggestion) {
    return GestureDetector(
      onTap: () {
        // Adicionar a sugestão ao campo de texto se já não estiver lá
        if (!_customPipArgsController.text.contains(suggestion)) {
          final currentText = _customPipArgsController.text.trim();
          final newText = currentText.isEmpty
              ? suggestion
              : '$currentText $suggestion';

          setState(() {
            _customPipArgsController.text = newText;
            _customPipArgs = newText;
          });
        }
      },
      child: Chip(
        label: Text(
          suggestion,
          style: const TextStyle(fontSize: 11),
        ),
        padding: EdgeInsets.zero,
        labelPadding: const EdgeInsets.symmetric(horizontal: 8),
        backgroundColor: AppColors.neutralLight,
      ),
    );
  }

  /// Tenta reinstalar com as opções selecionadas
  Future<void> _retryInstallation() async {
    try {
      setState(() {
        _isInstalling = true;
      });

      // Obter o serviço de backend
      final BackendService backendService = Get.find<BackendService>();

      // Construir os argumentos com base nas opções selecionadas
      final List<String> pipArgs = ['install', 'microdetect', '--upgrade', '--no-input'];

      if (_useUserInstall) {
        pipArgs.add('--user');
      }

      if (_skipDependencyCheck) {
        pipArgs.add('--no-deps');
      }

      if (_forceReinstall) {
        pipArgs.add('--force-reinstall');
      }

      // Adicionar argumentos personalizados
      if (_customPipArgs.isNotEmpty) {
        final customArgs = _customPipArgs.split(' ')
            .where((arg) => arg.isNotEmpty)
            .toList();
        pipArgs.addAll(customArgs);
      }

      // Adicionar ambiente personalizado
      final environment = {
        'PIP_NO_INPUT': '1',
        'PYTHONIOENCODING': 'utf-8',
        'PYTHONUNBUFFERED': '1',
      };

      // Flag para indicar se deve usar o Python do sistema
      final useSystemPython = _useSystemPython;

      // Executar a operação em uma tarefa em segundo plano
      LoggerUtil.info('Tentando reinstalação com opções personalizadas: ${pipArgs.join(' ')}');

      // Tentar instalação com as opções personalizadas
      // Isso requer um método personalizado no BackendService que aceite estas opções
      final success = await backendService.retryInstallationWithCustomOptions(
        pipArgs: pipArgs,
        environment: environment,
        useSystemPython: useSystemPython,
      );

      if (success) {
        Get.back(); // Fechar diálogo

        // Iniciar o backend novamente
        backendService.initialize();
      } else {
        // Manter o diálogo aberto, mas permitir tentar novamente
        setState(() {
          _isInstalling = false;
        });

        // Mostrar um toast de erro
        Get.snackbar(
          'Erro',
          'Falha ao instalar o pacote. Tente outras opções.',
          backgroundColor: AppColors.error.withOpacity(0.9),
          colorText: Colors.white,
          snackPosition: SnackPosition.BOTTOM,
        );
      }
    } catch (e) {
      LoggerUtil.error('Erro ao tentar reinstalar com opções personalizadas', e);

      setState(() {
        _isInstalling = false;
      });

      Get.snackbar(
        'Erro',
        'Ocorreu um erro inesperado: $e',
        backgroundColor: AppColors.error.withOpacity(0.9),
        colorText: Colors.white,
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }
}