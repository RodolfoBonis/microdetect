# Guia de Treinamento

Este guia explica como treinar modelos YOLOv8 para detecção de microorganismos usando as ferramentas de treinamento do MicroDetect.

## Visão Geral

O MicroDetect fornece um conjunto abrangente de ferramentas para treinar modelos YOLOv8, otimizados para detecção de microorganismos em imagens de microscopia. A classe `YOLOTrainer` simplifica o processo de treinamento, retomada de treinamento a partir de checkpoints e busca de hiperparâmetros ideais.

## Treinamento Básico

### Interface de Linha de Comando

A maneira mais simples de treinar um modelo é através da linha de comando:

```bash
microdetect train --dataset_dir dataset --model_size s --epochs 100 --batch_size 16 --image_size 640
```

Este comando irá:
1. Carregar a configuração do dataset de `dataset/data.yaml`
2. Inicializar um modelo YOLOv8s (variante pequena)
3. Treinar por 100 épocas com o tamanho de batch e tamanho de imagem especificados
4. Salvar os resultados no diretório `runs/train`

### Opções de Linha de Comando

| Parâmetro | Descrição | Padrão |
|-----------|-------------|---------|
| `--dataset_dir` | Diretório contendo o dataset | `dataset` |
| `--model_size` | Tamanho do modelo YOLOv8 (n, s, m, l, x) | `s` |
| `--epochs` | Número de épocas de treinamento | `100` |
| `--batch_size` | Tamanho do batch para treinamento | `16` |
| `--image_size` | Tamanho da imagem de entrada | `640` |
| `--pretrained` | Usar pesos pré-treinados | `True` |
| `--output_dir` | Diretório para salvar resultados | `runs/train` |

## Seleção de Tamanho do Modelo

O YOLOv8 vem em vários tamanhos, cada um com diferentes compromissos entre complexidade e desempenho:

| Tamanho do Modelo | Descrição | Caso de Uso Ideal |
|------------|-------------|----------------|
| `n` (nano) | Menor modelo, mais rápido mas menos preciso | Ambientes com recursos limitados, aplicações em tempo real |
| `s` (small) | Bom equilíbrio entre velocidade e precisão | Uso geral, desempenho equilibrado |
| `m` (medium) | Maior precisão que o small, ainda razoavelmente rápido | Melhor detecção quando os recursos permitem |
| `l` (large) | Alta precisão, mais lento que o medium | Priorização de precisão sobre velocidade |
| `x` (extra large) | Maior precisão, desempenho mais lento | Requisitos máximos de precisão |

Exemplo para treinar um modelo médio:

```bash
microdetect train --dataset_dir dataset --model_size m --epochs 150
```

## Treinamento Avançado

### Usando a API Python

Para mais controle, você pode usar a classe `YOLOTrainer` diretamente em Python:

```python
from microdetect.training.train import YOLOTrainer
from microdetect.data.dataset import DatasetManager

# Preparar dataset se necessário
dataset_manager = DatasetManager()
data_yaml = dataset_manager.create_data_yaml()

# Inicializar treinador com parâmetros personalizados
trainer = YOLOTrainer(
    model_size="m",
    epochs=150,
    batch_size=8,
    image_size=800,
    pretrained=True,
    output_dir="custom_runs/meu_treinamento"
)

# Iniciar treinamento
results = trainer.train(data_yaml=data_yaml)

# Imprimir resumo do treinamento
print(f"Treinamento concluído. Melhor mAP: {results.best_map}")
```

### Seleção de Hardware

O MicroDetect seleciona automaticamente o melhor hardware disponível para treinamento:

1. GPU NVIDIA (CUDA) se disponível
2. GPU Apple Silicon (MPS) se disponível
3. CPU como fallback

Você pode especificar manualmente o dispositivo:

```bash
microdetect train --dataset_dir dataset --model_size s --device cuda:0  # Dispositivo CUDA específico
microdetect train --dataset_dir dataset --model_size s --device cpu     # Forçar CPU
microdetect train --dataset_dir dataset --model_size s --device mps     # Forçar Apple MPS
```

## Estratégias de Treinamento

### Transfer Learning

Por padrão, o MicroDetect usa pesos pré-treinados no dataset COCO. Você pode começar do zero desabilitando isso:

```bash
microdetect train --dataset_dir dataset --model_size s --pretrained False
```

No entanto, começar com pesos pré-treinados geralmente dá melhores resultados, mesmo para tarefas especializadas como detecção de microorganismos.

### Programações de Taxa de Aprendizado

O MicroDetect usa o agendador de taxa de aprendizado integrado do YOLOv8. Você pode personalizá-lo:

```bash
microdetect train --dataset_dir dataset --lr0 0.01 --lrf 0.01 --momentum 0.937 --weight_decay 0.0005
```

Onde:
- `lr0`: Taxa de aprendizado inicial
- `lrf`: Fator de taxa de aprendizado final (final_lr = lr0 * lrf)
- `momentum`: Momentum SGD
- `weight_decay`: Fator de decay de peso

