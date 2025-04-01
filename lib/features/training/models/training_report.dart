import 'package:intl/intl.dart';

/// Modelo para relatório completo de treinamento
class TrainingReport {
  /// ID único do relatório
  final int id;

  /// ID da sessão de treinamento relacionada
  final int trainingSessionId;

  /// Nome do modelo treinado
  final String modelName;

  /// ID do dataset usado
  final int datasetId;

  /// Histórico de métricas durante o treinamento
  final List<TrainingMetrics> metricsHistory;

  /// Matriz de confusão para avaliação
  final List<List<int>> confusionMatrix;

  /// Desempenho por classe
  final List<ClassPerformance> classPerformance;

  /// Métricas finais do modelo
  final Map<String, dynamic> finalMetrics;

  /// Uso médio de recursos
  final ResourceUsage resourceUsageAvg;

  /// Uso máximo de recursos
  final ResourceUsage resourceUsageMax;

  /// Hiperparâmetros utilizados
  final Map<String, dynamic> hyperparameters;

  /// Número de imagens usadas para treino
  final int trainImagesCount;

  /// Número de imagens usadas para validação
  final int valImagesCount;

  /// Número de imagens usadas para teste
  final int testImagesCount;

  /// Tempo total de treinamento em segundos
  final int trainingTimeSeconds;

  /// Tamanho do modelo em MB
  final double modelSizeMb;

  /// Data de criação do relatório
  final DateTime createdAt;

  /// Construtor
  TrainingReport({
    required this.id,
    required this.trainingSessionId,
    required this.modelName,
    required this.datasetId,
    required this.metricsHistory,
    required this.confusionMatrix,
    required this.classPerformance,
    required this.finalMetrics,
    required this.resourceUsageAvg,
    required this.resourceUsageMax,
    required this.hyperparameters,
    required this.trainImagesCount,
    required this.valImagesCount,
    required this.testImagesCount,
    required this.trainingTimeSeconds,
    required this.modelSizeMb,
    required this.createdAt,
  });

  /// Cria uma instância a partir de JSON
  factory TrainingReport.fromJson(Map<String, dynamic> json) {
    return TrainingReport(
      id: json['id'],
      trainingSessionId: json['training_session_id'],
      modelName: json['model_name'],
      datasetId: json['dataset_id'],
      metricsHistory: json['metrics_history'] != null
          ? List<Map<String, dynamic>>.from(json['metrics_history'])
          .map((m) => TrainingMetrics.fromJson(m)).toList()
          : [],
      confusionMatrix: json['confusion_matrix'] != null
          ? List<List<int>>.from(json['confusion_matrix']
          .map((row) => List<int>.from(row)))
          : [],
      classPerformance: json['class_performance'] != null
          ? List<Map<String, dynamic>>.from(json['class_performance'])
          .map((c) => ClassPerformance.fromJson(c)).toList()
          : [],
      finalMetrics: json['final_metrics'] ?? {},
      resourceUsageAvg: ResourceUsage.fromJson(json['resource_usage_avg'] ?? {}),
      resourceUsageMax: ResourceUsage.fromJson(json['resource_usage_max'] ?? {}),
      hyperparameters: json['hyperparameters'] ?? {},
      trainImagesCount: json['train_images_count'] ?? 0,
      valImagesCount: json['val_images_count'] ?? 0,
      testImagesCount: json['test_images_count'] ?? 0,
      trainingTimeSeconds: json['training_time_seconds'] ?? 0,
      modelSizeMb: json['model_size_mb'] ?? 0.0,
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  /// Converte para JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'training_session_id': trainingSessionId,
      'model_name': modelName,
      'dataset_id': datasetId,
      'metrics_history': metricsHistory.map((m) => m.toJson()).toList(),
      'confusion_matrix': confusionMatrix,
      'class_performance': classPerformance.map((c) => c.toJson()).toList(),
      'final_metrics': finalMetrics,
      'resource_usage_avg': resourceUsageAvg.toJson(),
      'resource_usage_max': resourceUsageMax.toJson(),
      'hyperparameters': hyperparameters,
      'train_images_count': trainImagesCount,
      'val_images_count': valImagesCount,
      'test_images_count': testImagesCount,
      'training_time_seconds': trainingTimeSeconds,
      'model_size_mb': modelSizeMb,
      'created_at': DateFormat('yyyy-MM-ddTHH:mm:ss').format(createdAt),
    };
  }

  /// Formata o tempo de treinamento em formato legível
  String get trainingTimeFormatted {
    final hours = trainingTimeSeconds ~/ 3600;
    final minutes = (trainingTimeSeconds % 3600) ~/ 60;
    final seconds = trainingTimeSeconds % 60;

    if (hours > 0) {
      return '$hours h $minutes min $seconds s';
    } else if (minutes > 0) {
      return '$minutes min $seconds s';
    } else {
      return '$seconds s';
    }
  }

  /// Formata a data de criação para exibição
  String get createdAtFormatted {
    return DateFormat('dd/MM/yyyy HH:mm').format(createdAt);
  }

  /// Obtém o tamanho do modelo formatado
  String get modelSizeFormatted {
    if (modelSizeMb >= 1024) {
      return '${(modelSizeMb / 1024).toStringAsFixed(2)} GB';
    } else {
      return '${modelSizeMb.toStringAsFixed(2)} MB';
    }
  }

  /// Obtém o mAP50 final
  double get map50 {
    return finalMetrics['map50'] ?? 0.0;
  }

