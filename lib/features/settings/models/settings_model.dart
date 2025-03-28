import 'dart:convert';

/// Modelo que representa todas as configurações da aplicação MicroDetect
class SettingsModel {
  // Configurações da interface
  final String themeMode; // 'light', 'dark', 'system'
  final String language; // 'pt', 'en', 'es'
  final bool showAdvancedOptions;
  
  // Configurações da câmera
  final String lastCameraId;
  final String defaultCameraDir;
  final String defaultResolution; // 'sd', 'hd', 'fullhd'
  final String defaultWhiteBalance; // 'auto', 'daylight', 'fluorescent', etc.
  final double adjustBrightness; // -1.0 a 1.0
  final double adjustContrast; // -1.0 a 1.0 
  final double adjustSaturation; // -1.0 a 1.0
  final double adjustSharpness; // 0.0 a 1.0
  final String filterType; // 'none', 'grayscale', 'sepia', etc.
  
  // Configurações de sistema
  final bool enableLogging;
  final bool enableDebugMode;
  final bool enableLogPersistence; // Persistência de logs em arquivo
  final bool autoStartBackend;
  final bool backgroundProcessing;
  final int autoSaveInterval; // Em segundos
  final bool normalizeImages;
  final bool backupEnabled;
  
  // Configurações de diretórios
  final String pythonPath;
  final String dataDirectory;
  final String defaultExportDir;
  
  // Outros
  final List<String> recentProjects;
  final String lastDatasetId;

  /// Construtor com valores padrão
  SettingsModel({
    this.themeMode = 'system',
    this.language = 'pt',
    this.showAdvancedOptions = false,
    this.lastCameraId = '',
    this.defaultCameraDir = '',
    this.defaultResolution = 'hd',
    this.defaultWhiteBalance = 'auto',
    this.adjustBrightness = 0.0,
    this.adjustContrast = 0.0,
    this.adjustSaturation = 0.0,
    this.adjustSharpness = 0.0,
    this.filterType = 'none',
    this.enableLogging = true,
    this.enableDebugMode = false,
    this.enableLogPersistence = false,
    this.autoStartBackend = true,
    this.backgroundProcessing = true,
    this.autoSaveInterval = 300,
    this.normalizeImages = true,
    this.backupEnabled = true,
    this.pythonPath = '',
    this.dataDirectory = '',
    this.defaultExportDir = '',
    this.recentProjects = const [],
    this.lastDatasetId = '',
  });

  /// Converter para JSON
  Map<String, dynamic> toJson() => {
    'themeMode': themeMode,
    'language': language,
    'showAdvancedOptions': showAdvancedOptions,
    'lastCameraId': lastCameraId,
    'defaultCameraDir': defaultCameraDir,
    'defaultResolution': defaultResolution,
    'defaultWhiteBalance': defaultWhiteBalance,
    'adjustBrightness': adjustBrightness,
    'adjustContrast': adjustContrast,
    'adjustSaturation': adjustSaturation,
    'adjustSharpness': adjustSharpness,
    'filterType': filterType,
    'enableLogging': enableLogging,
    'enableDebugMode': enableDebugMode,
    'enableLogPersistence': enableLogPersistence,
    'autoStartBackend': autoStartBackend,
    'backgroundProcessing': backgroundProcessing,
    'autoSaveInterval': autoSaveInterval,
    'normalizeImages': normalizeImages,
    'backupEnabled': backupEnabled,
    'pythonPath': pythonPath,
    'dataDirectory': dataDirectory,
    'defaultExportDir': defaultExportDir,
    'recentProjects': recentProjects,
    'lastDatasetId': lastDatasetId,
  };

