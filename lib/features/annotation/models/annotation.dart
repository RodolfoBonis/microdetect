import 'dart:convert';

/// Representa uma anotação de bounding box para um objeto em uma imagem
class Annotation {
  final int? id;
  final int? imageId;
  final int? datasetId;
  final int? classId;
  final String? className;
  final double x; // Coordenada x do canto superior esquerdo (normalizada de 0 a 1)
  final double y; // Coordenada y do canto superior esquerdo (normalizada de 0 a 1)
  final double width; // Largura da bounding box (normalizada de 0 a 1)
  final double height; // Altura da bounding box (normalizada de 0 a 1)
  final double? confidence; // Confiança da detecção (de 0 a 1)
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final int? colorValue; // Valor de cor para visualização

  Annotation({
    this.id,
    this.imageId,
    this.datasetId,
    this.classId,
    this.className,
    required this.x,
    required this.y,
    required this.width,
    required this.height,
    this.confidence,
    this.createdAt,
    this.updatedAt,
    this.colorValue,
  });

  // Criar uma cópia da anotação com possíveis alterações
  Annotation copyWith({
    int? id,
    int? imageId,
    int? datasetId,
    int? classId,
    String? className,
    double? x,
    double? y,
    double? width,
    double? height,
    double? confidence,
    DateTime? createdAt,
    DateTime? updatedAt,
    int? colorValue,
  }) {
    return Annotation(
      id: id ?? this.id,
      imageId: imageId ?? this.imageId,
      datasetId: datasetId ?? this.datasetId,
      classId: classId ?? this.classId,
      className: className ?? this.className,
      x: x ?? this.x,
      y: y ?? this.y,
      width: width ?? this.width,
      height: height ?? this.height,
      confidence: confidence ?? this.confidence,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      colorValue: colorValue ?? this.colorValue,
    );
  }

  // Converter objeto JSON para Annotation
  factory Annotation.fromJson(Map<String, dynamic> json) {
    return Annotation(
      id: json['id'],
      imageId: json['image_id'],
      datasetId: json['dataset_id'],
      className: json['class_name'],
      x: json['x']?.toDouble() ?? 0.0,
      y: json['y']?.toDouble() ?? 0.0,
      width: json['width']?.toDouble() ?? 0.0,
      height: json['height']?.toDouble() ?? 0.0,
      confidence: json['confidence']?.toDouble(),
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : null,
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'])
          : null,
      colorValue: json['color_value'],
    );
  }

  // Converter Annotation para objeto JSON
  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      if (imageId != null) 'image_id': imageId,
      if (datasetId != null) 'dataset_id': datasetId,
      if (className != null) 'class_name': className,
      'x': x,
      'y': y,
      'width': width,
      'height': height,
      if (confidence != null) 'confidence': confidence,
      if (colorValue != null) 'color_value': colorValue,
    };
  }

  // Converter Annotation para formato YOLO
  // O formato YOLO é: class_id x_center y_center width height
  // Onde todas as coordenadas são normalizadas entre 0 e 1
  String toYoloFormat() {
    // Converter para coordenadas do centro
    final double xCenter = x + (width / 2);
    final double yCenter = y + (height / 2);

    return '$classId $xCenter $yCenter $width $height';
  }

  // Converter formato YOLO para Annotation
  static Annotation fromYoloFormat(String yoloString, {int? imageId, int? datasetId}) {
    final List<String> parts = yoloString.trim().split(' ');
    if (parts.length < 5) {
      throw FormatException('Formato YOLO inválido: $yoloString');
    }

    final int classId = int.parse(parts[0]);
    final double xCenter = double.parse(parts[1]);
    final double yCenter = double.parse(parts[2]);
    final double width = double.parse(parts[3]);
    final double height = double.parse(parts[4]);

    // Converter de coordenadas do centro para coordenadas do canto superior esquerdo
    final double x = xCenter - (width / 2);
    final double y = yCenter - (height / 2);

    double? confidence;
    if (parts.length > 5) {
      confidence = double.parse(parts[5]);
    }

    return Annotation(
      imageId: imageId,
      datasetId: datasetId,
      classId: classId,
      x: x,
      y: y,
      width: width,
      height: height,
      confidence: confidence,
    );
  }

  @override
  String toString() {
    return 'Annotation{id: $id, classId: $classId, className: $className, x: $x, y: $y, width: $width, height: $height, confidence: $confidence}';
  }
}

/// Modelo para armazenar uma imagem com suas anotações
class AnnotatedImage {
  final int id;
  final String fileName;
  final String url;
  final String? filePath; // Caminho do arquivo no sistema (pode ser o mesmo que url)
  final int? datasetId;
  final int width;
  final int height;
  final List<Annotation> annotations;
  
  const AnnotatedImage({
    required this.id,
    required this.fileName,
    required this.url,
    this.filePath,
    this.datasetId,
    required this.width,
    required this.height,
    this.annotations = const [],
  });
  
  /// Cria uma cópia da imagem com possíveis alterações
  AnnotatedImage copyWith({
    int? id,
    String? fileName,
    String? url,
    String? filePath,
    int? datasetId,
    int? width,
    int? height,
    List<Annotation>? annotations,
  }) {
    return AnnotatedImage(
      id: id ?? this.id,
      fileName: fileName ?? this.fileName,
      url: url ?? this.url,
      filePath: filePath ?? this.filePath,
      datasetId: datasetId ?? this.datasetId,
      width: width ?? this.width,
      height: height ?? this.height,
      annotations: annotations ?? this.annotations,
    );
  }
  
  factory AnnotatedImage.fromJson(Map<String, dynamic> json) {
    List<Annotation> annotations = [];
    if (json['annotations'] != null) {
      annotations = (json['annotations'] as List)
          .map((e) => Annotation.fromJson(e))
          .toList();
    }
    
    // Usar file_path se disponível ou fazer fallback para url
    String url = json['url'] ?? '';
    String? filePath = json['file_path'];
    
    // Se não tiver filePath, mas tiver url, usar url como filePath
    if (filePath == null && url.isNotEmpty) {
      filePath = url;
    }
    
    return AnnotatedImage(
      id: json['id'],
      fileName: json['file_name'],
      url: url,
      filePath: filePath,
      datasetId: json['dataset_id'],
      width: json['width'] ?? 0,
      height: json['height'] ?? 0,
      annotations: annotations,
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'file_name': fileName,
      'url': url,
      'file_path': filePath ?? url,
      'dataset_id': datasetId,
      'width': width,
      'height': height,
      'annotations': annotations.map((e) => e.toJson()).toList(),
    };
  }
} 