### Parada Antecipada

O MicroDetect implementa parada antecipada para evitar overfitting:

```bash
microdetect train --dataset_dir dataset --patience 15
```

Isso interrompe o treinamento se não for observada melhoria por 15 épocas consecutivas.

## Monitoramento de Treinamento

### Métricas de Treinamento

Durante o treinamento, o MicroDetect registra várias métricas:

- mAP50: Precisão Média Média no limite IoU 0,5
- mAP50-95: Precisão Média Média em vários limites IoU
- Precisão, Recall e pontuação F1
- Componentes de perda (box, class, dfl)

Você pode visualizar essas métricas em tempo real:

```bash
microdetect train --dataset_dir dataset --model_size s --plot True
```

### Integração com TensorBoard

Para visualização detalhada do treinamento, você pode usar o TensorBoard:

```bash
# Iniciar treinamento com registro TensorBoard
microdetect train --dataset_dir dataset --model_size s --use_tensorboard

# Iniciar TensorBoard
tensorboard --logdir runs/train
```

## Otimização de Hiperparâmetros

O MicroDetect fornece ferramentas para otimização de hiperparâmetros:

```bash
microdetect optimize_hyperparams --dataset_dir dataset --model_size s --trials 10
```

Isso realizará múltiplas execuções de treinamento com diferentes hiperparâmetros para encontrar a configuração ideal.

### Usando a API Python para Controle Detalhado

```python
from microdetect.training.train import YOLOTrainer

trainer = YOLOTrainer(model_size="s")
best_params = trainer.find_best_hyperparameters("dataset/data.yaml")

print(f"Melhores hiperparâmetros encontrados: {best_params}")
```

Isso testa diferentes combinações de tamanhos de batch e taxas de aprendizado para encontrar a configuração ideal.

## Exportação de Modelo

Após o treinamento, o MicroDetect exporta automaticamente o modelo para o formato ONNX para implantação:

```bash
# O modelo já é exportado durante o treinamento, mas você pode exportá-lo manualmente
microdetect export --model_path runs/train/yolov8_s_custom/weights/best.pt --format onnx
```

Outros formatos de exportação suportados:
- `torchscript`: Para implantação PyTorch
- `tflite`: Para TensorFlow Lite (móvel)
- `coreml`: Para Apple Core ML (iOS/macOS)

## Dicas para Treinamento Bem-sucedido

### Recomendações Específicas para Microorganismos

#### Para Detecção de Leveduras
```bash
microdetect train --dataset_dir dataset_leveduras --model_size s --image_size 800 --epochs 150
```
Leveduras geralmente requerem maior resolução devido ao seu tamanho pequeno e forma redonda.

#### Para Fungos com Hifas
```bash
microdetect train --dataset_dir dataset_fungos --model_size m --image_size 640 --epochs 200
```
Estruturas complexas como hifas se beneficiam de modelos mais poderosos e treinamento mais longo.

#### Para Micro-algas
```bash
microdetect train --dataset_dir dataset_algas --model_size s --image_size 640 --epochs 100 --batch_size 8
```
Micro-algas frequentemente têm formas distintivas e podem exigir menos tempo de treinamento.

### Desafios Comuns

#### Objetos Pequenos
Para microorganismos muito pequenos:
```bash
microdetect train --dataset_dir dataset --model_size m --image_size 1280
```
Entradas de maior resolução ajudam a detectar objetos menores.

#### Desequilíbrio de Classes
Se seu dataset tem classes desequilibradas:
```bash
microdetect train --dataset_dir dataset --model_size s --class_weights 1.0,2.0,1.5
```
Os pesos correspondem a cada classe, dando maior importância às classes sub-representadas.

#### Overfitting
Se você observar overfitting (boas métricas de treinamento, mas validação ruim):
```bash
microdetect train --dataset_dir dataset --model_size s --augment strong --dropout 0.2
```
Aumente a augmentação de dados e adicione regularização por dropout.

## Solução de Problemas

### Problemas Comuns

| Problema | Solução |
|----------|---------|
| Erros de memória insuficiente | Reduza o tamanho do batch ou da imagem |
| Perda de treinamento não diminui | Tente uma taxa de aprendizado diferente (--lr0 0.001) |
| Baixo desempenho de validação | Verifique a qualidade dos dados, aumente a augmentação |
| Treinamento muito lento | Tente um tamanho de modelo menor ou reduza a resolução da imagem |
| Valores de perda NaN | Reduza a taxa de aprendizado e verifique valores extremos de pixel |

## Próximos Passos

Após treinar seu modelo:

- [Guia de Gerenciamento de Checkpoints](checkpoint_management.md) - Aprenda como gerenciar e retomar treinamento a partir de checkpoints
- [Guia de Otimização de Hiperparâmetros](hyperparameter_optimization.md) - Ajuste fino do desempenho do seu modelo
- [Guia de Avaliação de Modelos](model_evaluation_analysis.md) - Avalie seu modelo treinado