  /// Criar a partir de JSON
  factory SettingsModel.fromJson(Map<String, dynamic> json) {
    return SettingsModel(
      themeMode: json['themeMode'] ?? 'system',
      language: json['language'] ?? 'pt',
      showAdvancedOptions: json['showAdvancedOptions'] ?? false,
      lastCameraId: json['lastCameraId'] ?? '',
      defaultCameraDir: json['defaultCameraDir'] ?? '',
      defaultResolution: json['defaultResolution'] ?? 'hd',
      defaultWhiteBalance: json['defaultWhiteBalance'] ?? 'auto',
      adjustBrightness: json['adjustBrightness']?.toDouble() ?? 0.0,
      adjustContrast: json['adjustContrast']?.toDouble() ?? 0.0,
      adjustSaturation: json['adjustSaturation']?.toDouble() ?? 0.0,
      adjustSharpness: json['adjustSharpness']?.toDouble() ?? 0.0,
      filterType: json['filterType'] ?? 'none',
      enableLogging: json['enableLogging'] ?? true,
      enableDebugMode: json['enableDebugMode'] ?? false,
      enableLogPersistence: json['enableLogPersistence'] ?? false,
      autoStartBackend: json['autoStartBackend'] ?? true,
      backgroundProcessing: json['backgroundProcessing'] ?? true,
      autoSaveInterval: json['autoSaveInterval'] ?? 300,
      normalizeImages: json['normalizeImages'] ?? true,
      backupEnabled: json['backupEnabled'] ?? true,
      pythonPath: json['pythonPath'] ?? '',
      dataDirectory: json['dataDirectory'] ?? '',
      defaultExportDir: json['defaultExportDir'] ?? '',
      recentProjects: json['recentProjects'] != null 
          ? List<String>.from(json['recentProjects']) 
          : [],
      lastDatasetId: json['lastDatasetId'] ?? '',
    );
  }

  /// Criar a partir de string JSON
  factory SettingsModel.fromJsonString(String jsonString) {
    final Map<String, dynamic> json = jsonDecode(jsonString);
    return SettingsModel.fromJson(json);
  }

  /// Converter para string JSON
  String toJsonString() => jsonEncode(toJson());

  /// Criar uma cópia com alterações
  SettingsModel copyWith({
    String? themeMode,
    String? language,
    bool? showAdvancedOptions,
    String? lastCameraId,
    String? defaultCameraDir,
    String? defaultResolution,
    String? defaultWhiteBalance,
    double? adjustBrightness,
    double? adjustContrast,
    double? adjustSaturation,
    double? adjustSharpness,
    String? filterType,
    bool? enableLogging,
    bool? enableDebugMode,
    bool? enableLogPersistence,
    bool? autoStartBackend,
    bool? backgroundProcessing,
    int? autoSaveInterval,
    bool? normalizeImages,
    bool? backupEnabled,
    String? pythonPath,
    String? dataDirectory,
    String? defaultExportDir,
    List<String>? recentProjects,
    String? lastDatasetId,
  }) {
    return SettingsModel(
      themeMode: themeMode ?? this.themeMode,
      language: language ?? this.language,
      showAdvancedOptions: showAdvancedOptions ?? this.showAdvancedOptions,
      lastCameraId: lastCameraId ?? this.lastCameraId,
      defaultCameraDir: defaultCameraDir ?? this.defaultCameraDir,
      defaultResolution: defaultResolution ?? this.defaultResolution,
      defaultWhiteBalance: defaultWhiteBalance ?? this.defaultWhiteBalance,
      adjustBrightness: adjustBrightness ?? this.adjustBrightness,
      adjustContrast: adjustContrast ?? this.adjustContrast,
      adjustSaturation: adjustSaturation ?? this.adjustSaturation,
      adjustSharpness: adjustSharpness ?? this.adjustSharpness,
      filterType: filterType ?? this.filterType,
      enableLogging: enableLogging ?? this.enableLogging,
      enableDebugMode: enableDebugMode ?? this.enableDebugMode,
      enableLogPersistence: enableLogPersistence ?? this.enableLogPersistence,
      autoStartBackend: autoStartBackend ?? this.autoStartBackend,
      backgroundProcessing: backgroundProcessing ?? this.backgroundProcessing,
      autoSaveInterval: autoSaveInterval ?? this.autoSaveInterval,
      normalizeImages: normalizeImages ?? this.normalizeImages,
      backupEnabled: backupEnabled ?? this.backupEnabled,
      pythonPath: pythonPath ?? this.pythonPath,
      dataDirectory: dataDirectory ?? this.dataDirectory,
      defaultExportDir: defaultExportDir ?? this.defaultExportDir,
      recentProjects: recentProjects ?? this.recentProjects,
      lastDatasetId: lastDatasetId ?? this.lastDatasetId,
    );
  }
} 