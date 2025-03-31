import 'package:flutter/material.dart';
import 'package:toastification/toastification.dart';
import 'package:get/get.dart';

/// Classe utilitária para mostrar notificações toast de forma consistente
/// usando o pacote toastification
class AppToast {
  /// Exibe um toast de informação
  static void info(
    String title, {
    String? description,
    Duration duration = const Duration(seconds: 3),
    OverlayState? overlayState,
    BuildContext? context,
    AlignmentGeometry alignment = Alignment.topRight,
  }) {
    _showToast(
      title: title,
      description: description,
      type: ToastificationType.info,
      duration: duration,
      overlayState: overlayState,
      context: context,
      alignment: alignment,
    );
  }

  /// Exibe um toast de sucesso
  static void success(
    String title, {
    String? description,
    Duration duration = const Duration(seconds: 3),
    OverlayState? overlayState,
    BuildContext? context,
    AlignmentGeometry alignment = Alignment.topRight,
  }) {
    _showToast(
      title: title,
      description: description,
      type: ToastificationType.success,
      duration: duration,
      overlayState: overlayState,
      context: context,
      alignment: alignment,
    );
  }

  /// Exibe um toast de aviso
  static void warning(
    String title, {
    String? description,
    Duration duration = const Duration(seconds: 4),
    OverlayState? overlayState,
    BuildContext? context,
    AlignmentGeometry alignment = Alignment.topRight,
  }) {
    _showToast(
      title: title,
      description: description,
      type: ToastificationType.warning,
      duration: duration,
      overlayState: overlayState,
      context: context,
      alignment: alignment,
    );
  }

  /// Exibe um toast de erro
  static void error(
    String title, {
    String? description,
    Duration duration = const Duration(seconds: 5),
    OverlayState? overlayState,
    BuildContext? context,
    AlignmentGeometry alignment = Alignment.topRight,
  }) {
    _showToast(
      title: title,
      description: description,
      type: ToastificationType.error,
      duration: duration,
      overlayState: overlayState,
      context: context, 
      alignment: alignment,
    );
  }

  /// Método privado para exibir o toast com configurações padronizadas
  static void _showToast({
    required String title,
    String? description,
    required ToastificationType type,
    required Duration duration,
    OverlayState? overlayState,
    BuildContext? context,
    AlignmentGeometry alignment = Alignment.topRight,
  }) {
    // Cria instância do toastification
    final toastification = Toastification();
    
    // Obter o contexto preferencialmente do parâmetro, ou usar o GetX como fallback
    if (context == null && overlayState == null) {
      if (Get.context != null) {
        context = Get.context;
      } else if (Get.overlayContext != null) {
        context = Get.overlayContext;
      } else if (Get.key.currentContext != null) {
        context = Get.key.currentContext;
      }
    }

    final Widget titleWidget = Text(
      title,
      style: const TextStyle(
        fontWeight: FontWeight.bold,
        fontSize: 14,
      ),
    );

    final Widget? descriptionWidget = description != null
        ? Text(
            description,
            style: const TextStyle(
              fontSize: 12,
            ),
          )
        : null;

    if (context != null) {
      toastification.show(
        context: context,
        title: titleWidget,
        description: descriptionWidget,
        type: type,
        style: ToastificationStyle.fillColored,
        autoCloseDuration: duration,
        alignment: alignment,
        animationDuration: const Duration(milliseconds: 300),
        showProgressBar: true,
        dragToClose: true,
        closeOnClick: true,
        pauseOnHover: true,
        borderRadius: BorderRadius.circular(8),
      );
    } else if (overlayState != null) {
      toastification.show(
        overlayState: overlayState,
        title: titleWidget,
        description: descriptionWidget,
        type: type,
        style: ToastificationStyle.fillColored,
        autoCloseDuration: duration,
        alignment: alignment,
        animationDuration: const Duration(milliseconds: 300),
        showProgressBar: true,
        dragToClose: true,
        closeOnClick: true,
        pauseOnHover: true,
        borderRadius: BorderRadius.circular(8),
      );
    }
  }
  
  /// Limpa todos os toasts atualmente visíveis
  static void dismissAll() {
    toastification.dismissAll();
  }
} 