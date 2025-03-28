/// Constantes de eventos para comunicação entre telas da aplicação
class ScreenEvents {
  // Eventos gerais
  static const String showHelp = 'SHOW_HELP';
  
  // Eventos da Home
  static const String refresh = 'REFRESH';
  
  // Eventos de Dataset
  static const String refreshDatasets = 'refresh_datasets';
  static const String createNewDataset = 'create_new_dataset';
  static const String clear = 'clear';

  // Eventos de Settings
  static const String applySettings = 'apply_settings';
  static const String resetSettings = 'reset_settings';

  // Eventos de Gelria
  static const String refreshGallery = 'refresh_gallery';

  // Outros eventos
  static const String toggleTheme = 'toggle_theme';
  static const String exportData = 'export_data';
  static const String importData = 'import_data';
  
  // Construtor privado para evitar instanciação
  ScreenEvents._();
}

/// Classe de evento para comunicação interna na aplicação
class ScreenEvent {
  final String eventType;
  final Map<String, dynamic>? data;

  ScreenEvent({required this.eventType, this.data});
} 