# Configuração Avançada do MicroDetect

Este documento explica todas as opções de configuração avançada disponíveis no MicroDetect para personalizar e otimizar seu funcionamento.

## Arquivo de Configuração

O MicroDetect usa um arquivo `config.yaml` centralizado para a maioria das configurações. Este arquivo é criado automaticamente quando você executa `microdetect init` e pode ser editado manualmente.

### Localização do Arquivo de Configuração

O sistema busca o arquivo de configuração nos seguintes locais, em ordem de prioridade:

1. Caminho especificado manualmente em comandos
2. Diretório atual (`./config.yaml`)
3. Diretório do usuário (`~/.microdetect/config.yaml`)
4. Configuração padrão interna do pacote

### Estrutura Completa de config.yaml

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
  "0": [0, 255, 0]                # Verde para levedura (formato RGB)
  "1": [0, 0, 255]                # Vermelho para fungo
  "2": [255, 0, 0]                # Azul para micro-alga
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
  warmup_bias_lr: 0.1             # Learning rate de bias durante aquecimento
  box: 7.5                        # Peso da loss de box
  cls: 0.5                        # Peso da loss de classe
  dfl: 1.5                        # Peso da loss DFL
  fl_gamma: 0.0                   # Focal loss gamma
  workers: 8                      # Número de workers para carregamento de dados
  cos_lr: true                    # Usar aprendizado coseno

# Parâmetros para divisão do dataset
dataset:
  train_ratio: 0.7                # Proporção para treinamento
  val_ratio: 0.15                 # Proporção para validação
  test_ratio: 0.15                # Proporção para teste
  seed: 42                        # Semente para reprodutibilidade
  cache: true                     # Cachear imagens em RAM
  rect: false                     # Usar recortes retangulares
  mosaic: 1.0                     # Probabilidade de mosaico
  mixup: 0.5                      # Probabilidade de mixup
  copy_images: true               # Copiar imagens para diretório do dataset

# Parâmetros para augmentação de dados
augmentation:
  factor: 20                      # Número de imagens a gerar por original
  brightness_range: [0.8, 1.2]    # Intervalo de brilho (min, max)
  contrast_range: [-30, 30]       # Intervalo de contraste (min, max)
  flip_probability: 0.5           # Probabilidade de flip horizontal
  rotation_range: [-15, 15]       # Intervalo de rotação (min, max)
  noise_probability: 0.3          # Probabilidade de ruído
  blur_probability: 0.2           # Probabilidade de desfoque
  cutout_probability: 0.2         # Probabilidade de cutout
  cutout_size: [0.05, 0.2]        # Tamanho do cutout (min%, max%)
  hue_shift: 0.1                  # Mudança de matiz
  saturation_shift: 0.1           # Mudança de saturação

# Parâmetros para avaliação
evaluation:
  conf_threshold: 0.25            # Threshold de confiança
  iou_threshold: 0.45             # Threshold de IoU
  max_detections: 300             # Máximo de detecções
  save_confusion_matrix: true     # Salvar matriz de confusão
  save_json: true                 # Salvar resultados em JSON
  verbose: true                   # Saída detalhada
  plots: true                     # Gerar gráficos

# Parâmetros para conversão de imagens
conversion:
  format: png                     # Formato alvo (png, jpg)
  quality: 95                     # Qualidade para JPG
  use_opencv: true                # Usar OpenCV em vez de PIL
  delete_original: false          # Excluir arquivo original após conversão
  preserve_metadata: true         # Preservar metadados EXIF
  resize: false                   # Redimensionar imagens
  max_size: [1024, 1024]          # Tamanho máximo após redimensionamento

# Parâmetros para anotação
annotation:
  box_thickness: 2                # Espessura das caixas
  text_size: 0.5                  # Tamanho do texto
  auto_save: true                 # Salvar anotações automaticamente
  auto_save_interval: 300         # Intervalo para auto-save (segundos)
  undo_levels: 10                 # Níveis de desfazer

# Parâmetros para AWS CodeArtifact
aws:
  domain: seu-dominio             # Nome do domínio CodeArtifact
  repository: seu-repositorio     # Nome do repositório
  region: us-east-1               # Região AWS
  auto_check: true                # Verificar atualizações automaticamente
  check_interval: 86400           # Intervalo entre verificações (segundos)

# Configurações de logging
logging:
  level: INFO                     # Nível de logging (DEBUG, INFO, WARNING, ERROR)
  file: microdetect.log           # Arquivo de log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Formato
  max_size: 10485760              # Tamanho máximo do arquivo de log (10MB)
  backup_count: 3                 # Número de backups
