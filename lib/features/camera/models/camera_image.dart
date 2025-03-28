import 'dart:typed_data';

/// Modelo para representar uma imagem capturada pela câmera
class CameraImage {
  /// Dados binários da imagem
  final Uint8List? bytes;
  
  /// Dados binários da imagem bruta (antes do processamento)
  final Uint8List? rawBytes;
  
  /// Indica se a imagem foi processada (filtros aplicados, etc)
  final bool isProcessed;
  
  /// Timestamp da captura
  final DateTime timestamp;
  
  /// Ajustes aplicados à imagem
  final Map<String, dynamic>? adjustments;
  
  /// Configurações da câmera no momento da captura
  final Map<String, dynamic>? cameraSettings;
  
  /// Construtor
  CameraImage({
    this.bytes,
    this.rawBytes,
    this.isProcessed = false,
    DateTime? timestamp,
    this.adjustments,
    this.cameraSettings,
  }) : timestamp = timestamp ?? DateTime.now();
  
  /// Indica se a imagem tem dados válidos
  bool get hasData => bytes != null || rawBytes != null;
  
  /// Tamanho dos dados em bytes
  int get size => bytes?.length ?? rawBytes?.length ?? 0;
  
  /// Formata o tamanho para exibição amigável
  String get formattedSize {
    final kb = size / 1024;
    if (kb < 1024) {
      return '${kb.toStringAsFixed(1)} KB';
    } else {
      final mb = kb / 1024;
      return '${mb.toStringAsFixed(1)} MB';
    }
  }
  
  /// Cria uma cópia da imagem com alguns atributos modificados
  CameraImage copyWith({
    Uint8List? bytes,
    Uint8List? rawBytes,
    bool? isProcessed,
    DateTime? timestamp,
    Map<String, dynamic>? adjustments,
    Map<String, dynamic>? cameraSettings,
  }) {
    return CameraImage(
      bytes: bytes ?? this.bytes,
      rawBytes: rawBytes ?? this.rawBytes,
      isProcessed: isProcessed ?? this.isProcessed,
      timestamp: timestamp ?? this.timestamp,
      adjustments: adjustments ?? this.adjustments,
      cameraSettings: cameraSettings ?? this.cameraSettings,
    );
  }
  
  /// Aplica ajustes à imagem
  CameraImage applyAdjustments(Map<String, dynamic> newAdjustments) {
    final mergedAdjustments = {
      ...?adjustments,
      ...newAdjustments,
    };
    
    return copyWith(
      adjustments: mergedAdjustments,
      isProcessed: true,
    );
  }
  
  /// Retorna uma string formatada da timestamp
  String get formattedTimestamp {
    return '${timestamp.day.toString().padLeft(2, '0')}/'
        '${timestamp.month.toString().padLeft(2, '0')}/'
        '${timestamp.year} '
        '${timestamp.hour.toString().padLeft(2, '0')}:'
        '${timestamp.minute.toString().padLeft(2, '0')}';
  }
  
  /// Combina dados de metadados, ajustes e configurações em um único mapa
  Map<String, dynamic> toMap() {
    return {
      'timestamp': timestamp.toIso8601String(),
      'size': size,
      'isProcessed': isProcessed,
      if (adjustments != null) 'adjustments': adjustments,
      if (cameraSettings != null) 'cameraSettings': cameraSettings,
    };
  }
} 