import 'package:intl/intl.dart';

/// Modelo de dados para uma sessão de treinamento
class TrainingSession {
  /// ID único da sessão
  final int id;

  /// Nome da sessão de treinamento
  final String name;

  /// Descrição detalhada do treinamento
  final String description;

  /// Estado atual: 'pending', 'running', 'completed', 'failed', 'paused'
  final String status;

  /// Tipo de modelo (ex: 'yolov8')
  final String modelType;

  /// Versão do modelo (ex: 'n', 's', 'm', 'l', 'x')
  final String modelVersion;

  /// ID do dataset usado para treinamento
  final int datasetId;

  /// Hiperparâmetros usados para o treinamento
  final Map<String, dynamic> hyperparameters;

  /// Métricas atuais/finais do treinamento
  final Map<String, dynamic>? metrics;

  /// Data de criação da sessão
  final DateTime createdAt;

  /// Data de início do treinamento
  final DateTime? startedAt;

  /// Data de conclusão do treinamento
  final DateTime? completedAt;

  /// Construtor
  TrainingSession({
    required this.id,
    required this.name,
    required this.description,
    required this.status,
    required this.modelType,
    required this.modelVersion,
    required this.datasetId,
    required this.hyperparameters,
    this.metrics,
    required this.createdAt,
    this.startedAt,
    this.completedAt,
  });

  /// Cria uma instância a partir de JSON
  factory TrainingSession.fromJson(Map<String, dynamic> json) {
    return TrainingSession(
      id: json['id'],
      name: json['name'],
      description: json['description'] ?? '',
      status: json['status'],
      modelType: json['model_type'],
      modelVersion: json['model_version'],
      datasetId: json['dataset_id'],
      hyperparameters: json['hyperparameters'] ?? {},
      metrics: json['metrics'],
      createdAt: DateTime.parse(json['created_at']),
      startedAt: json['started_at'] != null ? DateTime.parse(json['started_at']) : null,
      completedAt: json['completed_at'] != null ? DateTime.parse(json['completed_at']) : null,
    );
  }

  /// Converte para JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'status': status,
      'model_type': modelType,
      'model_version': modelVersion,
      'dataset_id': datasetId,
      'hyperparameters': hyperparameters,
      'metrics': metrics,
      'created_at': DateFormat('yyyy-MM-ddTHH:mm:ss').format(createdAt),
      'started_at': startedAt != null ? DateFormat('yyyy-MM-ddTHH:mm:ss').format(startedAt!) : null,
      'completed_at': completedAt != null ? DateFormat('yyyy-MM-ddTHH:mm:ss').format(completedAt!) : null,
    };
  }

  /// Formata o status para exibição
  String get statusDisplay {
    switch (status) {
      case 'pending':
        return 'Pendente';
      case 'running':
        return 'Em execução';
      case 'completed':
        return 'Concluído';
      case 'failed':
        return 'Falhou';
      case 'paused':
        return 'Pausado';
      default:
        return status;
    }
  }

  /// Retorna o nome completo do modelo
  String get fullModelName {
    if (modelType == 'yolov8') {
      return 'YOLOv8${modelVersion.toUpperCase()}';
    }
    return '$modelType-$modelVersion';
  }

  /// Formata a data de criação para exibição
  String get createdAtFormatted {
    return DateFormat('dd/MM/yyyy HH:mm').format(createdAt);
  }

  /// Calcula a duração do treinamento
  Duration get duration {
    if (startedAt == null) return Duration.zero;

    final endTime = completedAt ?? DateTime.now();
    return endTime.difference(startedAt!);
  }

  /// Formata a duração para exibição
  String get durationFormatted {
    final dur = duration;
    final hours = dur.inHours;
    final minutes = dur.inMinutes % 60;
    final seconds = dur.inSeconds % 60;

    return '$hours h $minutes min $seconds s';
  }

  /// Retorna o progresso atual do treinamento
  double get progress {
    if (metrics == null ||
        !metrics!.containsKey('current_epoch') ||
        !metrics!.containsKey('total_epochs')) {
      return 0.0;
    }

    final currentEpoch = metrics!['current_epoch'] as int;
    final totalEpochs = metrics!['total_epochs'] as int;

    return currentEpoch / totalEpochs;
  }

  /// Verifica se pode ser pausado
  bool get canBePaused => status == 'running';

  /// Verifica se pode ser retomado
  bool get canBeResumed => status == 'paused';

  /// Verifica se pode ser cancelado
  bool get canBeCancelled => status == 'running' || status == 'paused';

  /// Clona a instância com novos valores
  TrainingSession copyWith({
    int? id,
    String? name,
    String? description,
    String? status,
    String? modelType,
    String? modelVersion,
    int? datasetId,
    Map<String, dynamic>? hyperparameters,
    Map<String, dynamic>? metrics,
    DateTime? createdAt,
    DateTime? startedAt,
    DateTime? completedAt,
  }) {
    return TrainingSession(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      status: status ?? this.status,
      modelType: modelType ?? this.modelType,
      modelVersion: modelVersion ?? this.modelVersion,
      datasetId: datasetId ?? this.datasetId,
      hyperparameters: hyperparameters ?? this.hyperparameters,
      metrics: metrics ?? this.metrics,
      createdAt: createdAt ?? this.createdAt,
      startedAt: startedAt ?? this.startedAt,
      completedAt: completedAt ?? this.completedAt,
    );
  }
}