# Configuração do AWS CodeArtifact

Este documento explica como configurar o deploy automático para o AWS CodeArtifact e como utilizar o pacote MicroDetect a partir do repositório privado.

## Sumário
- [Requisitos](#requisitos)
- [Configuração no AWS CodeArtifact](#configuração-no-aws-codeartifact)
  - [1. Criar um Domínio no CodeArtifact](#1-criar-um-domínio-no-codeartifact)
  - [2. Criar um Repositório no CodeArtifact](#2-criar-um-repositório-no-codeartifact)
  - [3. Conectar o Repositório ao PyPI](#3-conectar-o-repositório-ao-pypi)
  - [4. Criar IAM User com Permissões](#4-criar-iam-user-com-permissões)
  - [5. Gerar Access Key para o IAM User](#5-gerar-access-key-para-o-iam-user)
- [Configuração no GitHub](#configuração-no-github)
  - [1. Adicionar Secrets no Repositório GitHub](#1-adicionar-secrets-no-repositório-github)
- [Uso do Workflow](#uso-do-workflow)
  - [Publicação Automática em Novas Releases](#publicação-automática-em-novas-releases)
  - [Publicação Manual](#publicação-manual)
- [Instalar o Pacote do AWS CodeArtifact](#instalar-o-pacote-do-aws-codeartifact)
  - [1. Configurar o pip para usar AWS CodeArtifact](#1-configurar-o-pip-para-usar-aws-codeartifact)
  - [2. Instalar o pacote](#2-instalar-o-pacote)
  - [3. Configuração Manual do pip](#3-configuração-manual-do-pip)
- [Ferramenta de Configuração AWS do MicroDetect](#ferramenta-de-configuração-aws-do-microdetect)
- [Solução de Problemas](#solução-de-problemas)
  - [Erro de Autenticação](#erro-de-autenticação)
  - [Erro de Versão](#erro-de-versão)
  - [Erro de Dependências](#erro-de-dependências)

## Requisitos

Para configurar o deploy automático, você precisará:

1. Uma conta AWS com permissões para acessar o CodeArtifact
2. Um domínio e repositório no CodeArtifact
3. Credenciais AWS com permissões para publicar no repositório
4. Secrets configurados no GitHub (para CI/CD)

## Configuração no AWS CodeArtifact

### 1. Criar um Domínio no CodeArtifact

Se você ainda não possui um domínio, crie um:

```bash
aws codeartifact create-domain --domain seu-dominio
```

### 2. Criar um Repositório no CodeArtifact

Crie um repositório dentro do seu domínio:

```bash
aws codeartifact create-repository \
    --domain seu-dominio \
    --repository seu-repositorio \
    --description "Repositório Python privado para MicroDetect"
```

### 3. Conectar o Repositório ao PyPI

Para permitir que seu repositório acesse pacotes do PyPI público:

```bash
# Criar um repositório para fazer proxy do PyPI
aws codeartifact create-repository \
    --domain seu-dominio \
    --repository pypi-store \
    --description "Proxy para PyPI público"

# Conectar ao PyPI externo
aws codeartifact associate-external-connection \
    --domain seu-dominio \
    --repository pypi-store \
    --external-connection public:pypi

# Fazer seu repositório usar o pypi-store como upstream
aws codeartifact update-repository \
    --domain seu-dominio \
    --repository seu-repositorio \
    --upstreams repositoryName=pypi-store
```

### 4. Criar IAM User com Permissões

Crie um usuário com permissões apropriadas:

```bash
aws iam create-user --user-name codeartifact-publisher

aws iam attach-user-policy --user-name codeartifact-publisher \
    --policy-arn arn:aws:iam::aws:policy/AWSCodeArtifactAdminAccess
```

### 5. Gerar Access Key para o IAM User

Gere credenciais para o usuário IAM:

```bash
aws iam create-access-key --user-name codeartifact-publisher
```

Guarde o `AccessKeyId` e `SecretAccessKey` retornados.

## Configuração no GitHub

### 1. Adicionar Secrets no Repositório GitHub

Vá para Settings → Secrets → Actions no seu repositório e adicione os seguintes secrets:

- `AWS_ACCESS_KEY_ID`: O ID da chave de acesso do IAM user
- `AWS_SECRET_ACCESS_KEY`: A chave secreta do IAM user
- `AWS_REGION`: A região onde o CodeArtifact está hospedado (ex: `us-east-1`)
- `AWS_CODEARTIFACT_DOMAIN`: O nome do domínio CodeArtifact
- `AWS_CODEARTIFACT_REPOSITORY`: O nome do repositório CodeArtifact
- `AWS_CODEARTIFACT_OWNER`: (Opcional) O ID da conta AWS proprietária do domínio
- `GH_TOKEN`: Token de acesso pessoal do GitHub com permissões para o repositório
- `BOTTOKEN`: Token do seu bot do Telegram
- `CHAT_ID`: ID do chat para notificações
- `THREAD_ID`: (Opcional) ID do thread para notificações em grupos

## Uso do Workflow

### Publicação Automática em Novas Releases

Quando você cria uma nova release no GitHub, o workflow é automaticamente acionado e:

1. Obtém as informações da release
2. Atualiza a versão no código (`__version__`)
3. Constrói o pacote
4. Publica no AWS CodeArtifact
5. Notifica via Telegram o resultado

### Publicação Manual

Você também pode acionar o workflow manualmente:

1. Vá para a aba "Actions" no GitHub
2. Selecione "Deploy to AWS CodeArtifact"
3. Clique em "Run workflow"
4. Escolha o tipo de incremento de versão (patch, minor, major) ou especifique uma versão personalizada
5. Clique em "Run workflow"

## Instalar o Pacote do AWS CodeArtifact

### 1. Configurar o pip para usar AWS CodeArtifact

```bash
# Obter token de autorização (válido por 12 horas)
aws codeartifact login \
    --tool pip \
    --domain seu-dominio \
    --repository seu-repositorio \
    --domain-owner ACCOUNT_ID
```

### 2. Instalar o pacote

```bash
pip install microdetect
```

### 3. Configuração Manual do pip

Alternativamente, você pode configurar o pip manualmente:

```bash
# Obter token
export CODEARTIFACT_AUTH_TOKEN=$(aws codeartifact get-authorization-token \
    --domain seu-dominio \
    --domain-owner ACCOUNT_ID \
    --query authorizationToken \
    --output text)

# Obter URL do repositório
export CODEARTIFACT_REPOSITORY_URL=$(aws codeartifact get-repository-endpoint \
    --domain seu-dominio \
    --domain-owner ACCOUNT_ID \
    --repository seu-repositorio \
    --format pypi \
    --query repositoryEndpoint \
    --output text)

# Instalar o pacote
pip install microdetect \
    --index-url "${CODEARTIFACT_REPOSITORY_URL}simple/" \
    --extra-index-url https://pypi.org/simple
```

## Ferramenta de Configuração AWS do MicroDetect

O MicroDetect oferece uma ferramenta CLI para simplificar a configuração do AWS CodeArtifact:

```bash
# Configurar AWS CodeArtifact
microdetect setup-aws --domain seu-dominio --repository seu-repositorio --configure-aws

# Opções disponíveis:
#   --domain           Nome do domínio CodeArtifact (obrigatório)
#   --repository       Nome do repositório CodeArtifact (obrigatório)
#   --domain-owner     ID da conta AWS proprietária do domínio (opcional)
#   --region           Região AWS (padrão: us-east-1)
#   --configure-aws    Configurar credenciais AWS
#   --test             Testar conexão após a configuração
```

Esta ferramenta irá:
1. Verificar se o AWS CLI está instalado (instalando-o se necessário)
2. Configurar credenciais AWS se solicitado
3. Configurar variáveis de ambiente e configuração para o sistema de atualização do MicroDetect
4. Testar a conexão para garantir que tudo funcione

## Solução de Problemas

### Erro de Autenticação

Se você receber erros de autenticação:

1. Verifique se suas credenciais AWS estão corretas
2. Verifique se o token de autorização é válido (expira após 12 horas)
3. Verifique as permissões do usuário IAM

```bash
# Testar autenticação
aws sts get-caller-identity

# Regenerar token de autorização
aws codeartifact get-authorization-token \
    --domain seu-dominio \
    --query authorizationToken \
    --output text
```

### Erro de Versão

Se você tentar publicar uma versão que já existe:

1. Certifique-se de incrementar a versão antes de publicar
2. Verifique a versão atual no repositório:

```bash
pip index versions microdetect \
    --index-url "${CODEARTIFACT_REPOSITORY_URL}simple/" \
    --no-cache-dir
```

### Erro de Dependências

Se houver problemas com dependências:

1. Certifique-se de que seu repositório tem acesso ao PyPI público
2. Verifique se todas as dependências estão listadas corretamente no `setup.py` ou `requirements.txt`

```bash
# Verificar configuração upstream
aws codeartifact list-repositories-in-domain \
    --domain seu-dominio

# Verificar detalhes do repositório incluindo upstreams
aws codeartifact describe-repository \
    --domain seu-dominio \
    --repository seu-repositorio
```

Para solução de problemas mais detalhada, consulte a [Documentação do AWS CodeArtifact](https://docs.aws.amazon.com/codeartifact/latest/ug/welcome.html) ou verifique o [Guia de Solução de Problemas](troubleshooting.md).