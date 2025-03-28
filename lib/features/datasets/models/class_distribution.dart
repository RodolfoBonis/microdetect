import 'dart:convert';

class ClassDistribution {
  final String className;
  final int count;
  final double percentage;
  final bool isUsed;
  final bool isUndefined;

  ClassDistribution({
    required this.className,
    required this.count,
    required this.percentage,
    this.isUsed = true,
    this.isUndefined = false,
  });

  factory ClassDistribution.fromJson(Map<String, dynamic> json) {
    return ClassDistribution(
      className: json['class_name'] ?? '',
      count: json['count'] ?? 0,
      percentage: json['percentage']?.toDouble() ?? 0.0,
      isUsed: json['is_used'] ?? true,
      isUndefined: json['is_undefined'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'class_name': className,
      'count': count,
      'percentage': percentage,
      'is_used': isUsed,
      'is_undefined': isUndefined,
    };
  }

  ClassDistribution copyWith({
    String? className,
    int? count,
    double? percentage,
    bool? isUsed,
    bool? isUndefined,
  }) {
    return ClassDistribution(
      className: className ?? this.className,
      count: count ?? this.count,
      percentage: percentage ?? this.percentage,
      isUsed: isUsed ?? this.isUsed,
      isUndefined: isUndefined ?? this.isUndefined,
    );
  }

  String toJsonString() => jsonEncode(toJson());

  @override
  String toString() {
    return 'ClassDistribution{className: $className, count: $count, percentage: $percentage, isUsed: $isUsed, isUndefined: $isUndefined}';
  }
} 