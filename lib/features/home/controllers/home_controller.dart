import 'dart:async';

import 'package:get/get.dart';
import 'package:flutter/material.dart';
import 'package:microdetect/core/models/system_status_model.dart';
import 'package:microdetect/core/services/system_status_service.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/features/shared/events/screen_events.dart';
import 'package:microdetect/features/shared/events/event_manager.dart';
import '../../../design_system/app_toast.dart';

class HomeController extends GetxController {
  // Serviços injetados
  final SystemStatusService systemStatusService;

  // Estado observável
  var isLoading = false.obs;
  var systemStatus = SystemStatusModel.defaultStatus().obs;

  // Gerenciamento de eventos usando o novo EventManager
  final List<String> _registeredEvents = [];
  
  // Controle de debounce para evitar múltiplos refreshes
  DateTime? _lastRefreshTime;
  final _refreshDebounceTime = const Duration(seconds: 2);

  HomeController({
    required this.systemStatusService,
  });

  @override
  void onInit() {
    super.onInit();
    fetchSystemStatus();
    _setupEventListeners();
  }

  @override
  void onClose() {
    // Limpar os listeners ao fechar o controller
    _unregisterEventListeners();
    super.onClose();
  }

  // Configurar listeners para eventos
  void _setupEventListeners() {
    // Registrar handler para o evento de refresh
    _registerEventListener(ScreenEvents.refresh, _handleRefreshEvent);
    
    // Registrar handler para o evento de ajuda
    _registerEventListener(ScreenEvents.showHelp, _handleHelpEvent);
  }
  
  // Registrar um listener e armazenar o tipo para limpeza futura
  void _registerEventListener(String eventType, Function(ScreenEvent) handler) {
    Get.events.addListener(eventType, handler);
    _registeredEvents.add(eventType);
  }
  
  // Cancelar todos os listeners registrados
  void _unregisterEventListeners() {
    for (final eventType in _registeredEvents) {
      Get.events.removeAllListenersForType(eventType);
    }
    _registeredEvents.clear();
  }
  
  // Handler para o evento de refresh
  void _handleRefreshEvent(ScreenEvent event) {
    // Aplicar debounce para evitar múltiplos refreshes
    final now = DateTime.now();
    if (_lastRefreshTime == null ||
        now.difference(_lastRefreshTime!) > _refreshDebounceTime) {
      _lastRefreshTime = now;
      refreshDashboard();
    }
  }
  
  // Handler para o evento de ajuda
  void _handleHelpEvent(ScreenEvent event) {
    showHelpDialog();
  }

  /// Buscar status do sistema a partir da API
  Future<void> fetchSystemStatus() async {
    isLoading.value = true;

    try {
      final statusData = await systemStatusService.getSystemStatus();
      systemStatus.value = statusData;
    } catch (e) {
      AppToast.error(
        'Erro',
        description: 'Erro ao carregar status do sistema: $e',
      );

      systemStatus.value = SystemStatusModel.defaultStatus();
    } finally {
      isLoading.value = false;
    }
  }

  /// Atualizar os dados do dashboard
  void refreshDashboard() async {
    isLoading.value = true;

    await fetchSystemStatus();

    AppToast.success(
      'Sucesso',
      description: 'Dashboard atualizado com sucesso!',
      duration: const Duration(seconds: 2),
    );
  }

  /// Exibir diálogo de ajuda para a tela inicial
  void showHelpDialog() {
    final isDark = Get.isDarkMode;
    final textColor = isDark ? AppColors.white : AppColors.neutralDarkest;

    Get.dialog(
      AlertDialog(
        title: Text(
          'Ajuda - Painel de Controle',
          style:
              AppTypography.titleLarge(Get.context!).copyWith(color: textColor),
        ),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildHelpSection('Visão Geral',
                  'O Painel de Controle fornece uma visão geral do sistema MicroDetect.'),
              SizedBox(height: AppSpacing.small),
              _buildHelpSection('Métricas',
                  'Mostra estatísticas gerais como número de datasets, modelos treinados, etc.'),
              SizedBox(height: AppSpacing.small),
              _buildHelpSection('Datasets Recentes',
                  'Lista os datasets mais recentemente acessados ou criados.'),
              SizedBox(height: AppSpacing.small),
              _buildHelpSection('Atividades Recentes',
                  'Exibe ações recentes realizadas no sistema.'),
              SizedBox(height: AppSpacing.small),
              _buildHelpSection('Status do Sistema',
                  'Mostra informações sobre GPU, armazenamento e outros recursos.'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: Text(
              'Fechar',
              style: AppTypography.labelMedium(Get.context!)
                  .copyWith(color: AppColors.primary),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHelpSection(String title, String content) {
    final isDark = Get.isDarkMode;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: AppTypography.bodyMedium(Get.context!).copyWith(
            fontWeight: FontWeight.bold,
            color: AppColors.primary,
          ),
        ),
        SizedBox(height: AppSpacing.xxSmall),
        Text(
          content,
          style: AppTypography.bodySmall(Get.context!).copyWith(
            color: isDark ? AppColors.neutralLight : AppColors.neutralDark,
          ),
        ),
      ],
    );
  }
}
