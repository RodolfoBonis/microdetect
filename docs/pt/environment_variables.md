# Guia de Variáveis de Ambiente

Este guia explica as variáveis de ambiente suportadas pelo MicroDetect, que fornecem uma maneira alternativa de configurar a aplicação sem modificar o arquivo de configuração.

## Sumário
- [Introdução](#introdução)
- [Variáveis de Ambiente Principais](#variáveis-de-ambiente-principais)
- [Variáveis do AWS CodeArtifact](#variáveis-do-aws-codeartifact)
- [Variáveis de Configuração de Hardware](#variáveis-de-configuração-de-hardware)
- [Variáveis de Logging](#variáveis-de-logging)
- [Variáveis de Diretório](#variáveis-de-diretório)
- [Definindo Variáveis de Ambiente](#definindo-variáveis-de-ambiente)
  - [Linux/macOS](#linuxmacos)
  - [Windows](#windows)
  - [Em Scripts Python](#em-scripts-python)
- [Variáveis de Ambiente no Docker](#variáveis-de-ambiente-no-docker)
- [Variáveis de Ambiente em CI/CD](#variáveis-de-ambiente-em-cicd)
- [Prioridade de Configuração](#prioridade-de-configuração)
- [Melhores Práticas](#melhores-práticas)

## Introdução

Variáveis de ambiente fornecem uma maneira flexível de configurar o MicroDetect sem modificar o arquivo de configuração. Elas são particularmente úteis em:

- Pipelines de CI/CD
- Contêineres Docker
- Scripts automatizados
- Múltiplos ambientes (desenvolvimento, homologação, produção)
- Situações onde você precisa sobrescrever configurações temporariamente

O MicroDetect verifica a existência de variáveis de ambiente específicas na inicialização e as utiliza para sobrescrever configurações correspondentes no arquivo de configuração.

## Variáveis de Ambiente Principais

Estas variáveis de ambiente controlam aspectos fundamentais do MicroDetect:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `MICRODETECT_CONFIG_PATH` | Caminho para o arquivo de configuração | `./config.yaml` |
| `MICRODETECT_SKIP_UPDATE_CHECK` | Desabilitar verificação automática de atualização | Não definido |
| `MICRODETECT_LOG_LEVEL` | Nível de logging (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `MICRODETECT_CACHE_DIR` | Diretório de cache | `~/.cache/microdetect` |
| `MICRODETECT_DATASET_DIR` | Diretório do dataset | `./dataset` |
| `MICRODETECT_IMAGES_DIR` | Diretório de imagens | `./data/images` |
| `MICRODETECT_LABELS_DIR` | Diretório de rótulos | `./data/labels` |
| `MICRODETECT_OUTPUT_DIR` | Diretório de saída | `./runs/train` |
| `MICRODETECT_REPORTS_DIR` | Diretório de relatórios | `./reports` |
| `MICRODETECT_NO_INTERACTIVE` | Desabilitar recursos interativos | Não definido |

Exemplo de uso:
```bash
MICRODETECT_LOG_LEVEL=DEBUG microdetect train --dataset_dir dataset
```

## Variáveis do AWS CodeArtifact

Estas variáveis controlam a integração com AWS CodeArtifact para atualizações:

| Variável | Descrição |
|----------|-----------|
| `AWS_CODEARTIFACT_DOMAIN` | Nome do domínio AWS CodeArtifact |
| `AWS_CODEARTIFACT_REPOSITORY` | Nome do repositório AWS CodeArtifact |
| `AWS_CODEARTIFACT_OWNER` | ID da conta AWS proprietária do domínio |
| `AWS_REGION` | Região AWS para CodeArtifact (padrão: us-east-1) |
| `AWS_ACCESS_KEY_ID` | ID da chave de acesso AWS para autenticação |
| `AWS_SECRET_ACCESS_KEY` | Chave de acesso secreta AWS para autenticação |
| `AWS_SESSION_TOKEN` | Token de sessão AWS (se usar credenciais temporárias) |
| `MICRODETECT_SKIP_UPDATE_CHECK` | Defina como `1` para desabilitar verificações de atualização |

Exemplo de uso:
```bash
export AWS_CODEARTIFACT_DOMAIN=meu-dominio
export AWS_CODEARTIFACT_REPOSITORY=meu-repo
export AWS_REGION=us-west-2
microdetect update --check-only
```

## Variáveis de Configuração de Hardware

Estas variáveis controlam como o MicroDetect utiliza recursos de hardware:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `CUDA_VISIBLE_DEVICES` | GPUs a serem utilizadas (ex: "0,1,2") | Todas disponíveis |
| `MICRODETECT_DEVICE` | Dispositivo a ser utilizado (ex: "cpu", "0", "cuda:0") | Auto-detectar |
| `OMP_NUM_THREADS` | Threads OpenMP para operações de CPU | Número de CPUs |
| `MKL_NUM_THREADS` | Threads MKL para operações de CPU | Número de CPUs |
| `NUMEXPR_NUM_THREADS` | Threads NumExpr para operações de CPU | Número de CPUs |
| `MICRODETECT_BATCH_SIZE` | Sobrescrever tamanho de batch padrão | Varia por comando |
| `MICRODETECT_WORKERS` | Número de workers para carregamento de dados | `8` |

Exemplo de uso:
```bash
# Usar apenas a primeira GPU
CUDA_VISIBLE_DEVICES=0 microdetect train --dataset_dir dataset

# Usar CPU em vez de GPU
MICRODETECT_DEVICE=cpu microdetect train --dataset_dir dataset

# Definir paralelismo de CPU
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 microdetect train --dataset_dir dataset
```

## Variáveis de Logging

Estas variáveis controlam o comportamento de logging:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `MICRODETECT_LOG_LEVEL` | Nível de logging | `INFO` |
| `MICRODETECT_LOG_FILE` | Caminho do arquivo de log | `microdetect.log` |
| `MICRODETECT_LOG_FORMAT` | Formato da mensagem de log | Ver [Referência de Configuração](configuration_reference.md) |
| `MICRODETECT_LOG_MAX_SIZE` | Tamanho máximo do arquivo de log em bytes | `10485760` (10MB) |
| `MICRODETECT_LOG_BACKUP_COUNT` | Número de backups de log a manter | `3` |
| `MICRODETECT_NO_COLOR` | Desabilitar saída colorida no console | Não definido |

Exemplo de uso:
```bash
MICRODETECT_LOG_LEVEL=DEBUG MICRODETECT_LOG_FILE=debug.log microdetect train --dataset_dir dataset
```

## Variáveis de Diretório

Estas variáveis controlam os diretórios utilizados pelo MicroDetect:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `MICRODETECT_DATASET_DIR` | Diretório do dataset | `./dataset` |
| `MICRODETECT_IMAGES_DIR` | Diretório de imagens | `./data/images` |
| `MICRODETECT_LABELS_DIR` | Diretório de rótulos | `./data/labels` |
| `MICRODETECT_OUTPUT_DIR` | Diretório de saída | `./runs/train` |
| `MICRODETECT_REPORTS_DIR` | Diretório de relatórios | `./reports` |
| `MICRODETECT_CACHE_DIR` | Diretório de cache | `~/.cache/microdetect` |
| `MICRODETECT_CONFIG_DIR` | Diretório de configuração | `~/.microdetect` |

Exemplo de uso:
```bash
MICRODETECT_IMAGES_DIR=/caminho/para/imagens MICRODETECT_LABELS_DIR=/caminho/para/rotulos microdetect dataset --dataset_dir dataset
```

## Definindo Variáveis de Ambiente

### Linux/macOS

Temporário (para a sessão atual do terminal):
```bash
export MICRODETECT_LOG_LEVEL=DEBUG
export MICRODETECT_CACHE_DIR=/tmp/microdetect_cache
```

Permanente (adicionar ao ~/.bashrc ou ~/.zshrc):
```bash
echo 'export MICRODETECT_LOG_LEVEL=DEBUG' >> ~/.bashrc
source ~/.bashrc
```

Uso único (para um único comando):
```bash
MICRODETECT_LOG_LEVEL=DEBUG microdetect train --dataset_dir dataset
```

### Windows

Temporário (para o prompt de comando atual):
```cmd
set MICRODETECT_LOG_LEVEL=DEBUG
set MICRODETECT_CACHE_DIR=C:\temp\microdetect_cache
```

Permanente (usando Propriedades do Sistema):
1. Clique com o botão direito em Computador → Propriedades → Configurações avançadas do sistema
2. Clique em Variáveis de Ambiente
3. Adicione ou modifique variáveis na seção Variáveis de usuário ou Variáveis de sistema

Uso único (para um único comando):
```cmd
set MICRODETECT_LOG_LEVEL=DEBUG && microdetect train --dataset_dir dataset
```

No PowerShell:
```powershell
$env:MICRODETECT_LOG_LEVEL = "DEBUG"
microdetect train --dataset_dir dataset
```

### Em Scripts Python

Para definir variáveis de ambiente em scripts Python:

```python
import os
import subprocess

# Definir variáveis de ambiente
os.environ["MICRODETECT_LOG_LEVEL"] = "DEBUG"
os.environ["MICRODETECT_CACHE_DIR"] = "/tmp/microdetect_cache"

# Executar MicroDetect como um subprocesso
subprocess.run(["microdetect", "train", "--dataset_dir", "dataset"])

# Ou importar e usar o MicroDetect diretamente
from microdetect.training import YOLOTrainer
trainer = YOLOTrainer()  # Usará as variáveis de ambiente
trainer.train("dataset/data.yaml")
```

## Variáveis de Ambiente no Docker

Ao executar o MicroDetect em contêineres Docker, você pode definir variáveis de ambiente usando a flag `-e`:

```bash
docker run -e MICRODETECT_LOG_LEVEL=DEBUG -e CUDA_VISIBLE_DEVICES=0 microdetect-image microdetect train --dataset_dir dataset
```

Ou em um arquivo Docker Compose:

```yaml
version: '3'
services:
  microdetect:
    image: microdetect-image
    environment:
      - MICRODETECT_LOG_LEVEL=DEBUG
      - CUDA_VISIBLE_DEVICES=0
      - AWS_CODEARTIFACT_DOMAIN=meu-dominio
      - AWS_CODEARTIFACT_REPOSITORY=meu-repo
```

## Variáveis de Ambiente em CI/CD

Em pipelines de CI/CD, variáveis de ambiente são frequentemente definidas no arquivo de configuração:

Exemplo do GitHub Actions:
```yaml
jobs:
  train_model:
    runs-on: ubuntu-latest
    env:
      MICRODETECT_LOG_LEVEL: INFO
      MICRODETECT_NO_INTERACTIVE: 1
      AWS_CODEARTIFACT_DOMAIN: ${{ secrets.AWS_CODEARTIFACT_DOMAIN }}
      AWS_CODEARTIFACT_REPOSITORY: ${{ secrets.AWS_CODEARTIFACT_REPOSITORY }}
    steps:
      - uses: actions/checkout@v3
      - name: Treinar modelo
        run: microdetect train --dataset_dir dataset --model_size m --epochs 100
```

Exemplo do GitLab CI:
```yaml
train_job:
  stage: train
  variables:
    MICRODETECT_LOG_LEVEL: INFO
    MICRODETECT_NO_INTERACTIVE: 1
  script:
    - microdetect train --dataset_dir dataset --model_size m --epochs 100
```

## Prioridade de Configuração

O MicroDetect usa a seguinte ordem de prioridade para determinar a configuração final:

1. Argumentos de linha de comando (prioridade mais alta)
2. Variáveis de ambiente
3. Arquivo de configuração
4. Valores padrão internos (prioridade mais baixa)

Por exemplo, se você definir o tamanho do batch de três formas:
- Linha de comando: `microdetect train --batch_size 16`
- Ambiente: `MICRODETECT_BATCH_SIZE=32`
- Arquivo de configuração: `batch_size: 64` no `config.yaml`

O valor da linha de comando (16) será usado porque tem a maior prioridade.

## Melhores Práticas

1. **Use variáveis de ambiente para mudanças temporárias**: Para mudanças permanentes, modifique o arquivo de configuração.

2. **Use variáveis de ambiente em pipelines de CI/CD**: Isso permite configurações diferentes em ambientes diferentes sem modificar arquivos.

3. **Use variáveis de ambiente para segredos**: Nunca armazene credenciais AWS ou outros segredos em arquivos de configuração.

4. **Documente suas variáveis de ambiente**: Inclua uma lista de variáveis de ambiente obrigatórias e opcionais na documentação do seu projeto.

5. **Defina variáveis relacionadas juntas**: Algumas variáveis funcionam juntas (como `OMP_NUM_THREADS` e `MKL_NUM_THREADS`), então defina-as consistentemente.

6. **Use nomes descritivos para scripts**: Crie scripts shell com nomes descritivos para combinações comuns de variáveis de ambiente.

7. **Verifique conflitos de variáveis de ambiente**: Esteja ciente de que algumas variáveis de ambiente podem ser definidas por outros softwares ou pelo sistema.

8. **Considere usar arquivos `.env`**: Para desenvolvimento, armazene variáveis de ambiente em um arquivo `.env` e carregue-as conforme necessário (não para segredos em produção).