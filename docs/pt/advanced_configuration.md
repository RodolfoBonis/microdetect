# Configuração Avançada

Este documento explica todas as opções de configuração avançada disponíveis no MicroDetect para personalizar e otimizar sua funcionalidade de acordo com suas necessidades específicas.

## Sumário
- [Visão Geral do Arquivo de Configuração](#visão-geral-do-arquivo-de-configuração)
- [Estrutura do Arquivo de Configuração](#estrutura-do-arquivo-de-configuração)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Configuração via Linha de Comando](#configuração-via-linha-de-comando)
- [Perfis de Configuração](#perfis-de-configuração)
- [Opções Avançadas de Treinamento](#opções-avançadas-de-treinamento)
- [Configuração de Inferência](#configuração-de-inferência)
- [Configuração de Callbacks](#configuração-de-callbacks)
- [Configuração Persistente](#configuração-persistente)
- [Configuração de Logging](#configuração-de-logging)
- [Configuração de Cache](#configuração-de-cache)
- [Configuração Multi-Projeto](#configuração-multi-projeto)
- [Integração CI/CD](#integração-cicd)

## Visão Geral do Arquivo de Configuração

O MicroDetect utiliza um arquivo centralizado `config.yaml` para a maioria das configurações. Este arquivo é criado automaticamente quando você executa `microdetect init` e pode ser editado manualmente.

### Localização do Arquivo de Configuração

O sistema procura o arquivo de configuração nos seguintes locais, em ordem de prioridade:

1. Caminho especificado manualmente em comandos
2. Diretório atual (`./config.yaml`)
3. Diretório do usuário (`~/.microdetect/config.yaml`)
4. Configuração padrão interna do pacote

## Estrutura do Arquivo de Configuração

Abaixo está a estrutura completa com todas as opções disponíveis:

```yaml
# Configuração para o Projeto MicroDetect

# Diretórios
directories:
  dataset: ./dataset              # Diretório para dataset estruturado
  images: ./data/images           # Diretório para imagens originais
  labels: ./data/labels           # Diretório para anotações
  output: ./runs/train            # Diretório para resultados de treinamento
  reports: ./reports              # Diretório para relatórios
  cache: ~/.cache/microdetect     # Diretório de cache

# Classes para detecção
classes:
  - "0-levedura"                  # Formato: "ID-nome"
  - "1-fungo"
  - "2-micro-alga"
  # Adicione mais classes conforme necessário

# Mapeamento de cores para visualização
color_map:
  "0": [0, 255, 0]                # Verde para leveduras (formato RGB)
  "1": [0, 0, 255]                # Vermelho para fungos
  "2": [255, 0, 0]                # Azul para micro-algas
  # Adicione cores para classes adicionais

# Parâmetros de treinamento
training:
  model_size: s                   # Tamanho do modelo (n, s, m, l, x)
  epochs: 100                     # Número de épocas
  batch_size: 32                  # Tamanho do batch
  image_size: 640                 # Tamanho da imagem
  pretrained: true                # Usar pesos pré-treinados
  patience: 20                    # Paciência para early stopping
  optimizer: AdamW                # Otimizador (SGD, Adam, AdamW)
  lr0: 0.01                       # Taxa de aprendizado inicial
  lrf: 0.01                       # Taxa de aprendizado final
  momentum: 0.937                 # Momentum para SGD
  weight_decay: 0.0005            # Weight decay
  warmup_epochs: 3                # Épocas de aquecimento
  warmup_momentum: 0.8            # Momentum durante aquecimento
  warmup_bias_lr: 0.1             # Taxa de aprendizado de bias durante aquecimento
  box: 7.5                        # Peso da perda de box
  cls: 0.5                        # Peso da perda de classe
  dfl: 1.5                        # Peso da perda DFL
  fl_gamma: 0.0                   # Gamma para focal loss
  workers: 8                      # Número de workers para carregamento de dados
  cos_lr: true                    # Usar learning rate com coseno

# Parâmetros do dataset
dataset:
  train_ratio: 0.7                # Proporção para treinamento
  val_ratio: 0.15                 # Proporção para validação
  test_ratio: 0.15                # Proporção para teste
  seed: 42                        # Semente para reprodutibilidade
  cache: true                     # Cache de imagens na RAM
  rect: false                     # Usar crops retangulares
  mosaic: 1.0                     # Probabilidade de mosaico
  mixup: 0.5                      # Probabilidade de mixup
  copy_images: true               # Copiar imagens para o diretório do dataset

# Parâmetros de augmentação de dados
augmentation:
  factor: 20                      # Número de imagens a gerar por original
  brightness_range: [0.8, 1.2]    # Intervalo de brilho (min, max)
  contrast_range: [-30, 30]       # Intervalo de contraste (min, max)
  flip_probability: 0.5           # Probabilidade de flip horizontal
  rotation_range: [-15, 15]       # Intervalo de rotação (min, max)
  noise_probability: 0.3          # Probabilidade de ruído
  blur_probability: 0.2           # Probabilidade de blur
  cutout_probability: 0.2         # Probabilidade de cutout
  cutout_size: [0.05, 0.2]        # Tamanho do cutout (min%, max%)
  hue_shift: 0.1                  # Deslocamento de matiz
  saturation_shift: 0.1           # Deslocamento de saturação

# Parâmetros de avaliação
evaluation:
  conf_threshold: 0.25            # Limiar de confiança
  iou_threshold: 0.45             # Limiar de IoU
  max_detections: 300             # Máximo de detecções
  save_confusion_matrix: true     # Salvar matriz de confusão
  save_json: true                 # Salvar resultados como JSON
  verbose: true                   # Saída detalhada
  plots: true                     # Gerar gráficos

# Parâmetros de conversão de imagem
conversion:
  format: png                     # Formato alvo (png, jpg)
  quality: 95                     # Qualidade para JPG
  use_opencv: true                # Usar OpenCV em vez de PIL
  delete_original: false          # Excluir arquivo original após conversão
  preserve_metadata: true         # Preservar metadados EXIF
  resize: false                   # Redimensionar imagens
  max_size: [1024, 1024]          # Tamanho máximo após redimensionamento

# Parâmetros de anotação
annotation:
  box_thickness: 2                # Espessura da caixa
  text_size: 0.5                  # Tamanho do texto
  auto_save: true                 # Auto-salvar anotações
  auto_save_interval: 300         # Intervalo de auto-save (segundos)
  undo_levels: 10                 # Níveis de desfazer

# Parâmetros do AWS CodeArtifact
aws:
  domain: seu-dominio             # Nome do domínio CodeArtifact
  repository: seu-repositorio     # Nome do repositório
  region: us-east-1               # Região AWS
  auto_check: true                # Verificar atualizações automaticamente
  check_interval: 86400           # Intervalo de verificação (segundos)

# Configuração de logging
logging:
  level: INFO                     # Nível de logging (DEBUG, INFO, WARNING, ERROR)
  file: microdetect.log           # Arquivo de log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Formato
  max_size: 10485760              # Tamanho máximo do arquivo de log (10MB)
  backup_count: 3                 # Número de backups
```

## Variáveis de Ambiente

Além do arquivo de configuração, o MicroDetect também respeita várias variáveis de ambiente:

| Variável | Descrição | Padrão |
|----------|-------------|---------|
| `MICRODETECT_CONFIG_PATH` | Caminho para o arquivo de configuração | `./config.yaml` |
| `MICRODETECT_LOG_LEVEL` | Nível de logging | `INFO` |
| `MICRODETECT_SKIP_UPDATE_CHECK` | Desabilitar verificação de atualização | Não definido |
| `MICRODETECT_CACHE_DIR` | Diretório de cache | `~/.cache/microdetect` |
| `AWS_CODEARTIFACT_DOMAIN` | Domínio AWS CodeArtifact | Definido por `setup-aws` |
| `AWS_CODEARTIFACT_REPOSITORY` | Repositório AWS CodeArtifact | Definido por `setup-aws` |
| `AWS_CODEARTIFACT_OWNER` | Proprietário do domínio AWS | Definido por `setup-aws` |
| `CUDA_VISIBLE_DEVICES` | GPUs a serem usadas | Todas disponíveis |
| `OMP_NUM_THREADS` | Threads OpenMP | Número de CPUs |

## Configuração via Linha de Comando

Muitas configurações podem ser substituídas usando argumentos de linha de comando:

```bash
# Exemplo: substituir configurações de treinamento
microdetect train --dataset_dir dataset --model_size m --epochs 200 --batch_size 16 --image_size 640
```

### Prioridade de Configuração

O MicroDetect usa a seguinte ordem de prioridade para determinar as configurações:

1. Argumentos de linha de comando
2. Variáveis de ambiente
3. Arquivo de configuração
4. Valores padrão internos

## Perfis de Configuração

Você pode manter múltiplos perfis de configuração para diferentes casos de uso:

```bash
# Criar um novo perfil
cp config.yaml config_treinamento.yaml

# Usar um perfil específico
microdetect train --config config_treinamento.yaml
```

## Opções Avançadas de Treinamento

### Configuração de GPU

Para controlar o uso de GPU:

```bash
# Usar GPU específica
CUDA_VISIBLE_DEVICES=0 microdetect train --dataset_dir dataset

# Usar múltiplas GPUs (se disponíveis)
microdetect train --dataset_dir dataset --device 0,1

# Forçar uso de CPU
microdetect train --dataset_dir dataset --device cpu
```

### Ajuste de Hiperparâmetros

O MicroDetect suporta busca de hiperparâmetros:

```bash
# Busca básica de hiperparâmetros
microdetect train --dataset_dir dataset --find_hyperparams

# Espaço de busca personalizado (requer arquivo JSON)
microdetect train --dataset_dir dataset --find_hyperparams --search_space hyperparams.json
```

Exemplo de `hyperparams.json`:

```json
{
  "learning_rate": {"type": "float", "min": 0.001, "max": 0.1, "log": true},
  "batch_size": {"type": "int", "values": [8, 16, 32, 64]},
  "model_size": {"type": "categorical", "values": ["n", "s", "m"]}
}
```

## Configuração de Inferência

Para configurar inferência e detecção:

```yaml
# Em config.yaml
inference:
  conf_threshold: 0.25            # Limiar de confiança para detecção
  iou_threshold: 0.45             # Limiar de IoU para NMS
  max_detections: 300             # Número máximo de detecções
  agnostic_nms: false             # NMS agnóstico de classe
  show_labels: true               # Mostrar rótulos
  show_conf: true                 # Mostrar confiança
  save_crops: false               # Salvar crops de detecção
  hide_conf: false                # Ocultar valor de confiança
  hide_labels: false              # Ocultar rótulos
  half: false                     # Usar precisão mista (FP16)
```

## Configuração de Callbacks

O MicroDetect suporta callbacks personalizados para treinamento:

```python
# Em seu script Python personalizado
from microdetect.training.train import YOLOTrainer
from ultralytics.callbacks import Callback

# Definir seu callback
class CustomCallback(Callback):
    def on_train_start(self, trainer):
        print("Treinamento iniciado!")
    
    def on_train_end(self, trainer):
        print("Treinamento concluído!")

# Usar com o treinador
trainer = YOLOTrainer()
trainer.model.add_callback("custom", CustomCallback())
trainer.train(data_yaml="dataset/data.yaml")
```

## Configuração Persistente

Para salvar configurações frequentemente usadas, adicione-as ao arquivo `.env`:

```bash
# Criar/editar .env
echo "MICRODETECT_LOG_LEVEL=DEBUG" >> .env
echo "AWS_CODEARTIFACT_DOMAIN=meu-dominio" >> .env
```

Para carregar automaticamente essas configurações:

```bash
# Linux/macOS
source <(grep -v '^#' .env | sed 's/^/export /')

# Windows PowerShell
Get-Content .env | ForEach-Object { 
    if ($_ -match '(.+)=(.+)') { 
        [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2]) 
    } 
}
```

## Configuração de Logging

Para configuração detalhada de logging:

```python
# Em seu script personalizado
import logging
from microdetect.utils.config import config

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.get("logging.level", "INFO")),
    format=config.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    handlers=[
        logging.FileHandler(config.get("logging.file", "microdetect.log")),
        logging.StreamHandler()
    ]
)
```

## Configuração de Cache

Para melhorar o desempenho com cache:

```yaml
# Em config.yaml
caching:
  enabled: true                   # Habilitar cache
  directory: ~/.cache/microdetect  # Diretório de cache
  max_size_gb: 10                 # Tamanho máximo de cache (GB)
  ttl: 604800                     # TTL em segundos (7 dias)
  compression: true               # Usar compressão
```

## Configuração Multi-Projeto

Para gerenciar múltiplos projetos:

```
projetos/
├── projeto1/
│   ├── config.yaml            # Configuração específica do Projeto1
│   ├── data/
│   │   ├── images/
│   │   └── labels/
│   └── dataset/
├── projeto2/
│   ├── config.yaml            # Configuração específica do Projeto2
│   ├── data/
│   │   ├── images/
│   │   └── labels/
│   └── dataset/
└── config_global.yaml         # Configurações compartilhadas
```

Cada projeto pode ter sua própria configuração, mas herdar das configurações globais:

```bash
# Combinar configurações
python -c "import yaml; config_global=yaml.safe_load(open('config_global.yaml')); config_projeto=yaml.safe_load(open('projeto1/config.yaml')); config_combinado={**config_global, **config_projeto}; print(yaml.dump(config_combinado))" > projeto1/config_combinado.yaml

# Usar configuração combinada
microdetect --config projeto1/config_combinado.yaml train
```

## Integração CI/CD

Para ambientes CI/CD, você pode usar variáveis de ambiente ou passar um arquivo de configuração:

```bash
# Exemplo GitHub Actions
MICRODETECT_CONFIG_PATH=ci_config.yaml microdetect train --dataset_dir dataset --no-interactive
```

Usando o Makefile com configurações:

```bash
# Exemplo com múltiplas configurações
make train MODEL_SIZE=m EPOCHS=200 BATCH_SIZE=16 IMAGE_SIZE=640 DOMAIN=meu-dominio
```

Para mais informações sobre recursos e fluxos de trabalho específicos, consulte as páginas de documentação correspondentes.