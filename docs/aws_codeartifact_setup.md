# Deploy para AWS CodeArtifact

Este documento explica como configurar o deploy automático para o AWS CodeArtifact e como utilizar o pacote MicroDetect a partir do repositório privado.

## Requisitos

Para configurar o deploy automático, você precisará:

1. Uma conta AWS com permissões para acessar o CodeArtifact
2. Um domínio e repositório no CodeArtifact
3. Credenciais AWS com permissões para publicar no repositório
4. Secrets configurados no GitHub

## Configuração no AWS CodeArtifact

### 1. Criar um Domínio no CodeArtifact (se não existir)

```bash
aws codeartifact create-domain --domain seu-dominio
```

### 2. Criar um Repositório no CodeArtifact

```bash
aws codeartifact create-repository \
    --domain seu-dominio \
    --repository seu-repositorio \
    --description "Repositório Python privado para MicroDetect"
```

### 3. Conectar o Repositório ao PyPI (opcional)

Para permitir que seu repositório acesse pacotes do PyPI público:

```bash
aws codeartifact create-repository \
    --domain seu-dominio \
    --repository pypi-store \
    --description "Proxy para PyPI público"

aws codeartifact associate-external-connection \
    --domain seu-dominio \
    --repository pypi-store \
    --external-connection public:pypi

aws codeartifact update-repository \
    --domain seu-dominio \
    --repository seu-repositorio \
    --upstreams repositoryName=pypi-store
```

### 4. Criar IAM User com Permissões

```bash
aws iam create-user --user-name codeartifact-publisher

aws iam attach-user-policy --user-name codeartifact-publisher \
    --policy-arn arn:aws:iam::aws:policy/AWSCodeArtifactAdminAccess
```

### 5. Gerar Access Key para o IAM User

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

Para instalar o pacote MicroDetect do seu repositório privado:

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

## Solução de Problemas

### Erro de Autenticação

Se você receber erros de autenticação:

1. Verifique se as credenciais AWS estão corretas
2. Verifique se o token de autorização é válido (expira em 12 horas)
3. Verifique as permissões do IAM user

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