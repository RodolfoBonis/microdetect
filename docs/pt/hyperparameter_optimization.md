# Guia de Otimização de Hiperparâmetros

Este guia explica como ajustar efetivamente os hiperparâmetros do seu modelo YOLOv8 usando as ferramentas de otimização do MicroDetect para alcançar o melhor desempenho na detecção.

## Visão Geral

Hiperparâmetros são variáveis de configuração que determinam como um modelo é treinado e como ele se comporta. O ajuste adequado de hiperparâmetros pode melhorar significativamente a precisão do modelo, velocidade de inferência e desempenho geral. O MicroDetect fornece ferramentas especializadas para otimizar modelos YOLOv8 para detecção de microorganismos.

## Entendendo os Hiperparâmetros Chave

### Hiperparâmetros Críticos

| Hiperparâmetro | Descrição | Impacto |
|----------------|-------------|--------|
| Taxa de Aprendizado (`lr0`) | Taxa de aprendizado inicial | Controla quão rapidamente o modelo se adapta ao problema |
| Tamanho do Batch (`batch_size`) | Número de amostras processadas antes de atualizar o modelo | Afeta a estabilidade e velocidade de treinamento |
| Tamanho da Imagem (`image_size`) | Resolução da imagem de entrada | Influencia a detecção de microorganismos pequenos |
| Weight Decay (`weight_decay`) | Parâmetro de regularização L2 | Controla a complexidade do modelo para evitar overfitting |
| Mosaic | Técnica de augmentação de dados | Aumenta a variabilidade durante o treinamento |
| Âncoras | Dimensões base das caixas de detecção | Âncoras otimizadas melhoram a precisão da detecção |

## Busca Básica de Hiperparâmetros

### Interface de Linha de Comando

A maneira mais simples de otimizar hiperparâmetros é através da linha de comando:

```bash
microdetect optimize_hyperparams --dataset_dir dataset --model_size s --trials 10
```

Este comando irá:
1. Executar 10 tentativas de treinamento com diferentes combinações de hiperparâmetros
2. Avaliar o desempenho de cada modelo
3. Reportar a melhor configuração encontrada

### Opções de Linha de Comando

| Parâmetro | Descrição | Padrão |
|-----------|-------------|---------|
| `--dataset_dir` | Diretório contendo o dataset | `dataset` |
| `--model_size` | Tamanho do modelo YOLOv8 (n, s, m, l, x) | `s` |
| `--trials` | Número de tentativas de otimização | `10` |
| `--epochs_per_trial` | Épocas por tentativa de otimização | `10` |
| `--metric` | Métrica a ser otimizada (map50, map50-95, recall, precision) | `map50-95` |
| `--output_dir` | Diretório para salvar resultados | `runs/hyp_tuning` |

## Otimização Avançada de Hiperparâmetros

### Usando a API Python

Para mais controle, você pode usar a classe `YOLOTrainer` diretamente em Python:

```python
from microdetect.training.train import YOLOTrainer

# Inicializar treinador
trainer = YOLOTrainer(model_size="s")

# Buscar melhores hiperparâmetros
best_params = trainer.find_best_hyperparameters(
    data_yaml="dataset/data.yaml"
)

print(f"Melhores hiperparâmetros encontrados: {best_params}")

# Treinar com os melhores hiperparâmetros
trainer = YOLOTrainer(
    model_size="s",
    batch_size=best_params["batch_size"],
    epochs=100,
    output_dir="runs/modelo_otimizado"
)

results = trainer.train(data_yaml="dataset/data.yaml")
```

### Espaço de Busca de Hiperparâmetros Personalizado

Para mais controle sobre o espaço de busca:

```python
import optuna
from microdetect.training.train import YOLOTrainer

def objective(trial):
    # Definir espaço de busca
    batch_size = trial.suggest_categorical("batch_size", [8, 16, 32, 64])
    lr0 = trial.suggest_float("lr0", 1e-5, 1e-2, log=True)
    weight_decay = trial.suggest_float("weight_decay", 1e-5, 1e-2, log=True)
    image_size = trial.suggest_categorical("image_size", [512, 640, 768])
    
    # Treinar com hiperparâmetros sugeridos
    trainer = YOLOTrainer(
        model_size="s",
        batch_size=batch_size,
        image_size=image_size,
        epochs=10,
        output_dir=f"runs/hyp_trial_{trial.number}"
    )
    
    # Usar argumentos de treinamento personalizados
    custom_args = {
        "lr0": lr0,
        "weight_decay": weight_decay,
        "patience": 5,
        "save": False  # Não salvar modelos intermediários
    }
    
    results = trainer.train(data_yaml="dataset/data.yaml", **custom_args)
    
    # Retornar métrica a ser otimizada (maior é melhor)
    return results.maps.mean()  # mAP médio

# Criar estudo e otimizar
study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=20)

print("Melhores hiperparâmetros:", study.best_params)
```

