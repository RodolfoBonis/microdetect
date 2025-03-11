# MicroDetect

![Versão](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Licença](https://img.shields.io/badge/license-PROPRIETARY-green)

**MicroDetect** é uma ferramenta completa para detecção e classificação de microorganismos em imagens de microscopia utilizando YOLOv8. Este projeto fornece uma pipeline completa desde a conversão de imagens, anotação manual, augmentação de dados, treinamento até avaliação de modelos.

## Idiomas da Documentação
[Inglês](README.md) | [Português](README.pt.md)(Atual)

## Principais Recursos

- 🔍 **Conversão de Imagens**: Converte imagens TIFF para formatos adequados ao processamento
- 🏷️ **Anotação Manual**: Interface gráfica para marcação de microorganismos em imagens
- 👁️ **Visualização**: Visualiza anotações existentes em imagens
- 🔄 **Augmentação de Dados**: Melhora o conjunto de dados com técnicas de augmentação
- 📊 **Preparação de Dataset**: Divide e organiza dados para treinamento/validação/teste
- 🧠 **Treinamento de Modelos**: Treina modelos YOLOv8 personalizados com suas imagens
- 📈 **Avaliação**: Avalia modelos com métricas detalhadas e relatórios visuais

## Microorganismos Suportados

- 🦠 **Leveduras**
- 🍄 **Fungos**
- 🌱 **Micro-algas**

## Instalação

### Pré-requisitos

- Python 3.12 ou superior
- Conda (recomendado para gerenciamento de ambiente)

### Configuração com Conda (Recomendado)

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/microdetect.git
cd microdetect

# Configurar ambiente
chmod +x scripts/setup.sh
./scripts/setup.sh --create

# Ativar ambiente
conda activate yeast_detection

# Instalar dependências
./scripts/setup.sh --install
```

### Configuração no Windows

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/microdetect.git
cd microdetect

# Configurar ambiente
scripts\setup.bat --create

# Ativar ambiente
conda activate yeast_detection

# Instalar dependências
scripts\setup.bat --install
```

### Instalação Manual

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/microdetect.git
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

### Conversão de Imagens TIFF para PNG

```bash
microdetect convert --input_dir data/raw_images --output_dir data/images --use_opencv
```

### Anotação Manual de Imagens

```bash
microdetect annotate --image_dir data/images --output_dir data/labels
```

### Visualização de Anotações

```bash
microdetect visualize --image_dir data/images --label_dir data/labels
```

### Augmentação de Dados

```bash
microdetect augment --image_dir data/images --label_dir data/labels --factor 10
```

### Preparação de Dataset

```bash
microdetect dataset --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset
```

### Treinamento de Modelo

```bash
microdetect train --dataset_dir dataset --model_size s --epochs 100
```

### Avaliação de Modelo

```bash
microdetect evaluate --model_path runs/train/yolov8_s_custom/weights/best.pt --dataset_dir dataset --confusion_matrix
```

## Estrutura do Projeto

```
microdetect/
├── README.md                  # Documentação principal
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
    ├── setup.sh               # Configuração no Linux/Mac
    └── setup.bat              # Configuração no Windows
```

## Estrutura dos Datasets

O projeto segue a estrutura padrão do YOLOv8:

```
dataset/
├── train/                     # Dados de treinamento
│   ├── images/                # Imagens para treinamento
│   └── labels/                # Anotações em formato YOLO
├── val/                       # Dados de validação
│   ├── images/
│   └── labels/
├── test/                      # Dados de teste
│   ├── images/
│   └── labels/
└── data.yaml                  # Configuração do dataset
```

## Formato das Anotações

As anotações seguem o formato YOLO:

```
<class_id> <x_center> <y_center> <width> <height>
```

Onde:
- `class_id`: ID da classe (0=levedura, 1=fungo, 2=micro-alga)
- `x_center`, `y_center`: Coordenadas normalizadas (0-1) do centro da caixa
- `width`, `height`: Largura e altura normalizadas (0-1) da caixa

## Uso com Makefile

O projeto inclui um Makefile para conveniência:

```bash
# Criar diretórios
make create-dirs

# Anotar imagens
make annotate

# Preparar dataset
make prepare-data

# Treinar modelo
make train

# Pipeline completa
make pipeline
```

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

Para questões, sugestões ou colaborações, entre em contato:

- Email: contato@exemplo.com
- GitHub Issues: [https://github.com/seu-usuario/microdetect/issues](https://github.com/seu-usuario/microdetect/issues)