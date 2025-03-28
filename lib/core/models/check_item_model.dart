// lib/core/models/check_item_model.dart
// Modelo para representar um item de verificação/step com seu status

import '../enums/backend_status_enum.dart';

// Classe para representar um item de verificação
class CheckItem {
  final String title;       // Título ou descrição do item
  final CheckStatus status; // Status atual do item
  final String? message;    // Mensagem adicional opcional (como detalhes ou erro)

  const CheckItem({
    required this.title,
    required this.status,
    this.message,
  });

  // Cria uma cópia do item com novos valores
  CheckItem copyWith({
    String? title,
    CheckStatus? status,
    String? message,
  }) {
    return CheckItem(
      title: title ?? this.title,
      status: status ?? this.status,
      message: message ?? this.message,
    );
  }

  // Converte para string para debug
  @override
  String toString() => 'CheckItem(title: $title, status: $status, message: $message)';
}