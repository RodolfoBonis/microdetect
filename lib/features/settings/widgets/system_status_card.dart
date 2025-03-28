import 'dart:async';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/models/system_status_model.dart';
import 'package:microdetect/core/services/api_service.dart';
import 'package:microdetect/core/services/system_status_service.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_borders.dart';

/// Widget que exibe informações de status do sistema obtidas da API
class SystemStatusCard extends StatefulWidget {
  final bool isDarkMode;
  const SystemStatusCard({Key? key, required this.isDarkMode}) : super(key: key);

  @override
  State<SystemStatusCard> createState() => _SystemStatusCardState();
}

class _SystemStatusCardState extends State<SystemStatusCard> {
  final SystemStatusService _systemStatusService = Get.find<SystemStatusService>();
  SystemStatusModel? _systemStatus;
  bool _isLoading = true;
  String? _errorMessage;
  Timer? _refreshTimer;

  Color get _titleColor => widget.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark;
  Color get _valueColor => widget.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark;

  @override
  void initState() {
    super.initState();
    _loadSystemStatus();
    
    // Configurar timer para atualizar status a cada 30 segundos
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      _loadSystemStatus();
    });
  }
  
  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadSystemStatus() async {
    if (!mounted) return;
    
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final status = await _systemStatusService.getSystemStatus();
      
      if (!mounted) return;
      
      setState(() {
        _systemStatus = status;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.medium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Informações do Sistema',
                  style: AppTypography.textTheme.titleLarge?.copyWith(
                    color: _titleColor,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.refresh),
                  onPressed: _loadSystemStatus,
                  tooltip: 'Atualizar informações',
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.small),
            _buildContent(),
          ],
        ),
      ),
    );
  }

  Widget _buildContent() {
    if (_isLoading) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(AppSpacing.medium),
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.medium),
          child: Column(
            children: [
              const Icon(
                Icons.error_outline,
                color: AppColors.error,
                size: 48,
              ),
              const SizedBox(height: AppSpacing.small),
              Text(
                'Erro ao carregar informações',
                style: AppTypography.textTheme.bodyLarge?.copyWith(
                  color: AppColors.error,
                ),
              ),
              Text(
                _errorMessage!,
                style: AppTypography.textTheme.bodySmall,
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    if (_systemStatus == null) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(AppSpacing.medium),
          child: Text('Nenhuma informação disponível'),
        ),
      );
    }


    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _buildInfoRow(
          title: 'Sistema Operacional',
          value: _systemStatus!.os,
          icon: Icons.computer,
        ),
        _buildInfoRow(
          title: 'Processador',
          value: _systemStatus!.cpu.model,
          subtitle: 'Núcleos: ${_systemStatus!.cpu.cores} (${_systemStatus!.cpu.threads} threads) - Uso: ${_systemStatus!.cpu.usage}',
          icon: Icons.memory,
        ),
        _buildInfoRow(
          title: 'Memória RAM',
          value: '${_systemStatus!.memory.available} disponível de ${_systemStatus!.memory.total}',
          subtitle: 'Utilização: ${_systemStatus!.memory.percentage.toString()}%',
          icon: Icons.memory_outlined,
          status: _getStorageStatus(_systemStatus!.memory.percentage),
        ),
        _buildInfoRow(
          title: 'GPU',
          value: _systemStatus!.gpu.model,
          subtitle: 'Memória: ${_systemStatus!.gpu.memory}',
          icon: Icons.developer_board,
          status: _systemStatus!.gpu.available == true ? StatusType.success : StatusType.warning,
        ),
        _buildInfoRow(
          title: 'Armazenamento',
          value: '${_systemStatus!.storage.used} / ${_systemStatus!.storage.total}',
          subtitle: 'Utilização: ${_systemStatus!.storage.percentage.toString()}%',
          icon: Icons.storage,
          status: _getStorageStatus(_systemStatus!.storage.percentage),
        ),
        _buildInfoRow(
          title: 'Versão do Servidor',
          value: _systemStatus!.server.version,
          icon: Icons.api,
          status: _systemStatus!.server.active == true ? StatusType.success : StatusType.error,
        ),
      ],
    );
  }

  StatusType _getStorageStatus(dynamic percentage) {
    if (percentage == null) return StatusType.warning;
    
    final storagePercentage = percentage is int 
        ? percentage.toDouble() 
        : percentage is double 
            ? percentage 
            : double.tryParse(percentage.toString()) ?? 0.0;
    
    if (storagePercentage > 90) {
      return StatusType.error;
    } else if (storagePercentage > 70) {
      return StatusType.warning;
    } else {
      return StatusType.success;
    }
  }

  Widget _buildInfoRow({
    required String title,
    required String value,
    String? subtitle,
    IconData? icon,
    StatusType status = StatusType.normal,
  }) {
    final Color statusColor = status == StatusType.success
        ? AppColors.success
        : status == StatusType.warning
            ? AppColors.warning
            : status == StatusType.error
                ? AppColors.error
                : AppColors.grey;

    return Container(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.small),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: AppColors.neutralLight.withOpacity(0.2),
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          if (icon != null) ...[
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: statusColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
              ),
              child: Icon(
                icon,
                color: statusColor,
                size: 18,
              ),
            ),
            const SizedBox(width: AppSpacing.small),
          ],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: AppTypography.textTheme.bodySmall?.copyWith(
                    color: _titleColor,
                  ),
                ),
                Text(
                  value,
                  style: AppTypography.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: _valueColor,
                  ),
                ),
                if (subtitle != null)
                  Text(
                    subtitle,
                    style: AppTypography.textTheme.bodySmall?.copyWith(
                      color: AppColors.grey,
                    ),
                  ),
              ],
            ),
          ),
          if (status != StatusType.normal)
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                color: statusColor,
                shape: BoxShape.circle,
              ),
            ),
        ],
      ),
    );
  }
}

enum StatusType {
  normal,
  success,
  warning,
  error,
} 