```

## Variáveis de Ambiente

Além do arquivo de configuração, o MicroDetect também respeita diversas variáveis de ambiente:

| Variável | Descrição | Valor Padrão |
|----------|-----------|--------------|
| `MICRODETECT_CONFIG_PATH` | Caminho para o arquivo de configuração | `./config.yaml` |
| `MICRODETECT_LOG_LEVEL` | Nível de logging | `INFO` |
| `MICRODETECT_SKIP_UPDATE_CHECK` | Desativar verificação de atualizações | Não definido |
| `MICRODETECT_CACHE_DIR` | Diretório de cache | `~/.cache/microdetect` |
| `AWS_CODEARTIFACT_DOMAIN` | Domínio AWS CodeArtifact | Configurado por `setup-aws` |
| `AWS_CODEARTIFACT_REPOSITORY` | Repositório AWS CodeArtifact | Configurado por `setup-aws` |
| `AWS_CODEARTIFACT_OWNER` | Proprietário do domínio AWS | Configurado por `setup-aws` |
| `CUDA_VISIBLE_DEVICES` | GPUs a serem usadas | Todas disponíveis |
| `OMP_NUM_THREADS` | Threads OpenMP | Número de CPUs |

## Configuração via Linha de Comando

Muitas configurações podem ser sobrescritas usando argumentos da linha de comando:

```bash
# Exemplo: sobrescrever configurações de treinamento
microdetect train --dataset_dir dataset --model_size m --epochs 200 --batch_size 16 --image_size 640
```

### Prioridade das Configurações

O MicroDetect usa a seguinte ordem de prioridade para determinar as configurações:

1. Argumentos da linha de comando
2. Variáveis de ambiente
3. Arquivo de configuração
4. Valores padrão internos

## Perfis de Configuração

Você pode manter vários perfis de configuração para diferentes casos de uso:

```bash
# Criar um novo perfil
cp config.yaml config_training.yaml

# Usar um perfil específico
microdetect train --config config_training.yaml
```

## Opções de Treinamento Avançadas

### Configurações de GPU

Para controlar o uso de GPU:

```bash
# Usar GPU específica
CUDA_VISIBLE_DEVICES=0 microdetect train --dataset_dir dataset

# Usar múltiplas GPUs (quando disponíveis)
microdetect train --dataset_dir dataset --device 0,1

# Forçar uso de CPU
microdetect train --dataset_dir dataset --device cpu
```

### Hyperparameter Tuning

O MicroDetect suporta busca de hiperparâmetros:

```bash
# Busca básica de hiperparâmetros
microdetect train --dataset_dir dataset --find_hyperparams

# Definir espaço de busca customizado (requer arquivo JSON)
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

Para configurar a inferência e detecção:

```yaml
# Em config.yaml
inference:
  conf_threshold: 0.25            # Threshold de confiança para detecção
  iou_threshold: 0.45             # Threshold de IoU para NMS
  max_detections: 300             # Número máximo de detecções
  agnostic_nms: false             # NMS agnóstico de classe
  show_labels: true               # Mostrar rótulos
  show_conf: true                 # Mostrar confiança
  save_crops: false               # Salvar recortes das detecções
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

# Defina seu callback
class CustomCallback(Callback):
    def on_train_start(self, trainer):
        print("Treinamento iniciado!")
    
    def on_train_end(self, trainer):
        print("Treinamento concluído!")

# Use com o treinador
trainer = YOLOTrainer()
trainer.model.add_callback("custom", CustomCallback())
trainer.train(data_yaml="dataset/data.yaml")
```

## Persistência de Configurações

Para salvar configurações frequentemente usadas, adicione-as ao arquivo `.env`:

```bash
# Criar/editar .env
echo "MICRODETECT_LOG_LEVEL=DEBUG" >> .env
echo "AWS_CODEARTIFACT_DOMAIN=meu-dominio" >> .env
```

Para carregar estas configurações automaticamente:

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

Para configuração detalhada do logging:

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

## Utilização de Cache

Para melhorar o desempenho com caching:

```yaml
# Em config.yaml
caching:
  enabled: true                   # Ativar caching
  directory: ~/.cache/microdetect  # Diretório de cache
  max_size_gb: 10                 # Tamanho máximo do cache (GB)
  ttl: 604800                     # TTL em segundos (7 dias)
  compression: true               # Usar compressão
```

## Usando Make para Configurações

O Makefile suporta sobrescrever qualquer configuração:

```bash
# Exemplo com várias configurações
make train MODEL_SIZE=m EPOCHS=200 BATCH_SIZE=16 IMAGE_SIZE=640 DOMAIN=meu-dominio
```

## Integração CI/CD

Para ambientes CI/CD, você pode usar variáveis de ambiente ou passar um arquivo de configuração:

```bash
# GitHub Actions exemplo
MICRODETECT_CONFIG_PATH=ci_config.yaml microdetect train --dataset_dir dataset --no-interactive
```

## Configuração Multi-Projeto

Para gerenciar múltiplos projetos:

```
projetos/
├── projeto1/
│   ├── config.yaml            # Configuração específica do projeto1
│   ├── data/
│   │   ├── images/
│   │   └── labels/
│   └── dataset/
├── projeto2/
│   ├── config.yaml            # Configuração específica do projeto2
│   ├── data/
│   │   ├── images/
│   │   └── labels/
│   └── dataset/
└── configuração_global.yaml   # Configurações compartilhadas
```

Cada projeto pode ter sua própria configuração, mas herdar configurações globais:

```bash
# Combinar configurações
python -c "import yaml; global_cfg=yaml.safe_load(open('configuração_global.yaml')); project_cfg=yaml.safe_load(open('projeto1/config.yaml')); merged_cfg={**global_cfg, **project_cfg}; print(yaml.dump(merged_cfg))" > projeto1/merged_config.yaml

# Usar configuração combinada
microdetect --config projeto1/merged_config.yaml train
```