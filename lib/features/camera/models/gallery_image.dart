import 'dart:typed_data';
import 'package:microdetect/features/annotation/models/annotation.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';
import 'package:intl/intl.dart';

/// Classe para representar uma imagem na galeria
class GalleryImage {
  /// ID único da imagem no backend
  final int id;

  /// Nome do arquivo
  final String fileName;

  /// Caminho relativo do arquivo no backend
  final String? filePath;

  /// URL completa para acesso à imagem
  final String url;

  /// Largura da imagem em pixels
  final int width;

  /// Altura da imagem em pixels
  final int height;

  /// Dados da imagem em memória (nullable, só disponível após o carregamento)
  final Uint8List? bytes;

  /// Data de criação da imagem
  final DateTime createdAt;

  /// Data de atualização da imagem
  final DateTime updatedAt;

  /// Tamanho do arquivo em bytes
  final int fileSize;

  /// ID do dataset primário associado à imagem (se houver)
  final int? datasetId;

  /// Lista de datasets associados à imagem
  final List<DatasetSummary> datasets;

  final List<Annotation> annotations;

  /// Metadados adicionais da imagem
  final Map<String, dynamic>? imageMetadata;

  /// Flag indicando se a imagem está carregada em memória
  bool get isLoaded => bytes != null;

  /// Verifica se a imagem pertence a pelo menos um dataset
  bool get hasDatasets => datasets.isNotEmpty;

  /// Retorna os nomes dos datasets formatados em uma string
  String get datasetNames => datasets.isNotEmpty
      ? datasets.map((d) => d.name).join(', ')
      : 'Nenhum dataset';

  /// Tamanho formatado para exibição
  String get formattedSize {
    final kb = fileSize / 1024;
    if (kb < 1024) {
      return '${kb.toStringAsFixed(1)} KB';
    } else {
      final mb = kb / 1024;
      return '${mb.toStringAsFixed(1)} MB';
    }
  }

  /// Data formatada para exibição
  String get formattedDate {
    final dateFormat = DateFormat('dd/MM/yyyy HH:mm');
    return dateFormat.format(createdAt);
  }

  GalleryImage({
    required this.id,
    required this.fileName,
    this.filePath,
    required this.url,
    this.width = 0,
    this.height = 0,
    DateTime? createdAt,
    DateTime? updatedAt,
    this.fileSize = 0,
    this.datasetId,
    this.datasets = const [],
    this.annotations = const [],
    this.imageMetadata,
    this.bytes,
  }) :
        createdAt = createdAt ?? DateTime.now(),
        updatedAt = updatedAt ?? DateTime.now();

  /// Cria uma instância a partir de um mapa JSON
  factory GalleryImage.fromJson(Map<String, dynamic> json) {
    // Processar a lista de datasets
    List<DatasetSummary> datasetsList = [];
    if (json['datasets'] != null) {
      datasetsList = (json['datasets'] as List)
          .map((dataset) => DatasetSummary.fromJson(dataset))
          .toList();
    }

    List<Annotation> annotationsList = [];
    if (json['annotations'] != null) {
      annotationsList = (json['annotations'] as List)
          .map((annotation) => Annotation.fromJson(annotation))
          .toList();
    }

    return GalleryImage(
      id: json['id'] ?? 0,
      fileName: json['file_name'] ?? 'Sem nome',
      filePath: json['file_path'],
      url: json['url'] ?? '',
      width: json['width'] ?? 0,
      height: json['height'] ?? 0,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'])
          : DateTime.now(),
      fileSize: json['file_size'] ?? 0,
      datasetId: json['dataset_id'],
      datasets: datasetsList,
      annotations: annotationsList,
      imageMetadata: json['image_metadata'],
      bytes: json['bytes'],
    );
  }

  /// Converte para JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'file_name': fileName,
      'file_path': filePath,
      'url': url,
      'width': width,
      'height': height,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'file_size': fileSize,
      'dataset_id': datasetId,
      'datasets': datasets.map((d) => d.toJson()).toList(),
      'annotations': annotations.map((a) => a.toJson()).toList(),
      'image_metadata': imageMetadata,
    };
  }
}