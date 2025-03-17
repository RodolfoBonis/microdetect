# Guia de Augmentação de Dados

Este guia explica como usar as ferramentas de augmentação de dados do MicroDetect para melhorar seu dataset, aumentar sua diversidade e melhorar o desempenho do modelo.

## Visão Geral

A augmentação de dados é uma técnica para expandir artificialmente seu dataset, criando versões modificadas de imagens existentes. Isso ajuda a:

- Aumentar o tamanho do seu dataset de treinamento
- Melhorar a generalização do modelo
- Tornar o modelo mais robusto a variações de iluminação, orientação e ruído
- Reduzir o overfitting, especialmente ao trabalhar com datasets pequenos

O MicroDetect fornece um conjunto abrangente de técnicas de augmentação especificamente adaptadas para imagens de microscopia.

## Uso Básico

### Interface de Linha de Comando

A maneira mais simples de aumentar seu dataset é através da linha de comando:

```bash
microdetect augment --image_dir data/imagens --label_dir data/labels --output_image_dir data/aumentadas/imagens --output_label_dir data/aumentadas/labels --factor 5
```

Este comando irá:
1. Carregar imagens de `data/imagens` e seus rótulos correspondentes de `data/labels`
2. Gerar 5 versões aumentadas de cada imagem
3. Salvar as imagens aumentadas e rótulos atualizados nos diretórios de saída especificados

### Opções de Linha de Comando

| Parâmetro | Descrição | Padrão |
|-----------|-------------|---------|
| `--image_dir` | Diretório contendo imagens originais | |
| `--label_dir` | Diretório contendo rótulos originais | |
| `--output_image_dir` | Diretório para imagens aumentadas | Mesmo que `image_dir` |
| `--output_label_dir` | Diretório para rótulos aumentados | Mesmo que `label_dir` |
| `--factor` | Número de versões aumentadas por imagem | 5 |
| `--brightness_range` | Intervalo para ajuste de brilho | [0.8, 1.2] |
| `--contrast_range` | Intervalo para ajuste de contraste | [-30, 30] |
| `--flip_probability` | Probabilidade de espelhamento horizontal | 0.5 |
| `--rotation_range` | Intervalo para rotação em graus | [-15, 15] |
| `--noise_probability` | Probabilidade de adicionar ruído | 0.3 |

## Técnicas de Augmentação

A classe `DataAugmenter` do MicroDetect implementa várias técnicas de augmentação:

### Ajuste de Brilho e Contraste

Altera o brilho e contraste das imagens para simular diferentes condições de iluminação:

```bash
microdetect augment --image_dir imagens --label_dir labels --brightness_range 0.7,1.3 --contrast_range -40,40
```

### Espelhamento Horizontal

Espelha imagens horizontalmente com uma probabilidade especificada:

```bash
microdetect augment --image_dir imagens --label_dir labels --flip_probability 0.7
```

Obs: Os rótulos são automaticamente ajustados para imagens espelhadas.

### Rotação

Rotaciona imagens dentro de um intervalo especificado:

```bash
microdetect augment --image_dir imagens --label_dir labels --rotation_range -20,20
```

### Ruído Gaussiano

Adiciona ruído aleatório para simular ruído do sensor da câmera:

```bash
microdetect augment --image_dir imagens --label_dir labels --noise_probability 0.5
```

## Uso Avançado

### Usando a API Python

Para mais controle, você pode usar a classe `DataAugmenter` diretamente em Python:

```python
from microdetect.data.augmentation import DataAugmenter

# Inicializar com parâmetros personalizados
augmenter = DataAugmenter(
    brightness_range=(0.7, 1.3),
    contrast_range=(-40, 40),
    flip_probability=0.6,
    rotation_range=(-25, 25),
    noise_probability=0.4
)

# Aumentar dados
num_originais, num_aumentadas = augmenter.augment_data(
    input_image_dir="data/imagens",
    input_label_dir="data/labels",
    output_image_dir="data/aumentadas/imagens",
    output_label_dir="data/aumentadas/labels",
    augmentation_factor=8
)

print(f"Geradas {num_aumentadas} imagens aumentadas a partir de {num_originais} imagens originais")
```

### Pipeline de Augmentação Personalizado

Você pode criar pipelines de augmentação mais complexos combinando técnicas:

