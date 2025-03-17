# Referência de Configuração

Este documento fornece uma referência completa para todas as opções de configuração disponíveis no arquivo `config.yaml` do MicroDetect, detalhando cada parâmetro e seu uso.

## Sumário
- [Introdução](#introdução)
- [Estrutura do Arquivo de Configuração](#estrutura-do-arquivo-de-configuração)
- [Configuração de Diretórios](#configuração-de-diretórios)
- [Configuração de Classes](#configuração-de-classes)
- [Mapeamento de Cores](#mapeamento-de-cores)
- [Configuração de Treinamento](#configuração-de-treinamento)
- [Configuração de Dataset](#configuração-de-dataset)
- [Configuração de Augmentação de Dados](#configuração-de-augmentação-de-dados)
- [Configuração de Avaliação](#configuração-de-avaliação)
- [Configuração de Conversão de Imagem](#configuração-de-conversão-de-imagem)
- [Configuração de Anotação](#configuração-de-anotação)
- [Configuração do AWS CodeArtifact](#configuração-do-aws-codeartifact)
- [Configuração de Logging](#configuração-de-logging)
- [Configuração de Cache](#configuração-de-cache)
- [Configuração de Inferência](#configuração-de-inferência)

## Introdução

O MicroDetect usa um arquivo de configuração YAML (`config.yaml`) para centralizar configurações e parâmetros. Este arquivo é criado automaticamente quando você executa `microdetect init` e pode ser editado manualmente para personalizar o comportamento de vários componentes.

O arquivo de configuração é carregado dos seguintes locais, em ordem de prioridade:
1. Caminho especificado manualmente em comandos
2. Diretório atual (`./config.yaml`)
3. Diretório do usuário (`~/.microdetect/config.yaml`)
4. Configuração padrão interna do pacote

## Estrutura do Arquivo de Configuração

A estrutura completa do `config.yaml` com todas as opções disponíveis é descrita abaixo:

```yaml
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

# Configuração de cache
caching:
  enabled: true                   # Habilitar cache
  directory: ~/.cache/microdetect  # Diretório de cache
  max_size_gb: 10                 # Tamanho máximo de cache (GB)
  ttl: 604800                     # TTL em segundos (7 dias)
  compression: true               # Usar compressão

# Configuração de inferência
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

## Configuração de Diretórios

A seção `directories` define caminhos padrão usados pelo MicroDetect:

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `dataset` | Diretório para o dataset estruturado | `./dataset` |
| `images` | Diretório para imagens originais | `./data/images` |
| `labels` | Diretório para anotações | `./data/labels` |
| `output` | Diretório para resultados de treinamento | `./runs/train` |
| `reports` | Diretório para relatórios gerados | `./reports` |
| `cache` | Diretório para arquivos em cache | `~/.cache/microdetect` |

## Configuração de Classes

A seção `classes` define as classes de microorganismos a serem detectadas:

```yaml
classes:
  - "0-levedura"                  # Formato: "ID-nome"
  - "1-fungo"
  - "2-micro-alga"
```

Cada classe é definida no formato `"ID-nome"` onde:
- `ID` é um identificador numérico começando de 0
- `nome` é um nome descritivo para a classe

## Mapeamento de Cores

A seção `color_map` define cores RGB para visualizar cada classe:

```yaml
color_map:
  "0": [0, 255, 0]                # Verde para leveduras
  "1": [0, 0, 255]                # Vermelho para fungos
  "2": [255, 0, 0]                # Azul para micro-algas
```

Cada entrada mapeia um ID de classe para uma cor RGB (vermelho, verde, azul) com valores de 0 a 255.

## Configuração de Treinamento

A seção `training` controla os parâmetros de treinamento do modelo:

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `model_size` | Tamanho do modelo YOLOv8 (n, s, m, l, x) | `s` |
| `epochs` | Número de épocas de treinamento | `100` |
| `batch_size` | Tamanho do batch de treinamento | `32` |
| `image_size` | Tamanho da imagem de treinamento (pixels) | `640` |
| `pretrained` | Usar pesos pré-treinados | `true` |
| `patience` | Épocas sem melhoria antes do early stopping | `20` |
| `optimizer` | Algoritmo de otimização (SGD, Adam, AdamW) | `AdamW` |
| `lr0` | Taxa de aprendizado inicial | `0.01` |
| `lrf` | Fator de taxa de aprendizado final | `0.01` |
| `momentum` | Momentum para otimizador SGD | `0.937` |
| `weight_decay` | Weight decay (regularização L2) | `0.0005` |
| `warmup_epochs` | Épocas para aquecimento da taxa de aprendizado | `3` |
| `warmup_momentum` | Momentum inicial durante aquecimento | `0.8` |
| `warmup_bias_lr` | Taxa de aprendizado inicial para bias durante aquecimento | `0.1` |
| `box` | Peso da perda de box | `7.5` |
| `cls` | Peso da perda de classe | `0.5` |
| `dfl` | Peso da perda focal de distribuição | `1.5` |
| `fl_gamma` | Gamma para focal loss | `0.0` |
| `workers` | Número de workers para carregamento de dados | `8` |
| `cos_lr` | Usar cronograma de taxa de aprendizado de coseno | `true` |

## Configuração de Dataset

A seção `dataset` controla a divisão e processamento do dataset:

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `train_ratio` | Proporção de dados para treinamento | `0.7` |
| `val_ratio` | Proporção de dados para validação | `0.15` |
| `test_ratio` | Proporção de dados para teste | `0.15` |
| `seed` | Semente aleatória para divisões reproduzíveis | `42` |
| `cache` | Cache de imagens na RAM durante treinamento | `true` |
| `rect` | Usar treinamento retangular (mantém proporção) | `false` |
| `mosaic` | Probabilidade de augmentação de mosaico | `1.0` |
| `mixup` | Probabilidade de augmentação de mixup | `0.5` |
| `copy_images` | Copiar imagens para diretório do dataset | `true` |

## Configuração de Augmentação de Dados

A seção `augmentation` controla os parâmetros de augmentação de dados:

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `factor` | Número de imagens aumentadas por original | `20` |
| `brightness_range` | Intervalo de ajuste de brilho [min, max] | `[0.8, 1.2]` |
| `contrast_range` | Intervalo de ajuste de contraste [min, max] | `[-30, 30]` |
| `flip_probability` | Probabilidade de flip horizontal | `0.5` |
| `rotation_range` | Intervalo de rotação em graus [min, max] | `[-15, 15]` |
| `noise_probability` | Probabilidade de adicionar ruído | `0.3` |
| `blur_probability` | Probabilidade de aplicar blur | `0.2` |
| `cutout_probability` | Probabilidade de aplicar cutout | `0.2` |
| `cutout_size` | Intervalo de tamanho de cutout como fração [min, max] | `[0.05, 0.2]` |
| `hue_shift` | Deslocamento máximo de matiz | `0.1` |
| `saturation_shift` | Deslocamento máximo de saturação | `0.1` |

## Configuração de Avaliação

A seção `evaluation` controla os parâmetros de avaliação do modelo:

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `conf_threshold` | Limiar de confiança para detecções | `0.25` |
| `iou_threshold` | Limiar de IoU para correspondência | `0.45` |
| `max_detections` | Máximo de detecções por imagem | `300` |
| `save_confusion_matrix` | Gerar e salvar matriz de confusão | `true` |
| `save_json` | Salvar resultados como JSON | `true` |
| `verbose` | Mostrar saída detalhada | `true` |
| `plots` | Gerar gráficos de avaliação | `true` |

## Configuração de Conversão de Imagem

A seção `conversion` controla os parâmetros de conversão de imagem:

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `format` | Formato alvo da imagem (png, jpg) | `png` |
| `quality` | Configuração de qualidade JPG (1-100) | `95` |
| `use_opencv` | Usar OpenCV em vez de PIL | `true` |
| `delete_original` | Excluir arquivo original após conversão | `false` |
| `preserve_metadata` | Preservar metadados EXIF | `true` |
| `resize` | Redimensionar imagens durante conversão | `false` |
| `max_size` | Dimensões máximas após redimensionamento [largura, altura] | `[1024, 1024]` |

## Configuração de Anotação

A seção `annotation` controla os parâmetros da ferramenta de anotação:

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `box_thickness` | Espessura da linha da caixa delimitadora | `2` |
| `text_size` | Tamanho do texto para rótulos | `0.5` |
| `auto_save` | Habilitar salvamento automático de anotações | `true` |
| `auto_save_interval` | Segundos entre auto-saves | `300` |
| `undo_levels` | Número de operações de desfazer suportadas | `10` |

## Configuração do AWS CodeArtifact

A seção `aws` controla a integração com AWS CodeArtifact para atualizações:

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `domain` | Nome do domínio AWS CodeArtifact | `seu-dominio` |
| `repository` | Nome do repositório AWS CodeArtifact | `seu-repositorio` |
| `region` | Região AWS | `us-east-1` |
| `auto_check` | Verificar atualizações automaticamente | `true` |
| `check_interval` | Intervalo de verificação de atualização em segundos | `86400` (1 dia) |

## Configuração de Logging

A seção `logging` controla o comportamento de logging:

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `level` | Nível de logging (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `file` | Caminho do arquivo de log | `microdetect.log` |
| `format` | Formato da mensagem de log | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` |
| `max_size` | Tamanho máximo do arquivo de log em bytes | `10485760` (10MB) |
| `backup_count` | Número de backups de log para manter | `3` |

## Configuração de Cache

A seção `caching` controla o comportamento de cache:

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `enabled` | Habilitar cache | `true` |
| `directory` | Diretório de cache | `~/.cache/microdetect` |
| `max_size_gb` | Tamanho máximo de cache em GB | `10` |
| `ttl` | Tempo de vida para itens em cache em segundos | `604800` (7 dias) |
| `compression` | Usar compressão para itens em cache | `true` |

## Configuração de Inferência

A seção `inference` controla o comportamento de detecção e inferência:

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `conf_threshold` | Limiar de confiança para detecção | `0.25` |
| `iou_threshold` | Limiar de IoU para NMS | `0.45` |
| `max_detections` | Número máximo de detecções por imagem | `300` |
| `agnostic_nms` | Non-Maximum Suppression agnóstico de classe | `false` |
| `show_labels` | Mostrar rótulos de classe nas detecções | `true` |
| `show_conf` | Mostrar pontuações de confiança nas detecções | `true` |
| `save_crops` | Salvar recortes de objetos detectados | `false` |
| `hide_conf` | Ocultar valores de confiança na saída | `false` |
| `hide_labels` | Ocultar rótulos de classe na saída | `false` |
| `half` | Usar FP16 (meia precisão) para inferência | `false` |