# Guia de Validação Cruzada e Benchmarking

Este guia explica como usar as ferramentas de validação cruzada e benchmarking do MicroDetect para avaliar minuciosamente o desempenho do modelo e analisar o uso de recursos.

## Sumário
- [Introdução](#introdução)
- [Validação Cruzada](#validação-cruzada)
  - [Uso Básico](#uso-básico)
  - [Compreendendo os Resultados](#compreendendo-os-resultados)
  - [Personalizando a Validação Cruzada](#personalizando-a-validação-cruzada)
- [Benchmarking de Desempenho](#benchmarking-de-desempenho)
  - [Benchmarking de Velocidade](#benchmarking-de-velocidade)
  - [Monitoramento de Recursos](#monitoramento-de-recursos)
  - [Visualizando Resultados de Benchmark](#visualizando-resultados-de-benchmark)
- [Comparação de Modelos](#comparação-de-modelos)
  - [Comparação Básica](#comparação-básica)
  - [Comparação Avançada](#comparação-avançada)
- [Melhores Práticas](#melhores-práticas)
- [Solução de Problemas](#solução-de-problemas)

## Introdução

A avaliação robusta de modelos é essencial para desenvolver sistemas confiáveis de detecção de microorganismos. O MicroDetect fornece duas poderosas ferramentas de avaliação:

- **Validação Cruzada**: Avalia a estabilidade e confiabilidade do modelo em diferentes subconjuntos de dados
- **Benchmarking**: Mede a velocidade do modelo, throughput e uso de recursos

Essas ferramentas ajudam você a:
- Identificar overfitting e viés de dados
- Entender o desempenho do seu modelo em diferentes distribuições de dados
- Otimizar para implantação medindo velocidade e requisitos de recursos
- Tomar decisões informadas sobre tamanho e configuração do modelo

## Validação Cruzada

A validação cruzada é uma técnica para avaliar o desempenho do modelo treinando e testando em diferentes subconjuntos de dados. O MicroDetect implementa a validação cruzada k-fold, onde o dataset é dividido em k partes iguais (folds), e o modelo é treinado k vezes, cada vez usando um fold diferente como conjunto de teste.

### Uso Básico

Para executar a validação cruzada com 5 folds:

```python
from microdetect.training import CrossValidator

validator = CrossValidator(
    base_dataset_dir="dataset",
    output_dir="cv_results",
    model_size="m",
    epochs=100,
    folds=5,
    seed=42
)

# Executar a validação cruzada
results = validator.run()

# Gerar um relatório
report_path = validator.generate_report()
```

Isso cria a seguinte estrutura:
```
cv_results/
├── fold_1/
│   ├── train/
│   ├── val/
│   ├── runs/
│   ├── evaluation/
│   └── data.yaml
├── fold_2/
│   ├── ...
...
├── cross_validation_plot.png
└── cross_validation_report.json
```

### Compreendendo os Resultados

O relatório de validação cruzada (`cross_validation_report.json`) contém:

```json
{
  "cross_validation": {
    "folds": 5,
    "model_size": "m",
    "epochs": 100,
    "seed": 42
  },
  "average_metrics": {
    "map50": 0.845,
    "map50_95": 0.623,
    "recall": 0.812,
    "precision": 0.867,
    "f1_score": 0.838
  },
  "std_metrics": {
    "map50": 0.035
  },
  "fold_results": [
    {
      "fold": 1,
      "train_files": 342,
      "val_files": 86,
      "model_path": "cv_results/fold_1/runs/train/weights/best.pt",
      "metrics": {
        "metricas_gerais": {
          "Precisão (mAP50)": 0.856,
          "Precisão (mAP50-95)": 0.634,
          "Recall": 0.823,
          "Precisão": 0.878,
          "F1-Score": 0.849
        },
        "metricas_por_classe": [
          ...
        ]
      }
    },
    ...
  ]
}
```

O `cross_validation_plot.png` mostra métricas para cada fold, ajudando você a identificar:
- Consistência de desempenho entre folds
- Potencial viés de dados (se um fold apresentar desempenho significativamente diferente)
- Desempenho médio com desvio padrão

### Personalizando a Validação Cruzada

Você pode personalizar a validação cruzada com:

```python
validator = CrossValidator(
    base_dataset_dir="dataset",
    output_dir="cv_results",
    model_size="s",        # Use um modelo menor (n, s, m, l, x)
    epochs=50,             # Menos épocas para treinamento mais rápido
    folds=10,              # Mais folds para avaliação mais detalhada
    seed=123               # Semente diferente para reprodutibilidade
)
```

## Benchmarking de Desempenho

O MicroDetect oferece dois tipos de benchmarking:
1. **Benchmarking de Velocidade**: Avalia a velocidade de inferência com diferentes tamanhos de batch e tamanhos de imagem
2. **Monitoramento de Recursos**: Mede o uso de CPU, memória e GPU durante a execução do modelo

### Benchmarking de Velocidade

Para fazer benchmark da velocidade do modelo:

```python
from microdetect.training import SpeedBenchmark

benchmark = SpeedBenchmark(model_path="runs/train/exp/weights/best.pt")

# Executar benchmark com diferentes configurações
results = benchmark.run(
    batch_sizes=[1, 2, 4, 8, 16],        # Testar diferentes tamanhos de batch
    image_sizes=[640, 960, 1280],        # Testar diferentes tamanhos de imagem
    iterations=50,                        # Número de iterações de inferência
    warmup=10                             # Número de iterações de aquecimento
)

# Gerar visualização
plot_path = benchmark.plot_results("benchmark_results.png")

# Salvar resultados detalhados
benchmark.save_results("benchmark_results.csv")
```

Os resultados mostram:
- Tempo médio de inferência por amostra
- Quadros por segundo (FPS)
- Amostras processadas por segundo
- Como o desempenho escala com o tamanho do batch e o tamanho da imagem

Exemplo de saída:
```
Batch Size: 1, Image Size: 640, Latency: 25.4ms, FPS: 39.4
Batch Size: 2, Image Size: 640, Latency: 43.2ms, FPS: 46.3
Batch Size: 4, Image Size: 640, Latency: 82.7ms, FPS: 48.4
...
```

### Monitoramento de Recursos

Para monitorar o uso de recursos durante a execução do modelo:

```python
from microdetect.training import ResourceMonitor, YOLOTrainer

# Iniciar monitoramento
monitor = ResourceMonitor()
monitor.start()

# Executar seu modelo (exemplo: treinamento)
trainer = YOLOTrainer(model_size="m", epochs=100)
trainer.train("dataset/data.yaml")

# Parar monitoramento e obter estatísticas
stats = monitor.stop()
print(f"Uso de CPU (média): {stats['cpu_percent_avg']}%")
print(f"Uso de memória (máx): {stats['memory_percent_max']}%")

# Gerar gráfico de uso
monitor.plot_usage("resource_usage.png")
```

Isso gera um gráfico de série temporal mostrando:
- Uso de CPU ao longo do tempo
- Uso de memória ao longo do tempo
- Uso de GPU (se disponível)

O monitoramento de recursos ajuda você a:
- Identificar gargalos de desempenho
- Planejar requisitos de hardware para implantação
- Comparar a eficiência de diferentes tamanhos de modelo

### Visualizando Resultados de Benchmark

A visualização de benchmark de velocidade inclui:
- **FPS vs. Tamanho do Batch**: Mostra como o throughput escala com o tamanho do batch
- **Throughput vs. Tamanho da Imagem**: Mostra o impacto de desempenho da resolução da imagem
- **Distribuição de Latência**: Mostra a consistência dos tempos de inferência

A visualização de monitoramento de recursos inclui:
- **Uso de CPU**: Série temporal de utilização da CPU
- **Uso de Memória**: Série temporal de consumo de RAM
- **Uso de GPU**: Série temporal de utilização da GPU (se disponível)

## Melhores Práticas

1. **Use dados consistentes**: Certifique-se de que todos os folds na validação cruzada tenham distribuições de classe similares

2. **Execute múltiplos benchmarks**: Para medições de velocidade confiáveis, execute benchmarks várias vezes e calcule a média dos resultados

3. **Priorize métricas relevantes**: Concentre-se em métricas que importam para sua aplicação (ex: precisão vs. velocidade)

4. **Combine condições de benchmark com implantação**: Teste com tamanhos de batch e tamanhos de imagem que você usará em produção

5. **Considere restrições de recursos**: Se estiver implantando em dispositivos com recursos limitados, priorize modelos com menor uso de recursos

6. **Defina seeds apropriadas**: Use valores de seed para resultados reproduzíveis de validação cruzada

7. **Compare modelos de forma abrangente**: Não olhe apenas para a precisão; considere velocidade, tamanho e uso de recursos

## Solução de Problemas

### Problema: Validação cruzada leva muito tempo
**Solução**: Reduza o número de épocas ou use um modelo de tamanho menor para validação inicial

### Problema: Memória insuficiente durante validação cruzada
**Solução**: Reduza o tamanho do batch ou da imagem; use um modelo de tamanho menor; processe um fold de cada vez

### Problema: Resultados de benchmark inconsistentes
**Solução**: Aumente o número de iterações; use um período de aquecimento; feche outros aplicativos durante o benchmarking

### Problema: Monitor de recursos mostra uso mínimo de GPU
**Solução**: Verifique se a GPU está configurada corretamente; garanta que o PyTorch esteja usando CUDA ou MPS

### Problema: Grande desvio padrão nos resultados de validação cruzada
**Solução**: Aumente o número de folds; verifique desequilíbrio de classes; verifique a qualidade dos dados em todas as amostras

Para mais ajuda na solução de problemas, consulte o [Guia de Solução de Problemas](troubleshooting.md).