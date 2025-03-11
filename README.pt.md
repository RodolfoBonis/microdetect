# MicroDetect

![Versão](https://img.shields.io/badge/versão-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)
![Licença](https://img.shields.io/badge/licença-MIT-green)

*Read this in [English](README.md)*

**MicroDetect** é uma ferramenta completa para detecção e classificação de microorganismos em imagens de microscopia utilizando YOLOv8. Este projeto fornece uma pipeline completa desde a conversão de imagens, anotação manual com sistema de retomada, augmentação de dados, treinamento com checkpoints até avaliação de modelos.

## Índice

- [Principais Recursos](#principais-recursos)
- [Microorganismos Suportados](#microorganismos-suportados)
- [Instalação](#instalação)
- [Guia Rápido](#guia-rápido)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Funcionalidades Detalhadas](#funcionalidades-detalhadas)
  - [Conversão de Imagens](#conversão-de-imagens)
  - [Anotação Manual com Retomada](#anotação-manual-com-retomada)
  - [Visualização de Anotações](#visualização-de-anotações)
  - [Preparação de Dataset](#preparação-de-dataset)
  - [Augmentação de Dados](#augmentação-de-dados)
  - [Treinamento com Checkpoints](#treinamento-com-checkpoints)
  - [Avaliação de Modelos](#avaliação-de-modelos)
- [Configuração Personalizada](#configuração-personalizada)
- [Uso com Makefile](#uso-com-makefile)
- [Contribuição](#contribuição)
- [Licença](#licença)
- [Contato](#contato)

## Principais Recursos

- 🔍 **Conversão de Imagens**: Converte imagens TIFF para formatos adequados ao processamento
- 🏷️ **Anotação Manual com Retomada**: Interface gráfica para marcação de microorganismos com capacidade de salvar progresso e retomar de onde parou
- 👁️ **Visualização**: Visualiza anotações existentes em imagens
- 🔄 **Augmentação de Dados**: Melhora o conjunto de dados com técnicas de augmentação
- 📊 **Preparação de Dataset**: Divide e organiza dados para treinamento/validação/teste
- 🧠 **Treinamento com Checkpoints**: Treina modelos YOLOv8 personalizados com sistema de checkpoints para retomada
- 📈 **Avaliação**: Avalia modelos com métricas detalhadas e relatórios visuais

## Microorganismos Suportados

- 🦠 **Leveduras**
- 🍄 **Fungos**
- 🌱 **Micro-algas**

## Instalação

### Pré-requisitos

- Python 3.9 ou superior
- Conda (recomendado para gerenciamento de ambiente)

### Configuração com Conda (Recomendado)

```bash
# Clonar o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Configurar ambiente
chmod +x scripts/install_production_robust.sh
./scripts/install_production.sh

# OU para criar um ambiente virtual
./scripts/install_production.sh --virtual-env

# Para criar também um projeto exemplo
./scripts/install_production.sh --with-example
```

### Configuração no Windows

```bash
# Clonar o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Configurar ambiente
scripts\install_production.bat

# OU para criar um ambiente virtual
scripts\install_production.bat --virtual-env

# Para criar também um projeto exemplo
scripts\install_production.bat --with-example
```

### Instalação Manual

```bash
# Clonar o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
pip install -e .
```

## Guia Rápido

### Inicializar Projeto

```bash
# Criar um diretório para seu projeto
mkdir meu_projeto
cd meu_projeto

# Inicializar o MicroDetect
microdetect init
```

### Conversão de Imagens TIFF para PNG

```bash
microdetect convert --input_dir data/raw_images --output_dir data/images --use_opencv
```

### Anotação Manual de Imagens (com sistema de retomada)

```bash
microdetect annotate --image_dir data/images --output_dir data/labels
```

### Visualização de Anotações

```bash
microdetect visualize --image_dir data/images --label_dir data/labels
```

### Preparação de Dataset

```bash
microdetect dataset --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset
```

### Augmentação de Dados

```bash
microdetect augment --image_dir data/images --label_dir data/labels --factor 10
```

### Treinamento de Modelo

```bash
microdetect train --dataset_dir dataset --model_size s --epochs 100
```

### Retomada de Treinamento de um Checkpoint

```bash
microdetect train --resume runs/train/yolov8_s_custom/weights/last.pt --dataset_dir dataset --epochs 50
```

### Avaliação de Modelo

```bash
microdetect evaluate --model_path runs/train/yolov8_s_custom/weights/best.pt --dataset_dir dataset --confusion_matrix
```

## Estrutura do Projeto

```
microdetect/
├── README.md                  # Documentação principal
├── README_PT.md               # Documentação em português
├── requirements.txt           # Dependências do projeto
├── setup.py                   # Script de instalação
├── Makefile                   # Comandos make para automação
├── config.yaml                # Configuração central do projeto
├── microdetect/               # Pacote principal
│   ├── __init__.py            # Inicialização do pacote
│   ├── cli.py                 # Interface de linha de comando
│   ├── data/                  # Módulos de processamento de dados
│   │   ├── __init__.py
│   │   ├── augmentation.py    # Augmentação de imagens
│   │   ├── conversion.py      # Conversão de formatos
│   │   └── dataset.py         # Gerenciamento de datasets
│   ├── annotation/            # Módulos de anotação
│   │   ├── __init__.py
│   │   ├── annotator.py       # Ferramenta de anotação
│   │   └── visualization.py   # Visualização de anotações
│   ├── training/              # Módulos de treinamento
│   │   ├── __init__.py
│   │   ├── train.py           # Treinamento de modelos
│   │   └── evaluate.py        # Avaliação de modelos
│   └── utils/                 # Funções e classes utilitárias
│       ├── __init__.py
│       └── config.py          # Gerenciamento de configuração
└── scripts/                   # Scripts auxiliares
    ├── install_production_robust.sh  # Instalação em Linux/Mac
    └── install_production_robust.bat # Instalação em Windows
```

## Funcionalidades Detalhadas

### Conversão de Imagens

O módulo de conversão permite transformar imagens TIFF em formatos mais adequados para processamento, como PNG:

```bash
# Uso básico
microdetect convert --input_dir data/raw_images --output_dir data/images

# Com OpenCV para melhor processamento de imagens de 16 bits
microdetect convert --input_dir data/raw_images --output_dir data/images --use_opencv

# Excluir arquivos originais após conversão
microdetect convert --input_dir data/raw_images --output_dir data/images --delete_original
```

A conversão é especialmente importante para imagens de microscopia, que frequentemente são salvas em formatos TIFF de alta resolução.

### Anotação Manual com Retomada

O sistema de anotação possui uma interface gráfica completa para marcar microorganismos e permite retomar o trabalho de onde você parou:

```bash
microdetect annotate --image_dir data/images --output_dir data/labels
```

**Características principais:**

- Carrega automaticamente anotações existentes ao editar uma imagem
- Salva progresso para retomada posterior
- Permite pausar e continuar de onde parou
- Opções para pular, editar ou sobrescrever anotações existentes

**Atalhos de teclado:**

- **R**: Reiniciar (limpar todas as anotações da imagem atual)
- **D**: Excluir a última caixa desenhada
- **S**: Salvar anotações e ir para próxima imagem
- **Q**: Sair sem salvar
- **E**: Salvar anotação atual e sair (para retomar depois)

Quando você reinicia a ferramenta de anotação, ela pergunta se deseja retomar do ponto onde parou anteriormente.

### Visualização de Anotações

Para revisar as anotações feitas:

```bash
# Visualização interativa
microdetect visualize --image_dir data/images --label_dir data/labels

# Salvar imagens com anotações desenhadas
microdetect visualize --image_dir data/images --label_dir data/labels --output_dir data/annotated_images

# Filtrar classes específicas
microdetect visualize --image_dir data/images --label_dir data/labels --filter_classes "0,1"
```

A visualização permite navegar entre imagens usando as teclas:
- 'n': próxima imagem
- 'p': imagem anterior
- '0'-'9': alternar visibilidade de classes
- 's': salvar imagem atual com anotações
- 'q': sair

### Preparação de Dataset

Organiza seu dataset em estrutura para treinamento:

```bash
microdetect dataset --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset
```

Isso cria:
- Divisão em treino/validação/teste
- Arquivo de configuração YAML para o treinamento
- Estrutura de diretórios compatível com YOLOv8

Você pode personalizar as proporções:

```bash
microdetect dataset --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset --train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1
```

### Augmentação de Dados

Aumenta seu dataset com variações automáticas:

```bash
microdetect augment --image_dir data/images --label_dir data/labels --factor 10
```

Técnicas de augmentação aplicadas:
- Variação de brilho e contraste
- Espelhamento horizontal
- Rotação leve
- Adição de ruído gaussiano

Os parâmetros de augmentação podem ser personalizados no `config.yaml`.

### Treinamento com Checkpoints

Treina modelos YOLOv8 com sistema de checkpoints:

```bash
# Treinamento básico
microdetect train --dataset_dir dataset --model_size s --epochs 100

# Configuração avançada
microdetect train --dataset_dir dataset --model_size m --epochs 200 --batch_size 16 --image_size 640
```

**Sistema de Checkpoints:**

O treinamento salva automaticamente:
- O melhor modelo (`best.pt`)
- O modelo mais recente (`last.pt`)
- Estado do otimizador e métricas

Para retomar um treinamento interrompido:

```bash
microdetect train --resume runs/train/yolov8_s_custom/weights/last.pt --dataset_dir dataset --epochs 50
```

### Avaliação de Modelos

Avalie o desempenho do modelo treinado:

```bash
microdetect evaluate --model_path runs/train/yolov8_s_custom/weights/best.pt --dataset_dir dataset
```

Para gerar uma matriz de confusão:

```bash
microdetect evaluate --model_path runs/train/yolov8_s_custom/weights/best.pt --dataset_dir dataset --confusion_matrix
```

Os relatórios de avaliação incluem:
- Precisão (mAP50, mAP50-95)
- Recall
- F1-Score
- Métricas por classe
- Gráficos de desempenho
- Matriz de confusão (opcional)

## Configuração Personalizada

O MicroDetect usa um arquivo `config.yaml` para configuração centralizada. Quando você executa `microdetect init`, esse arquivo é criado no diretório atual com valores padrão.

Exemplo de personalização:

```yaml
# config.yaml
directories:
  dataset: ./meu_dataset
  images: ./minhas_imagens
  labels: ./minhas_anotacoes

classes:
  - "0-levedura"
  - "1-fungo"
  - "2-micro-alga"
  - "3-minha-nova-classe"

training:
  model_size: m
  epochs: 300
  batch_size: 16
```

Após personalizar, os comandos usarão automaticamente esses valores como padrão.

## Uso com Makefile

O projeto inclui um Makefile para automação de tarefas:

```bash
# Criar diretórios
make create-dirs

# Converter imagens TIFF
make convert-tiff

# Anotar imagens
make annotate

# Visualizar anotações
make visualize

# Preparar dataset
make prepare-data

# Aplicar augmentação
make augment

# Treinar modelo
make train

# Avaliar modelo
make evaluate

# Pipeline completa
make pipeline
```

Você pode personalizar parâmetros:

```bash
make train MODEL_SIZE=m EPOCHS=200 BATCH_SIZE=16
```

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

Para questões, sugestões ou colaborações, entre em contato:

- Email: dev@rodolfodebonis.com.br
- GitHub Issues: [https://github.com/RodolfoBonis/microdetect/issues](https://github.com/RodolfoBonis/microdetect/issues)