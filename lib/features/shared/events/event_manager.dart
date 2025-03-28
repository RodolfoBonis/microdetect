import 'package:get/get.dart';
import 'package:microdetect/features/shared/events/screen_events.dart';

/// Um gerenciador de eventos central que substitui o uso direto de Streams
/// para evitar problemas de null check e ciclo de vida
class EventManager {
  // Singleton para garantir que temos apenas uma instância
  static final EventManager _instance = EventManager._internal();
  
  // Fábrica para acessar a instância singleton
  factory EventManager() {
    return _instance;
  }
  
  // Construtor interno para o singleton
  EventManager._internal();
  
  // Mapa de callbacks registrados por tipo de evento
  final Map<String, List<Function(ScreenEvent)>> _listeners = {};
  
  /// Registra um callback para um tipo específico de evento
  void addListener(String eventType, Function(ScreenEvent) callback) {
    if (_listeners[eventType] == null) {
      _listeners[eventType] = [];
    }
    _listeners[eventType]!.add(callback);
  }
  
  /// Registra um callback para vários tipos de eventos
  void addListeners(List<String> eventTypes, Function(ScreenEvent) callback) {
    for (final eventType in eventTypes) {
      addListener(eventType, callback);
    }
  }
  
  /// Remove um callback específico para um tipo de evento
  void removeListener(String eventType, Function(ScreenEvent) callback) {
    if (_listeners[eventType] != null) {
      _listeners[eventType]!.remove(callback);
    }
  }
  
  /// Remove todos os callbacks para um tipo específico de evento
  void removeAllListenersForType(String eventType) {
    _listeners.remove(eventType);
  }
  
  /// Limpa todos os callbacks registrados
  void clearAllListeners() {
    _listeners.clear();
  }
  
  /// Dispara um evento para todos os callbacks registrados para esse tipo
  void fireEvent(ScreenEvent event) {
    final listeners = _listeners[event.eventType];
    if (listeners != null) {
      for (final callback in List.from(listeners)) {
        callback(event);
      }
    }
  }
  
  /// Dispara um evento simples a partir de um tipo
  void fire(String eventType, {Map<String, dynamic>? data}) {
    fireEvent(ScreenEvent(eventType: eventType, data: data));
  }
  
  /// Obtém acesso estático à instância
  static EventManager get instance => _instance;
}

/// Extension para facilitar o acesso ao EventManager via Get
extension EventManagerExtension on GetInterface {
  EventManager get events => EventManager.instance;
} 