import 'package:intl/intl.dart';

/// Modelo de dados para busca de hiperparâmetros
class HyperparamSearch {
  /// ID único da busca
  final int id;

  /// Nome da busca
  final String name;

  /// Descrição da busca
  final String description;

  /// Estado atual da busca: 'pending', 'running', 'completed', 'failed'
  final String status;

  /// ID do dataset usado para a busca
  final int datasetId;

  /// Espaço de busca para hiperparâmetros
  final Map<String, dynamic> searchSpace;

  /// Melhores parâmetros encontrados
  final Map<String, dynamic>? bestParams;

  /// Métricas dos melhores parâmetros
  final Map<String, dynamic>? bestMetrics;

  /// Dados de todas as tentativas realizadas
  final List<Map<String, dynamic>>? trialsData;

  /// Número total de iterações a serem realizadas
  final int iterations;

  /// Data de criação da busca
  final DateTime createdAt;

  /// Data de início da busca
  final DateTime? startedAt;

  /// Data de conclusão da busca
  final DateTime? completedAt;

  /// ID da sessão de treinamento criada com os melhores parâmetros
  final int? trainingSessionId;

  /// Construtor
  HyperparamSearch({
    required this.id,
    required this.name,
    required this.description,
    required this.status,
    required this.datasetId,
    required this.searchSpace,
    this.bestParams,
    this.bestMetrics,
    this.trialsData,
    required this.iterations,
    required this.createdAt,
    this.startedAt,
    this.completedAt,
    this.trainingSessionId,
  });

  /// Cria uma instância a partir de JSON
  factory HyperparamSearch.fromJson(Map<String, dynamic> json) {
    return HyperparamSearch(
      id: json['id'],
      name: json['name'],
      description: json['description'] ?? '',
      status: json['status'],
      datasetId: json['dataset_id'],
      searchSpace: json['search_space'] ?? {},
      bestParams: json['best_params'],
      bestMetrics: json['best_metrics'],
      trialsData: json['trials_data'] != null
          ? List<Map<String, dynamic>>.from(json['trials_data'])
          : null,
      iterations: json['iterations'] ?? 5,
      createdAt: DateTime.parse(json['created_at']),
      startedAt: json['started_at'] != null ? DateTime.parse(json['started_at']) : null,
      completedAt: json['completed_at'] != null ? DateTime.parse(json['completed_at']) : null,
      trainingSessionId: json['training_session_id'],
    );
  }

  /// Converte para JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'status': status,
      'dataset_id': datasetId,
      'search_space': searchSpace,
      'best_params': bestParams,
      'best_metrics': bestMetrics,
      'trials_data': trialsData,
      'iterations': iterations,
      'created_at': DateFormat('yyyy-MM-ddTHH:mm:ss').format(createdAt),
      'started_at': startedAt != null ? DateFormat('yyyy-MM-ddTHH:mm:ss').format(startedAt!) : null,
      'completed_at': completedAt != null ? DateFormat('yyyy-MM-ddTHH:mm:ss').format(completedAt!) : null,
      'training_session_id': trainingSessionId,
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
      default:
        return status;
    }
  }

  /// Retorna o progresso atual da busca (número de trials / iterações totais)
  double get progress {
    if (trialsData == null) return 0.0;
    return trialsData!.length / iterations;
  }

  /// Formata a data de criação para exibição
  String get createdAtFormatted {
    return DateFormat('dd/MM/yyyy HH:mm').format(createdAt);
  }

  /// Calcula a duração da busca
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

  /// Clona a instância com novos valores
  HyperparamSearch copyWith({
    int? id,
    String? name,
    String? description,
    String? status,
    int? datasetId,
    Map<String, dynamic>? searchSpace,
    Map<String, dynamic>? bestParams,
    Map<String, dynamic>? bestMetrics,
    List<Map<String, dynamic>>? trialsData,
    int? iterations,
    DateTime? createdAt,
    DateTime? startedAt,
    DateTime? completedAt,
    int? trainingSessionId,
  }) {
    return HyperparamSearch(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      status: status ?? this.status,
      datasetId: datasetId ?? this.datasetId,
      searchSpace: searchSpace ?? this.searchSpace,
      bestParams: bestParams ?? this.bestParams,
      bestMetrics: bestMetrics ?? this.bestMetrics,
      trialsData: trialsData ?? this.trialsData,
      iterations: iterations ?? this.iterations,
      createdAt: createdAt ?? this.createdAt,
      startedAt: startedAt ?? this.startedAt,
      completedAt: completedAt ?? this.completedAt,
      trainingSessionId: trainingSessionId ?? this.trainingSessionId,
    );
  }
}