```python
import cv2
import numpy as np
from microdetect.data.augmentation import DataAugmenter

class AugmentadorPersonalizado(DataAugmenter):
    def augment_image(self, image, annotations):
        # Aplicar augmentações padrão
        augmented_image, augmented_annotations = super().augment_image(image, annotations)
        
        # Aplicar augmentações personalizadas adicionais
        
        # Exemplo: Ajuste de cor
        if np.random.random() < 0.3:
            # Converter para HSV e ajustar saturação
            hsv = cv2.cvtColor(augmented_image, cv2.COLOR_BGR2HSV)
            hsv[:,:,1] = hsv[:,:,1] * np.random.uniform(0.8, 1.2)
            augmented_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # Exemplo: Desfoque
        if np.random.random() < 0.2:
            augmented_image = cv2.GaussianBlur(augmented_image, (5, 5), 0)
            
        return augmented_image, augmented_annotations

# Usar o augmentador personalizado
augmentador_personalizado = AugmentadorPersonalizado()
augmentador_personalizado.augment_data("imagens", "labels", "aumentadas/imagens", "aumentadas/labels")
```

### Integração com Gerenciamento de Dataset

Ao preparar seu dataset, você pode incluir a augmentação como parte do fluxo de trabalho:

```bash
# Primeiro, crie a estrutura de seu dataset
microdetect dataset --source_img_dir original/imagens --source_label_dir original/labels

# Depois aumente o conjunto de treino
microdetect augment --image_dir dataset/train/images --label_dir dataset/train/labels --factor 5
```

Obs: Geralmente é recomendado aumentar apenas o conjunto de treino, não os conjuntos de validação ou teste.

## Melhores Práticas

### Estratégias de Augmentação por Tipo de Microorganismo

Diferentes microorganismos se beneficiam de diferentes estratégias de augmentação:

#### Para Leveduras
```bash
microdetect augment --image_dir imagens_leveduras --label_dir labels_leveduras \
                    --brightness_range 0.7,1.3 \
                    --contrast_range -30,30 \
                    --flip_probability 0.5 \
                    --rotation_range -180,180  # Leveduras frequentemente têm forma circular, então rotação completa é apropriada
```

#### Para Fungos com Hifas
```bash
microdetect augment --image_dir imagens_fungos --label_dir labels_fungos \
                    --brightness_range 0.8,1.2 \
                    --contrast_range -20,20 \
                    --flip_probability 0.5 \
                    --rotation_range -30,30  # Rotação limitada para manter formas características
```

#### Para Micro-algas
```bash
microdetect augment --image_dir imagens_algas --label_dir labels_algas \
                    --brightness_range 0.6,1.4  # Maior variação de brilho para imagens de fluorescência
                    --contrast_range -40,40 \
                    --flip_probability 0.5 \
                    --rotation_range -45,45
```

### Encontrando o Equilíbrio Certo

- Pouca augmentação: Melhoria limitada na generalização
- Muita augmentação: Risco de criar imagens irrealistas

Comece com configurações moderadas e ajuste com base no desempenho do modelo:

1. Treine sem augmentação como baseline
2. Adicione augmentação leve e compare métricas de validação
3. Aumente gradualmente a intensidade da augmentação até que as métricas de validação estabilizem ou declinem

### Considerações sobre Tamanho do Dataset

- Datasets pequenos (<100 imagens): Augmentação mais agressiva (fator 10-20)
- Datasets médios (100-1000 imagens): Augmentação moderada (fator 5-10)
- Datasets grandes (>1000 imagens): Augmentação leve (fator 2-5)

## Avaliando o Impacto da Augmentação

Para avaliar a eficácia da sua estratégia de augmentação:

```bash
# Treinar um modelo sem augmentação
microdetect train --dataset_dir dataset_original --output_dir runs/sem_augmentacao

# Treinar um modelo com augmentação
microdetect augment --image_dir dataset_original/train/images --label_dir dataset_original/train/labels
microdetect train --dataset_dir dataset_original --output_dir runs/com_augmentacao

# Comparar os resultados
microdetect compare_results --result_dirs runs/sem_augmentacao,runs/com_augmentacao
```

## Solução de Problemas

### Problemas Comuns

| Problema | Solução |
|----------|---------|
| Anotações aumentadas fora dos limites da imagem | Reduzir o intervalo de rotação ou implementar verificação de limites |
| Brilho/contraste irrealista | Reduzir os intervalos de brilho/contraste |
| Muito ruído degrada a qualidade da imagem | Reduzir a probabilidade ou intensidade do ruído |
| Tempo de processamento longo | Considere usar menos augmentações por imagem ou processar em lotes |

## Próximos Passos

Após aumentar seu dataset:

- [Guia de Treinamento](training_guide.md) - Treine seu modelo YOLOv8 usando seu dataset aumentado
- [Guia de Avaliação](model_evaluation_analysis.md) - Avalie o impacto da augmentação no desempenho do modelo