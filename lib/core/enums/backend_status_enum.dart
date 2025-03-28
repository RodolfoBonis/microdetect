// lib/core/enums/backend_status_enum.dart

/// Define as etapas de inicialização do backend com precisão
enum BackendInitStep {
  /// Inicialização do sistema principal
  systemInitialization,

  /// Configuração de diretórios da aplicação
  directorySetup,

  /// Verificação da instalação do backend
  installationCheck,

  /// Verificação de atualizações disponíveis
  updateCheck,

  /// Instalação ou atualização do backend
  backendInstallation,

  /// Configuração dos diretórios de dados
  dataDirectorySetup,

  /// Verificação do ambiente Python
  pythonEnvironmentCheck,

  /// Instalação de dependências Python
  dependenciesInstallation,

  /// Inicialização do servidor Python
  serverStartup,

  /// Verificação da saúde do servidor
  healthCheck,

  /// Processo de inicialização concluído
  completed,

  /// Falha na inicialização
  failed
}

/// Status geral do backend
enum BackendStatus {
  /// Inicializando o sistema
  initializing,

  /// Verificando o status ou disponibilidade
  checking,

  /// Iniciando o serviço
  starting,

  /// Servidor está rodando normalmente
  running,

  /// Servidor está em processo de encerramento
  stopping,

  /// Servidor está parado (intencionalmente)
  stopped,

  /// Erro ocorreu durante a operação do servidor
  error,

  /// Estado desconhecido ou não definido
  unknown,
}

/// Status de uma verificação ou operação específica
enum CheckStatus {
  /// Pendente, ainda não iniciado
  pending,

  /// Em progresso
  inProgress,

  /// Concluído com sucesso
  completed,

  /// Falha na verificação ou operação
  error,
}

/// Tipo de operação de atualização do backend
enum UpdateOperation {
  /// Verificando se existe atualização
  checking,

  /// Baixando atualização
  downloading,

  /// Instalando atualização
  installing,

  /// Reiniciando após atualização
  restarting,

  /// Nenhuma operação de atualização em andamento
  none,
}

/// Resultado de uma operação no backend
enum OperationResult {
  /// Operação bem-sucedida
  success,

  /// Operação falhou
  failure,

  /// Operação cancelada
  cancelled,

  /// Operação em andamento
  inProgress,

  /// Operação aguardando alguma condição
  pending,
}