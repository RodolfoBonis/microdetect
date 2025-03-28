// lib/core/enums/backend_status_enum.dart


enum BackendSteps {
  /// Inicialização do sistema
  initialize,

  /// Inicialização do backend
  backend,

  /// Inicialização do Python
  python,

  /// Inicialização do servidor
  server,

  /// Instalando dependências
  dependencies,

  /// Inicialização do sistema de diretórios
  directories,

  /// Inicialização do sistema de configurações
  settings,

  /// Inicialização do sistema de notificações
  notifications,

  /// Inicialização do sistema de temas
  themes,

  /// Inicialização do sistema de logs
  logs,

  /// Inicialização do sistema de atualizações
  updates,

  /// Inicialização do sistema de armazenamento
  storage,

  /// Inicialização do sistema de eventos
  events,

}

/// Enum que representa os diferentes estados do backend
enum BackendStatus {
  /// Inicializando o sistema
  initializing,
  
  /// Verificando o status ou disponibilidade
  checking,
  
  /// Iniciando o serviço ou iniciando o processo de inicialização
  starting,
  
  /// Servidor está rodando normalmente
  running,
  
  /// Servidor está em processo de encerramento
  stopping,
  
  /// Servidor está parado (intencionalmente)
  stopped,
  
  /// Erro ocorreu durante a operação do servidor
  error,
  
  /// Erro ocorreu durante a operação do servidor (alias para 'error')
  failed,
  
  /// Estado desconhecido ou não definido
  unknown,
}

/// Enum para representar o status de um item de verificação (check item)
enum CheckStatus {
  /// Pendente, ainda não iniciado
  pending,
  
  /// Em progresso de verificação ou processamento
  inProgress,
  
  /// Em progresso de verificação ou processamento (alias para 'inProgress')
  loading,
  
  /// Concluído com sucesso
  completed,
  
  /// Concluído com sucesso (alias para 'completed')
  success,
  
  /// Erro durante a verificação
  error,
}