import 'dart:async';

import 'package:get/get.dart';

/// Event data class that contains both event name and associated data
class EventData {
  final String name;
  final Map<String, dynamic>? data;

  EventData(this.name, [this.data]);
}

class EventBus extends GetxService {
  EventBus();

  final StreamController<EventData> _eventStreamController = StreamController<EventData>.broadcast();

  /// Stream of events that can be listened to
  Stream<EventData> get stream => _eventStreamController.stream;

  /// EventBus instance
  static EventBus get instance => Get.find<EventBus>();

  /// Singleton instance of EventBus
  static EventBus get to => Get.find<EventBus>();

  /// Private constructor
  EventBus._();

  /// Initialize the EventBus service
  static Future<EventBus> init() async {
    return EventBus._();
  }

  /// Emit an event with optional data
  void emit(String event, {Map<String, dynamic>? data}) {
    _eventStreamController.add(EventData(event, data));
  }

  /// Listen to specific events
  StreamSubscription<EventData> on(
      String eventName,
      void Function(Map<String, dynamic>?) callback,
      ) {
    return stream.where((event) => event.name == eventName).listen(
          (event) => callback(event.data),
    );
  }

  /// Dispose the EventBus service
  @override
  void onClose() {
    _eventStreamController.close();
    super.onClose();
  }
}