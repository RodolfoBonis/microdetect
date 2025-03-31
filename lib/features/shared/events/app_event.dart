class AppEvent {
  // Eventos globais
  static const String refresh = 'refresh';
  static const String showHelp = 'show_help';

  // Eventos de navegação
  static const String pageEntered = 'page_entered';
  static const String pageExited = 'page_exited';

  // Eventos de datasets
  static const String refreshDatasets = 'refresh_datasets';
  static const String createDataset = 'create_dataset';
  static const String updateDataset = 'update_dataset';
  static const String deleteDataset = 'delete_dataset';

  // Eventos de configurações
  static const String settingsChanged = 'settings_changed';

  // Eventos de sistema
  static const String systemStatusChanged = 'system_status_changed';

  // Eventos de UI
  static const String themeChanged = 'theme_changed';
  static const String languageChanged = 'language_changed';

  // Construtor privado para evitar instâncias
  AppEvent._();
}