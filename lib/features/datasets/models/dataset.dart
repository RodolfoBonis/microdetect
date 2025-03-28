import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:intl/intl.dart';

/// Classe simplificada que representa um dataset para uso em listas e sumários
class DatasetSummary {
  /// ID único do dataset
  final int id;

  /// Nome do dataset
  final String name;

  /// Descrição do dataset (opcional)
  final String? description;

  const DatasetSummary({
    required this.id,
    required this.name,
    this.description,
  });

  /// Cria uma instância a partir de um mapa JSON
  factory DatasetSummary.fromJson(Map<String, dynamic> json) {
    return DatasetSummary(
      id: json['id'],
      name: json['name'],
      description: json['description'],
    );
  }

  /// Converte para JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
    };
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is DatasetSummary &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// Classe que representa um conjunto de dados (dataset) para treinamento de modelos
class Dataset {
  /// ID único do dataset
  final int id;

  /// Nome do dataset
  final String name;

  /// Descrição do dataset (opcional)
  final String? description;

  /// Data de criação do dataset
  final DateTime createdAt;

  /// Data da última atualização do dataset
  final DateTime updatedAt;

  /// Número de imagens no dataset
  final int imagesCount;

  /// Lista de classes de objetos que o dataset pode conter
  final List<String> classes;

  /// Número de anotações no dataset (objetos marcados nas imagens)
  final int? annotationsCount;

  /// Dados estatísticos do dataset
  final Map<String, dynamic>? statistics;

  const Dataset({
    required this.id,
    required this.name,
    this.description,
    required this.createdAt,
    required this.updatedAt,
    required this.imagesCount,
    this.classes = const [],
    this.annotationsCount,
    this.statistics,
  });

  /// Converte para uma versão resumida (DatasetSummary)
  DatasetSummary toSummary() {
    return DatasetSummary(
      id: id,
      name: name,
      description: description,
    );
  }

  /// Data de criação formatada para exibição
  String get formattedCreatedAt {
    return DateFormat('dd/MM/yyyy - HH:mm').format(createdAt);
  }

  /// Data de atualização formatada para exibição
  String get formattedUpdatedAt {
    return DateFormat('dd/MM/yyyy - HH:mm').format(updatedAt);
  }

  /// Cria uma instância a partir de um mapa JSON
  factory Dataset.fromJson(Map<String, dynamic> json) {
    return Dataset(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      imagesCount: json['images_count'] ?? 0,
      classes: json['classes'] != null
          ? List<String>.from(json['classes'])
          : [],
      annotationsCount: json['annotations_count'],
      statistics: json['statistics'],
    );
  }

  /// Converte para JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'images_count': imagesCount,
      'classes': classes,
      'annotations_count': annotationsCount,
      'statistics': statistics,
    };
  }

  /// Cria uma cópia do dataset com valores atualizados
  Dataset copyWith({
    int? id,
    String? name,
    String? description,
    List<String>? classes,
    DateTime? createdAt,
    DateTime? updatedAt,
    int? imagesCount,
    int? annotationsCount,
    Map<String, dynamic>? statistics,
  }) {
    return Dataset(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      imagesCount: imagesCount ?? this.imagesCount,
      classes: classes ?? this.classes,
      annotationsCount: annotationsCount ?? this.annotationsCount,
      statistics: statistics ?? this.statistics,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Dataset &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;
} 