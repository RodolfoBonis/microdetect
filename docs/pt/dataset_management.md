# Guia de Gerenciamento de Dataset

Este guia explica como organizar, dividir e preparar eficientemente seu dataset para treinamento usando as ferramentas de gerenciamento de dataset do MicroDetect.

## Visão Geral

O gerenciamento adequado do dataset é crucial para o sucesso do treinamento do modelo. O MicroDetect fornece um conjunto abrangente de ferramentas para organizar suas imagens anotadas na estrutura apropriada para treinamento YOLOv8, validar seus dados e gerar os arquivos de configuração necessários.

## Estrutura do Dataset

O MicroDetect requer uma estrutura de diretórios específica para treinamento:

```
dataset/
├── train/
│   ├── images/
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   └── ...
│   └── labels/
│       ├── image1.txt
│       ├── image2.txt
│       └── ...
├── val/
│   ├── images/
│   │   └── ...
│   └── labels/
│       └── ...
├── test/
│   ├── images/
│   │   └── ...
│   └── labels/
│       └── ...
└── data.yaml
```

A classe `DatasetManager` lida com a criação desta estrutura automaticamente.

## Uso Básico

### Criando um Dataset

A maneira mais simples de criar um dataset é usar o comando `microdetect dataset`:

```bash
microdetect dataset --source_img_dir data/imagens --source_label_dir data/labels
```

Este comando irá:
1. Criar a estrutura de diretórios apropriada
2. Dividir seus dados em conjuntos de treino/validação/teste
3. Gerar um arquivo de configuração `data.yaml`

### Opções de Linha de Comando

| Parâmetro | Descrição | Padrão |
|-----------|-------------|---------|
| `--source_img_dir` | Diretório contendo imagens anotadas | |
| `--source_label_dir` | Diretório contendo arquivos de rótulos | |
| `--dataset_dir` | Diretório de saída para o dataset | `dataset` |
| `--train_ratio` | Proporção de dados para treinamento | 0.7 |
| `--val_ratio` | Proporção de dados para validação | 0.15 |
| `--test_ratio` | Proporção de dados para teste | 0.15 |
| `--seed` | Semente aleatória para reprodutibilidade | 42 |

## Gerenciamento Avançado de Dataset

### Usando a API Python

Para mais controle, você pode usar a classe `DatasetManager` diretamente em Python:

```python
from microdetect.data.dataset import DatasetManager

# Inicializar com parâmetros personalizados
dataset_manager = DatasetManager(
    dataset_dir="dataset_personalizado",
    train_ratio=0.8,
    val_ratio=0.1,
    test_ratio=0.1,
    seed=123
)

# Criar estrutura de diretórios
dataset_manager.prepare_directory_structure()

# Dividir o dataset
split_counts = dataset_manager.split_dataset(
    source_img_dir="data/imagens_preprocessadas",
    source_label_dir="data/anotacoes"
)
print(f"Dataset dividido: {split_counts}")

# Criar configuração YAML
yaml_path = dataset_manager.create_data_yaml()
print(f"Arquivo de configuração criado: {yaml_path}")
```

### Configuração Personalizada de Classes

Você pode especificar seus próprios nomes de classe:

```python
# No arquivo config.yaml
classes:
  - "0-levedura"
  - "1-fungo"
  - "2-micro-alga"
  - "3-bacteria"
```

Ou usando a API Python:

```python
from microdetect.data.dataset import DatasetManager
from microdetect.utils.config import config

# Definir classes
config.set("classes", ["0-levedura", "1-fungo", "2-micro-alga", "3-bacteria"])

# Inicializar gerenciador de dataset
dataset_manager = DatasetManager()

# Prosseguir com a preparação do dataset
```

## Validação de Dataset

### Verificando a Integridade do Dataset

O MicroDetect fornece ferramentas para validar seu dataset:

```bash
microdetect validate_dataset --dataset_dir dataset
```

Isso verifica:
- Arquivos de imagem ausentes
- Arquivos de rótulo ausentes
- Imagens corrompidas
- Formatos de rótulo inválidos
- Desequilíbrio na distribuição de classes

### Visualizando a Distribuição de Classes

Examine o equilíbrio de classes em seu dataset:

```bash
microdetect dataset_stats --dataset_dir dataset --visualize
```

Isso gera visualizações mostrando:
- Distribuição de classes entre as divisões de treino/validação/teste
- Contagem de amostras por classe
- Distribuição de tamanho e proporção das amostras

## Trabalhando com Datasets Existentes

### Importando de Outros Formatos

O MicroDetect pode importar datasets de outros formatos comuns:

```bash
# Importar do formato COCO
microdetect import_dataset --source dataset_coco --format coco --output dataset

# Importar do formato VOC
microdetect import_dataset --source dataset_voc --format pascal_voc --output dataset

# Importar do formato CreateML
microdetect import_dataset --source dataset_createml --format createml --output dataset
```

### Mesclando Múltiplos Datasets

Combine datasets de diferentes fontes:

```bash
microdetect merge_datasets --sources dataset1,dataset2,dataset3 --output dataset_mesclado
```

## Configuração de Validação Cruzada

Para validação cruzada k-fold:

```bash
microdetect create_cv_folds --dataset_dir dataset --k 5 --output_dir datasets_cv
```

Isso cria 5 diferentes divisões de treino/validação para validação cruzada, mantendo o conjunto de teste consistente.

## Melhores Práticas

### Equilíbrio de Classes

Busque uma distribuição equilibrada de classes. Se seu dataset for desequilibrado:

```bash
# Analisar distribuição de classes
microdetect dataset_stats --dataset_dir dataset

# Equilibrar dataset por oversampling de classes minoritárias
microdetect balance_dataset --dataset_dir dataset --method oversample
```

### Divisão Treino/Validação/Teste

A divisão padrão (70% treino, 15% validação, 15% teste) funciona bem para a maioria dos casos, mas considere:
- Mais dados de treinamento (80/10/10) para datasets menores
- Mais dados de validação (60/20/20) ao ajustar hiperparâmetros

### Prevenção de Vazamento de Dados

Garanta que imagens semelhantes não apareçam em diferentes divisões:

```bash
# Verificar potencial vazamento de dados
microdetect check_leakage --dataset_dir dataset

# Dividir por grupos (ex: por lâmina ou amostra) em vez de aleatoriamente
microdetect dataset --source_img_dir imagens --source_label_dir labels --group_by id_lamina
```

## Solução de Problemas

### Problemas Comuns

| Problema | Solução |
|----------|---------|
| Distribuição desequilibrada de classes | Use o comando `balance_dataset` para fazer oversampling de classes minoritárias |
| Rótulos ausentes | Use `find_missing_labels` para identificar imagens sem anotações |
| Configuração YAML inválida | Valide seu data.yaml com o comando `validate_yaml` |
| Dataset muito pequeno | Considere técnicas de augmentação de dados (veja [Guia de Augmentação de Dados](data_augmentation.md)) |

## Próximos Passos

Após preparar seu dataset:

- [Guia de Augmentação de Dados](data_augmentation.md) - Melhore seu dataset com augmentação
- [Guia de Treinamento](training_guide.md) - Treine seu modelo YOLOv8 usando seu dataset preparado