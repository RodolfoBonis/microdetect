import 'package:flutter/material.dart';

/// Representa um item do menu lateral
class SidebarItem {
  /// Ícone do item
  final IconData icon;
  
  /// Rótulo do item
  final String label;
  
  /// Rota associada ao item
  final String route;
  
  /// Construtor padrão
  const SidebarItem({
    required this.icon,
    required this.label,
    required this.route,
  });
} 