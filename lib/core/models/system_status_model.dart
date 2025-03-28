// To parse this JSON data, do
//
//     final systemStatusModel = systemStatusModelFromMap(jsonString);

import 'dart:convert';

SystemStatusModel systemStatusModelFromMap(String str) => SystemStatusModel.fromMap(json.decode(str));

String systemStatusModelToMap(SystemStatusModel data) => json.encode(data.toMap());

class SystemStatusModel {
  SystemStatusModel({
    required this.os,
    required this.cpu,
    required this.memory,
    required this.gpu,
    required this.storage,
    required this.server,
  });

  final String os;
  final Cpu cpu;
  final Memory memory;
  final Gpu gpu;
  final Storage storage;
  final Server server;

  factory SystemStatusModel.fromMap(Map<String, dynamic> json) => SystemStatusModel(
    os: json["os"],
    cpu: Cpu.fromMap(json["cpu"]),
    memory: Memory.fromMap(json["memory"]),
    gpu: Gpu.fromMap(json["gpu"]),
    storage: Storage.fromMap(json["storage"]),
    server: Server.fromMap(json["server"]),
  );

  Map<String, dynamic> toMap() => {
    "os": os,
    "cpu": cpu.toMap(),
    "memory": memory.toMap(),
    "gpu": gpu.toMap(),
    "storage": storage.toMap(),
    "server": server.toMap(),
  };

  factory SystemStatusModel.defaultStatus() {
    return SystemStatusModel(
      os: 'Desconhecido',
      cpu: Cpu(
          model: 'Desconhecido',
          cores: 0,
          threads: 0,
          usage: '0%'
      ),
      memory: Memory(
          total: '0 GB',
          available: '0 GB',
          percentage: 0.0
      ),
      gpu: Gpu(
          model: 'Desconhecido',
          memory: '0 GB',
          available: false
      ),
      storage: Storage(
          used: '0 GB',
          total: '0 GB',
          percentage: 0.0
      ),
      server: Server(
          version: 'Desconhecido',
          active: false
      ),
    );
  }
}

class Cpu {
  Cpu({
    required this.model,
    required this.cores,
    required this.threads,
    required this.usage,
  });

  final String model;
  final int cores;
  final int threads;
  final String usage;

  factory Cpu.fromMap(Map<String, dynamic> json) => Cpu(
    model: json["model"],
    cores: json["cores"],
    threads: json["threads"],
    usage: json["usage"],
  );

  Map<String, dynamic> toMap() => {
    "model": model,
    "cores": cores,
    "threads": threads,
    "usage": usage,
  };
}

class Gpu {
  Gpu({
    required this.model,
    required this.memory,
    required this.available,
  });

  final String model;
  final String memory;
  final bool available;

  factory Gpu.fromMap(Map<String, dynamic> json) => Gpu(
    model: json["model"],
    memory: json["memory"],
    available: json["available"],
  );

  Map<String, dynamic> toMap() => {
    "model": model,
    "memory": memory,
    "available": available,
  };
}

class Memory {
  Memory({
    required this.total,
    required this.available,
    required this.percentage,
  });

  final String total;
  final String available;
  final double percentage;

  factory Memory.fromMap(Map<String, dynamic> json) => Memory(
    total: json["total"],
    available: json["available"],
    percentage: json["percentage"].toDouble(),
  );

  Map<String, dynamic> toMap() => {
    "total": total,
    "available": available,
    "percentage": percentage,
  };
}

class Server {
  Server({
    required this.version,
    required this.active,
  });

  final String version;
  final bool active;

  factory Server.fromMap(Map<String, dynamic> json) => Server(
    version: json["version"],
    active: json["active"],
  );

  Map<String, dynamic> toMap() => {
    "version": version,
    "active": active,
  };
}

class Storage {
  Storage({
    required this.used,
    required this.total,
    required this.percentage,
  });

  final String used;
  final String total;
  final double percentage;

  factory Storage.fromMap(Map<String, dynamic> json) => Storage(
    used: json["used"],
    total: json["total"],
    percentage: json["percentage"].toDouble(),
  );

  Map<String, dynamic> toMap() => {
    "used": used,
    "total": total,
    "percentage": percentage,
  };
}
