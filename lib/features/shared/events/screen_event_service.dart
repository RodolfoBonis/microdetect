import 'package:get/get.dart';
import 'package:microdetect/features/shared/events/event_manager.dart';
import 'package:microdetect/features/shared/events/screen_events.dart';

/// Serviço para disparar eventos do sistema
class ScreenEventService extends GetxService {
  /// Dispara um evento de refresh
  void fireRefresh() {
    Get.events.fire(ScreenEvents.refresh);
  }
  
  /// Dispara um evento de mostrar ajuda
  void fireShowHelp() {
    Get.events.fire(ScreenEvents.showHelp);
  }
  
  /// Dispara um evento de refresh de datasets
  void fireRefreshDatasets() {
    Get.events.fire(ScreenEvents.refreshDatasets);
  }
  
  /// Dispara um evento de criação de dataset
  void fireCreateNewDataset() {
    Get.events.fire(ScreenEvents.createNewDataset);
  }
  
  /// Dispara um evento de limpar
  void fireClear() {
    Get.events.fire(ScreenEvents.clear);
  }
  
  /// Dispara um evento de aplicar configurações
  void fireApplySettings() {
    Get.events.fire(ScreenEvents.applySettings);
  }
  
  /// Dispara um evento de resetar configurações
  void fireResetSettings() {
    Get.events.fire(ScreenEvents.resetSettings);
  }
  
  /// Dispara um evento personalizado com dados adicionais
  void fireCustomEvent(String eventType, {Map<String, dynamic>? data}) {
    Get.events.fire(eventType, data: data);
  }
  
  /// Obtém a instância do serviço
  static ScreenEventService get to => Get.find<ScreenEventService>();
} 