  /// Obtém a precisão média
  double get precision {
    return finalMetrics['precision'] ?? 0.0;
  }

  /// Obtém o recall médio
  double get recall {
    return finalMetrics['recall'] ?? 0.0;
  }

  /// Obtém o F1-Score médio
  double get f1Score {
    if (precision <= 0 || recall <= 0) return 0.0;
    return 2 * precision * recall / (precision + recall);
  }

  /// Total de imagens utilizadas
  int get totalImages {
    return trainImagesCount + valImagesCount + testImagesCount;
  }
}

/// Modelo para métricas coletadas durante o treinamento
class TrainingMetrics {
  /// Número da época
  final int epoch;

  /// Valor da função de perda
  final double loss;

  /// Valor da função de perda na validação
  final double? valLoss;

  /// mAP50 (Mean Average Precision com IoU threshold de 0.5)
  final double? map50;

  /// mAP (Mean Average Precision com IoU médio de 0.5 a 0.95)
  final double? map;

  /// Precisão
  final double? precision;

  /// Recall
  final double? recall;

  /// Uso de recursos computacionais
  final ResourceUsage? resources;

  /// Construtor
  TrainingMetrics({
    required this.epoch,
    required this.loss,
    this.valLoss,
    this.map50,
    this.map,
    this.precision,
    this.recall,
    this.resources,
  });

  /// Cria uma instância a partir de JSON
  factory TrainingMetrics.fromJson(Map<String, dynamic> json) {
    return TrainingMetrics(
      epoch: json['epoch'] ?? 0,
      loss: json['loss'] ?? 0.0,
      valLoss: json['val_loss'],
      map50: json['map50'],
      map: json['map'],
      precision: json['precision'],
      recall: json['recall'],
      resources: json['resources'] != null
          ? ResourceUsage.fromJson(json['resources'])
          : null,
    );
  }

  /// Converte para JSON
  Map<String, dynamic> toJson() {
    return {
      'epoch': epoch,
      'loss': loss,
      'val_loss': valLoss,
      'map50': map50,
      'map': map,
      'precision': precision,
      'recall': recall,
      'resources': resources?.toJson(),
    };
  }
}

/// Modelo para uso de recursos computacionais
class ResourceUsage {
  /// Porcentagem de uso de CPU
  final double cpuPercent;

  /// Porcentagem de uso de memória RAM
  final double memoryPercent;

  /// Porcentagem de uso de GPU (opcional)
  final double? gpuPercent;

  /// Porcentagem de uso de memória de GPU (opcional)
  final double? gpuMemoryPercent;

  /// Construtor
  ResourceUsage({
    required this.cpuPercent,
    required this.memoryPercent,
    this.gpuPercent,
    this.gpuMemoryPercent,
  });

  /// Cria uma instância a partir de JSON
  factory ResourceUsage.fromJson(Map<String, dynamic> json) {
    return ResourceUsage(
      cpuPercent: json['cpu_percent'] ?? 0.0,
      memoryPercent: json['memory_percent'] ?? 0.0,
      gpuPercent: json['gpu_percent'],
      gpuMemoryPercent: json['gpu_memory_percent'],
    );
  }

  /// Converte para JSON
  Map<String, dynamic> toJson() {
    return {
      'cpu_percent': cpuPercent,
      'memory_percent': memoryPercent,
      'gpu_percent': gpuPercent,
      'gpu_memory_percent': gpuMemoryPercent,
    };
  }

  /// Verifica se GPU foi utilizada
  bool get hasGpuUsage => gpuPercent != null && gpuMemoryPercent != null;
}

/// Modelo para desempenho por classe
class ClassPerformance {
  /// ID da classe
  final int classId;

  /// Nome da classe
  final String className;

  /// Precisão da classe
  final double precision;

  /// Recall da classe
  final double recall;

  /// F1-Score da classe
  final double f1Score;

  /// Número de exemplos no conjunto de validação/teste
  final int support;

  /// Número total de exemplos desta classe
  final int examplesCount;

  /// Construtor
  ClassPerformance({
    required this.classId,
    required this.className,
    required this.precision,
    required this.recall,
    required this.f1Score,
    required this.support,
    required this.examplesCount,
  });

  /// Cria uma instância a partir de JSON
  factory ClassPerformance.fromJson(Map<String, dynamic> json) {
    return ClassPerformance(
      classId: json['class_id'],
      className: json['class_name'],
      precision: json['precision'] ?? 0.0,
      recall: json['recall'] ?? 0.0,
      f1Score: json['f1_score'] ?? 0.0,
      support: json['support'] ?? 0,
      examplesCount: json['examples_count'] ?? 0,
    );
  }

  /// Converte para JSON
  Map<String, dynamic> toJson() {
    return {
      'class_id': classId,
      'class_name': className,
      'precision': precision,
      'recall': recall,
      'f1_score': f1Score,
      'support': support,
      'examples_count': examplesCount,
    };
  }

  /// Retorna a precisão formatada como porcentagem
  String get precisionFormatted => '${(precision * 100).toStringAsFixed(1)}%';

  /// Retorna o recall formatado como porcentagem
  String get recallFormatted => '${(recall * 100).toStringAsFixed(1)}%';

  /// Retorna o F1-Score formatado como porcentagem
  String get f1ScoreFormatted => '${(f1Score * 100).toStringAsFixed(1)}%';
}