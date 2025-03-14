# Sistema de Atualização do MicroDetect

Este documento explica o sistema de atualização automática do MicroDetect, que permite verificar e instalar atualizações a partir do AWS CodeArtifact.

## Visão Geral

O sistema de atualização do MicroDetect permite que você:

1. Configure uma conexão com o AWS CodeArtifact
2. Verifique se há versões mais recentes disponíveis
3. Atualize para a versão mais recente de forma segura
4. Receba notificações automáticas sobre novas versões

## Pré-requisitos

Para usar o sistema de atualização, você precisará de:

- Acesso a um domínio e repositório do AWS CodeArtifact
- AWS CLI instalado (será instalado automaticamente se necessário)
- Credenciais AWS com permissões para acessar o CodeArtifact

## Configuração Inicial

Antes de usar o sistema de atualização, você precisa configurar a conexão com o AWS CodeArtifact:

```bash
microdetect setup-aws --domain seu-dominio --repository seu-repositorio --configure-aws
```

### Parâmetros de Configuração

| Parâmetro | Descrição | Obrigatório |
|-----------|-----------|-------------|
| `--domain` | Nome do domínio AWS CodeArtifact | Sim |
| `--repository` | Nome do repositório AWS CodeArtifact | Sim |
| `--domain-owner` | ID da conta proprietária do domínio | Não |
| `--region` | Região AWS (padrão: us-east-1) | Não |
| `--configure-aws` | Configurar credenciais AWS | Não |
| `--test` | Testar conexão após a configuração | Não |

### Exemplo de Configuração Completa

```bash
microdetect setup-aws --domain meu-dominio --repository meu-repo --domain-owner 123456789012 --region us-east-2 --configure-aws --test
```

## Verificando Atualizações

Para verificar manualmente se há atualizações disponíveis:

```bash
microdetect update --check-only
```

Este comando compara a versão instalada com a versão mais recente disponível no AWS CodeArtifact e informa se há uma atualização disponível.

## Instalando Atualizações

Para atualizar o MicroDetect para a versão mais recente:

```bash
microdetect update
```

Quando você executa este comando:

1. O sistema verifica se há uma nova versão disponível
2. Se uma nova versão for encontrada, você será perguntado se deseja atualizar
3. A atualização é baixada e instalada usando pip
4. O processo de atualização exibe o progresso em tempo real

### Atualização Forçada

Para atualizar sem confirmação:

```bash
microdetect update --force
```

## Verificação Automática de Atualizações

O MicroDetect verifica automaticamente se há atualizações disponíveis após a execução de qualquer comando (exceto os próprios comandos de atualização). Se uma atualização for encontrada, você verá uma notificação:

```
🔄 Nova versão do MicroDetect disponível: 1.2.3 (atual: 1.1.0)
   Para atualizar, execute: microdetect update
```

### Desativando as Verificações Automáticas

Se você não deseja verificar atualizações automaticamente, pode definir a variável de ambiente `MICRODETECT_SKIP_UPDATE_CHECK`:

```bash
# Linux/macOS
export MICRODETECT_SKIP_UPDATE_CHECK=1

# Windows
set MICRODETECT_SKIP_UPDATE_CHECK=1
```

## Uso com o Makefile

O Makefile do projeto inclui comandos para facilitar o gerenciamento de atualizações:

```bash
# Configurar AWS CodeArtifact
make setup-aws DOMAIN=seu-dominio REPOSITORY=seu-repo

# Verificar atualizações
make check-update

# Atualizar aplicação
make update
```

## Como Funciona Internamente

O sistema de atualização opera da seguinte forma:

1. **Autenticação com AWS CodeArtifact**:
   - Obtém um token de autenticação utilizando o AWS CLI
   - Determina o endpoint do repositório

2. **Verificação de Versões**:
   - Usa pip para listar versões disponíveis
   - Extrai e compara versões usando versionamento semântico

3. **Fontes de Configuração**:
   - Busca credenciais AWS em múltiplos locais nesta ordem:
     1. Variáveis de ambiente (`AWS_CODEARTIFACT_DOMAIN`, `AWS_CODEARTIFACT_REPOSITORY`, `AWS_CODEARTIFACT_OWNER`)
     2. Arquivo de configuração em `~/.microdetect/config.ini`
     3. Arquivo `.env` local (para compatibilidade)

4. **Processo de Atualização**:
   - Configura ambiente pip para usar o repositório AWS CodeArtifact
   - Executa a atualização preservando dependências
   - Detecta se está executando em um ambiente Conda e ajusta conforme necessário

5. **Cache de Verificação**:
   - Armazena data da última verificação para não sobrecarregar
   - Verifica apenas uma vez por dia (configurável)

## Solução de Problemas

### Erro de Configuração AWS

Se você receber um erro de conexão ao AWS CodeArtifact:

1. Verifique se suas credenciais AWS estão configuradas corretamente
2. Verifique se o domínio e repositório existem
3. Verifique se você tem permissões para acessar o repositório
4. Execute `microdetect setup-aws --test` para diagnosticar problemas

### Erro na Verificação de Versões

Se você não conseguir verificar ou obter a versão mais recente:

1. Verifique se o token AWS está válido
2. Verifique se o pacote existe no repositório
3. Verifique sua conexão com a internet

### Erro na Atualização

Se a atualização falhar:

1. Verifique se você tem permissões para instalar pacotes
2. Tente atualizar com pip diretamente
3. Verifique se há conflitos de dependências

## Registro e Diagnóstico

O sistema de atualização registra informações detalhadas no arquivo de log do MicroDetect. Para ver logs mais detalhados, você pode aumentar o nível de logging:

```bash
export MICRODETECT_LOG_LEVEL=DEBUG
microdetect update --check-only
```

Os logs ajudarão a diagnosticar problemas no processo de atualização.

## Perguntas Frequentes

### Com que frequência o MicroDetect verifica atualizações?

Por padrão, o MicroDetect verifica atualizações uma vez por dia quando você executa qualquer comando. O intervalo de verificação pode ser configurado no arquivo `config.yaml`.

### Posso atualizar para uma versão específica?

Sim, você pode atualizar para uma versão específica usando:

```bash
microdetect update --version 1.2.3
```

### Como sei qual versão estou usando atualmente?

Você pode verificar sua versão atual com:

```bash
microdetect --version
```

### O que acontece se uma atualização falhar?

Se uma atualização falhar, o MicroDetect manterá a versão atual e exibirá uma mensagem de erro. Você pode tentar novamente ou verificar os logs para mais informações.

### Posso reverter para uma versão anterior?

Sim, você pode instalar uma versão anterior específica usando:

```bash
microdetect update --version 1.1.0
```

## Melhores Práticas

1. **Atualizações Regulares**: Mantenha o MicroDetect atualizado para se beneficiar das mais recentes funcionalidades e correções de bugs.
2. **Teste Após Atualizações**: Após atualizar para uma nova versão, teste seus fluxos de trabalho para garantir que tudo funcione como esperado.
3. **Backup de Dados Importantes**: Antes de atualizações de versões principais, faça backup da sua configuração e dados importantes.
4. **Atualize Primeiro em Desenvolvimento**: Se estiver usando o MicroDetect em produção, teste as atualizações em um ambiente de desenvolvimento primeiro.
5. **Verifique as Notas de Release**: Revise as notas de release antes de atualizar para entender as mudanças na nova versão.