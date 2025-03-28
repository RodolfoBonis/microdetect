import 'dart:convert';

/// Modelo que representa estatísticas detalhadas de um dataset
class DatasetStatistics {
  /// Número total de imagens no dataset
  final int totalImages;
  
  /// Número total de anotações (objetos marcados) no dataset
  final int totalAnnotations;
  
  /// Número de imagens que têm pelo menos uma anotação
  final int annotatedImages;
  
  /// Número de imagens sem nenhuma anotação
  final int unannotatedImages;
  
  /// Tamanho médio das imagens em pixels (largura x altura)
  final Map<String, dynamic>? averageImageSize;
  
  /// Distribuição de tamanhos de objetos anotados (pequeno, médio, grande)
  final Map<String, int>? objectSizeDistribution;
  
  /// Desbalanceamento entre classes (quanto maior, mais desbalanceado)
  final double? classImbalance;
  
  /// Número médio de objetos por imagem
  final double? averageObjectsPerImage;
  
  /// Densidade média de objetos (objetos por área de imagem)
  final double? averageObjectDensity;
  
  /// Último cálculo das estatísticas (timestamp)
  final DateTime? lastCalculated;
  
  /// Contagem detalhada por classe
  final Map<String, int>? classCounts;
  
  /// Dados extras específicos da aplicação
  final Map<String, dynamic>? extraData;

  const DatasetStatistics({
    required this.totalImages,
    required this.totalAnnotations,
    required this.annotatedImages,
    required this.unannotatedImages,
    this.averageImageSize,
    this.objectSizeDistribution,
    this.classImbalance,
    this.averageObjectsPerImage,
    this.averageObjectDensity,
    this.lastCalculated,
    this.classCounts,
    this.extraData,
  });

  /// Cria uma instância a partir de um mapa JSON
  factory DatasetStatistics.fromJson(Map<String, dynamic> json) {
    return DatasetStatistics(
      totalImages: json['total_images'] ?? 0,
      totalAnnotations: json['total_annotations'] ?? 0,
      annotatedImages: json['annotated_images'] ?? 0,
      unannotatedImages: json['unannotated_images'] ?? 0,
      averageImageSize: json['average_image_size'],
      objectSizeDistribution: json['object_size_distribution'] != null
          ? Map<String, int>.from(json['object_size_distribution'])
          : null,
      classImbalance: json['class_imbalance']?.toDouble(),
      averageObjectsPerImage: json['average_objects_per_image']?.toDouble(),
      averageObjectDensity: json['average_object_density']?.toDouble(),
      lastCalculated: json['last_calculated'] != null
          ? DateTime.parse(json['last_calculated'])
          : null,
      classCounts: json['class_counts'] != null
          ? Map<String, int>.from(json['class_counts'])
          : null,
      extraData: json['extra_data'],
    );
  }

  /// Converte para JSON
  Map<String, dynamic> toJson() {
    return {
      'total_images': totalImages,
      'total_annotations': totalAnnotations,
      'annotated_images': annotatedImages,
      'unannotated_images': unannotatedImages,
      'average_image_size': averageImageSize,
      'object_size_distribution': objectSizeDistribution,
      'class_imbalance': classImbalance,
      'average_objects_per_image': averageObjectsPerImage,
      'average_object_density': averageObjectDensity,
      'last_calculated': lastCalculated?.toIso8601String(),
      'class_counts': classCounts,
      'extra_data': extraData,
    };
  }

  /// Cria uma cópia do objeto com propriedades atualizadas
  DatasetStatistics copyWith({
    int? totalImages,
    int? totalAnnotations,
    int? annotatedImages,
    int? unannotatedImages,
    Map<String, dynamic>? averageImageSize,
    Map<String, int>? objectSizeDistribution,
    double? classImbalance,
    double? averageObjectsPerImage,
    double? averageObjectDensity,
    DateTime? lastCalculated,
    Map<String, int>? classCounts,
    Map<String, dynamic>? extraData,
  }) {
    return DatasetStatistics(
      totalImages: totalImages ?? this.totalImages,
      totalAnnotations: totalAnnotations ?? this.totalAnnotations,
      annotatedImages: annotatedImages ?? this.annotatedImages,
      unannotatedImages: unannotatedImages ?? this.unannotatedImages,
      averageImageSize: averageImageSize ?? this.averageImageSize,
      objectSizeDistribution: objectSizeDistribution ?? this.objectSizeDistribution,
      classImbalance: classImbalance ?? this.classImbalance,
      averageObjectsPerImage: averageObjectsPerImage ?? this.averageObjectsPerImage,
      averageObjectDensity: averageObjectDensity ?? this.averageObjectDensity,
      lastCalculated: lastCalculated ?? this.lastCalculated,
      classCounts: classCounts ?? this.classCounts,
      extraData: extraData ?? this.extraData,
    );
  }

  /// Converte para string JSON
  String toJsonString() => jsonEncode(toJson());

  @override
  String toString() {
    return 'DatasetStatistics{totalImages: $totalImages, totalAnnotations: $totalAnnotations, '
        'annotatedImages: $annotatedImages, unannotatedImages: $unannotatedImages}';
  }
} 