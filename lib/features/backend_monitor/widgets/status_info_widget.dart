import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/enums/backend_status_enum.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';

class StatusInfoWidget extends StatelessWidget {
  final BackendStatus status;
  final String statusMessage;
  final bool isRunning;
  final bool isInitializing;
  final Duration initTime;

  const StatusInfoWidget({
    Key? key,
    required this.status,
    required this.statusMessage,
    required this.isRunning,
    required this.isInitializing,
    required this.initTime,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      color: ThemeColors.surface(context),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: ThemeColors.border(context)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.medium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Status do Backend', 
              style: AppTypography.titleMedium(context),
            ),
            const SizedBox(height: AppSpacing.small),
            
            // Status atual com ícone
            Row(
              children: [
                _buildStatusIcon(),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _getStatusText(),
                        style: AppTypography.bodyMedium(context).copyWith(
                          fontWeight: FontWeight.bold,
                          color: _getStatusColor(),
                        ),
                      ),
                      Text(
                        statusMessage,
                        style: AppTypography.bodySmall(context),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.medium),
            
            // Detalhes adicionais
            _buildDetailRow(
              context, 
              'Servidor ativo:', 
              isRunning ? 'Sim' : 'Não',
              icon: isRunning ? Icons.check_circle : Icons.cancel,
              iconColor: isRunning ? AppColors.success : AppColors.error,
            ),
            const SizedBox(height: AppSpacing.xSmall),
            
            // Inicialização
            _buildDetailRow(
              context, 
              'Inicializando:', 
              isInitializing ? 'Em progresso' : 'Não',
              icon: isInitializing ? Icons.hourglass_top : Icons.hourglass_disabled,
              iconColor: isInitializing ? AppColors.warning : AppColors.neutralDark,
            ),
            
            // Mostrar o tempo de inicialização apenas se estiver inicializando
            if (isInitializing) ...[
              const SizedBox(height: AppSpacing.xSmall),
              _buildDetailRow(
                context, 
                'Tempo decorrido:',
                _formatDuration(initTime),
                icon: Icons.timer,
                iconColor: initTime.inMinutes >= 2 
                  ? AppColors.error
                  : initTime.inSeconds >= 30 
                    ? AppColors.warning
                    : AppColors.info,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildStatusIcon() {
    IconData iconData;
    Color iconColor;
    
    switch (status) {
      case BackendStatus.starting:
      case BackendStatus.checking:
      case BackendStatus.initializing:
        iconData = Icons.refresh;
        iconColor = AppColors.info;
        break;
      case BackendStatus.running:
        iconData = Icons.check_circle;
        iconColor = AppColors.success;
        break;
      case BackendStatus.stopping:
        iconData = Icons.pause_circle;
        iconColor = AppColors.warning;
        break;
      case BackendStatus.error:
        iconData = Icons.error;
        iconColor = AppColors.error;
        break;
      default:
        iconData = Icons.help;
        iconColor = AppColors.neutralDark;
    }
    
    return Icon(
      iconData,
      color: iconColor,
      size: 24,
    );
  }
  
  String _getStatusText() {
    switch (status) {
      case BackendStatus.starting:
        return 'Iniciando';
      case BackendStatus.checking:
        return 'Verificando';
      case BackendStatus.initializing:
        return 'Inicializando';
      case BackendStatus.running:
        return 'Em execução';
      case BackendStatus.stopping:
        return 'Parando';
      case BackendStatus.error:
        return 'Erro';
      default:
        return 'Desconhecido';
    }
  }
  
  Color _getStatusColor() {
    switch (status) {
      case BackendStatus.starting:
      case BackendStatus.checking:
      case BackendStatus.initializing:
        return AppColors.info;
      case BackendStatus.running:
        return AppColors.success;
      case BackendStatus.stopping:
        return AppColors.warning;
      case BackendStatus.error:
        return AppColors.error;
      default:
        return AppColors.neutralDark;
    }
  }

  Widget _buildDetailRow(
    BuildContext context,
    String label, 
    String value, 
    {IconData? icon, Color? iconColor}
  ) {
    return Row(
      children: [
        if (icon != null) ...[
          Icon(
            icon,
            color: iconColor ?? AppColors.neutralDark,
            size: 16,
          ),
          const SizedBox(width: 4),
        ],
        Text(
          label,
          style: AppTypography.bodySmall(context).copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          value,
          style: AppTypography.bodySmall(context),
        ),
      ],
    );
  }
  
  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    String twoDigitMinutes = twoDigits(duration.inMinutes.remainder(60));
    String twoDigitSeconds = twoDigits(duration.inSeconds.remainder(60));
    
    if (duration.inHours > 0) {
      return '${duration.inHours}:$twoDigitMinutes:$twoDigitSeconds';
    } else {
      return '$twoDigitMinutes:$twoDigitSeconds';
    }
  }
} 