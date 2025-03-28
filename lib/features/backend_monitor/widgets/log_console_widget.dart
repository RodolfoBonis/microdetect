import 'package:flutter/material.dart';
import 'dart:ui';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import '../../../design_system/app_toast.dart';

class LogConsoleWidget extends StatefulWidget {
  final RxList<String> logs;
  final bool scrollToBottom;
  final bool darkMode;

  const LogConsoleWidget({
    Key? key,
    required this.logs,
    this.scrollToBottom = true,
    this.darkMode = true,
  }) : super(key: key);

  @override
  State<LogConsoleWidget> createState() => _LogConsoleWidgetState();
}

class _LogConsoleWidgetState extends State<LogConsoleWidget> {
  final ScrollController _scrollController = ScrollController();
  bool _autoScroll = true;

  @override
  void initState() {
    super.initState();
    _autoScroll = widget.scrollToBottom;
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    if (!_autoScroll || !widget.scrollToBottom) return;
    
    // Adicionar um pequeno atraso para garantir que a rolagem ocorra após a renderização
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      margin: EdgeInsets.zero,
      color: widget.darkMode 
          ? const Color(0xFF1E1E1E) 
          : ThemeColors.surface(context),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(
          color: ThemeColors.border(context),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.small),
            decoration: BoxDecoration(
              color: widget.darkMode 
                  ? const Color(0xFF2D2D2D) 
                  : ThemeColors.background(context),
              borderRadius: const BorderRadius.vertical(
                top: Radius.circular(8),
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Icon(
                      Icons.terminal,
                      size: 18,
                      color: widget.darkMode 
                          ? Colors.white70 
                          : ThemeColors.text(context),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Console de Logs',
                      style: (widget.darkMode 
                          ? AppTypography.bodyMedium(context).copyWith(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ) 
                          : AppTypography.bodyMedium(context).copyWith(
                              fontWeight: FontWeight.bold,
                            )),
                    ),
                  ],
                ),
                Row(
                  children: [
                    // Botão de autoscroll
                    InkWell(
                      onTap: () {
                        setState(() {
                          _autoScroll = !_autoScroll;
                        });
                        if (_autoScroll) {
                          _scrollToBottom();
                        }
                      },
                      borderRadius: BorderRadius.circular(4),
                      child: Padding(
                        padding: const EdgeInsets.all(8.0),
                        child: Row(
                          children: [
                            Icon(
                              _autoScroll
                                  ? Icons.vertical_align_bottom
                                  : Icons.vertical_align_center,
                              size: 16,
                              color: widget.darkMode
                                  ? (_autoScroll ? Colors.green : Colors.white60)
                                  : (_autoScroll ? AppColors.primary : ThemeColors.textSecondary(context)),
                            ),
                            const SizedBox(width: 4),
                            Text(
                              _autoScroll ? 'Auto-rolar' : 'Rolagem manual',
                              style: AppTypography.labelSmall(context).copyWith(
                                color: widget.darkMode
                                    ? (_autoScroll ? Colors.green : Colors.white60)
                                    : (_autoScroll ? AppColors.primary : ThemeColors.textSecondary(context)),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    // Botão de limpar
                    const SizedBox(width: 8),
                    Tooltip(
                      message: 'Copiar logs',
                      child: InkWell(
                        onTap: () {
                          final logText = widget.logs.join('\n');
                          // TODO: Implementar cópia para clipboard
                          AppToast.success(
                            'Copiado',
                            description: '${widget.logs.length} linhas de log copiadas para o clipboard',
                            duration: const Duration(seconds: 2),
                          );
                        },
                        borderRadius: BorderRadius.circular(4),
                        child: Padding(
                          padding: const EdgeInsets.all(8.0),
                          child: Icon(
                            Icons.copy,
                            size: 16,
                            color: widget.darkMode
                                ? Colors.white60
                                : ThemeColors.textSecondary(context),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Expanded(
            child: Obx(() {
              if (widget.scrollToBottom && _autoScroll) {
                _scrollToBottom();
              }
              
              return Container(
                decoration: BoxDecoration(
                  color: widget.darkMode
                      ? const Color(0xFF1E1E1E)
                      : ThemeColors.surface(context),
                  borderRadius: const BorderRadius.vertical(
                    bottom: Radius.circular(8),
                  ),
                ),
                child: widget.logs.isEmpty
                    ? _buildEmptyState()
                    : _buildLogsList(),
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.article_outlined,
            size: 48,
            color: ThemeColors.textSecondary(context),
          ),
          const SizedBox(height: AppSpacing.small),
          Text(
            'Nenhum log para exibir',
            style: AppTypography.bodyMedium(context).copyWith(
              color: ThemeColors.textSecondary(context),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLogsList() {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.all(AppSpacing.small),
      itemCount: widget.logs.length,
      itemBuilder: (context, index) {
        final log = widget.logs[index];
        return _buildLogEntry(log, index);
      },
    );
  }

  Widget _buildLogEntry(String log, int index) {
    // Determinar o tipo de log para estilização
    Color logColor = widget.darkMode ? Colors.white70 : ThemeColors.text(context);
    
    if (log.toLowerCase().contains('erro') || 
        log.toLowerCase().contains('error') || 
        log.toLowerCase().contains('falha') || 
        log.toLowerCase().contains('failed')) {
      logColor = AppColors.error;
    } else if (log.toLowerCase().contains('aviso') || 
               log.toLowerCase().contains('warning') || 
               log.toLowerCase().contains('warn')) {
      logColor = AppColors.warning;
    } else if (log.toLowerCase().contains('info') || 
               log.toLowerCase().contains('informação')) {
      logColor = widget.darkMode ? Colors.lightBlue : AppColors.info;
    } else if (log.toLowerCase().contains('sucesso') || 
               log.toLowerCase().contains('success') || 
               log.toLowerCase().contains('concluído')) {
      logColor = AppColors.success;
    }
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 1),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Número da linha
          SizedBox(
            width: 40,
            child: Text(
              '${index + 1}',
              style: AppTypography.bodySmall(context).copyWith(
                color: ThemeColors.textSecondary(context),
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
            ),
          ),
          Expanded(
            child: Text(
              log,
              style: AppTypography.bodySmall(context).copyWith(
                color: logColor,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
} 