## Estratégias de Otimização Especializadas

### Otimizando para Microorganismos Pequenos

Microorganismos menores (como certas leveduras) requerem atenção especial:

```bash
microdetect optimize_hyperparams_small --dataset_dir dataset_microorganismos_pequenos --model_size m --min_image_size 800 --focus anchor_scale
```

Este comando se concentra em otimizar parâmetros cruciais para detecção de objetos pequenos:
- Imagens de maior resolução
- Escalas de caixas âncora (anchor boxes)
- Configurações de rede piramidal de características (feature pyramid network)

### Otimizando para Velocidade de Inferência

Quando a velocidade de implantação é crítica:

```bash
microdetect optimize_hyperparams_speed --dataset_dir dataset --target_device cpu --max_latency 50
```

Isso otimiza hiperparâmetros mantendo a latência de inferência abaixo de 50ms na CPU.

### Otimizando para Diferentes Tipos de Microorganismos

#### Para Detecção de Leveduras
```bash
microdetect optimize_hyperparams --dataset_dir dataset_leveduras --model_size s --focus "anchor_scale,image_size"
```

#### Para Fungos com Hifas
```bash
microdetect optimize_hyperparams --dataset_dir dataset_fungos --model_size m --focus "mosaic,mixup,copy_paste"
```
Estruturas de hifas se beneficiam de otimizações de augmentação.

#### Para Micro-algas
```bash
microdetect optimize_hyperparams --dataset_dir dataset_algas --model_size s --focus "image_size,focal_loss"
```
Micro-algas frequentemente têm formas distintivas, mas tamanhos variados.

## Otimização Multi-objetivo

Equilibre múltiplos objetivos (precisão, velocidade, tamanho do modelo):

```bash
microdetect optimize_multi_objective --dataset_dir dataset --model_size s --objectives "map50-95,latency,param_count" --weights "0.6,0.3,0.1"
```

Isso otimiza para uma combinação ponderada de precisão do modelo, velocidade de inferência e tamanho do modelo.

## Melhores Práticas

### Validação Cruzada Durante Otimização

Para seleção de hiperparâmetros mais robusta:

```bash
microdetect optimize_hyperparams --dataset_dir dataset --model_size s --cross_validation_folds 3
```

Isso avalia cada conjunto de hiperparâmetros usando validação cruzada 3-fold para resultados mais confiáveis.

### Estratégia de Otimização Progressiva

Para otimização eficiente:

1. Comece com uma busca ampla:
```bash
microdetect optimize_hyperparams --dataset_dir dataset --model_size s --trials 10 --epochs_per_trial 5 --search_strategy coarse
```

2. Refine com uma busca focada:
```bash
microdetect optimize_hyperparams --dataset_dir dataset --model_size s --trials 10 --epochs_per_trial 10 --search_strategy fine --base_params melhores_params.yaml
```

### Congelamento de Parâmetros

Ao otimizar um aspecto específico:

```bash
microdetect optimize_hyperparams --dataset_dir dataset --model_size s --focus "learning_rate,batch_size" --freeze "image_size=640,weight_decay=0.0005"
```

Isso congela certos parâmetros enquanto otimiza outros.

## Visualizando Resultados da Otimização

Gere visualizações da busca de hiperparâmetros:

```bash
microdetect analyze_hyp_results --results_dir runs/hyp_tuning --visualize
```

Isso cria:
- Gráficos de importância de parâmetros
- Gráfico de coordenadas paralelas
- Gráficos de contorno de interações chave entre parâmetros
- Histórico de otimização

## Exportando e Compartilhando Hiperparâmetros

Salve hiperparâmetros otimizados para uso futuro:

```bash
microdetect export_hyperparams --model_path runs/hyp_tuning/best/weights/best.pt --output hyp_microalgas.yaml
```

Use os hiperparâmetros exportados para treinamento:

```bash
microdetect train --dataset_dir dataset --model_size s --hyperparameters hyp_microalgas.yaml
```

## Solução de Problemas

### Problemas Comuns

| Problema | Solução |
|----------|---------|
| Otimização demorando muito | Reduza `epochs_per_trial` ou use um tamanho de modelo menor |
| Resultados instáveis entre tentativas | Aumente `epochs_per_trial` ou adicione validação cruzada |
| Erros de memória insuficiente | Reduza o intervalo de tamanho de batch ou tamanho de imagem |
| Otimização não melhorando o desempenho | Verifique a qualidade do dataset ou expanda o espaço de busca de hiperparâmetros |

## Próximos Passos

Após otimizar seus hiperparâmetros:

- [Guia de Treinamento](training_guide.md) - Treine seu modelo com os hiperparâmetros otimizados
- [Guia de Avaliação de Modelos](model_evaluation_analysis.md) - Avalie seu modelo otimizado
- [Guia de Comparação de Modelos](model_comparison.md) - Compare o desempenho com modelos baseline