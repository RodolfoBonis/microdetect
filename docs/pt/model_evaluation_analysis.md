# Guia de Avaliação de Modelos e Análise de Dados

Este guia explica como avaliar modelos treinados e analisar resultados de detecção no MicroDetect.

## Sumário
- [Introdução](#introdução)
- [Avaliação de Modelos](#avaliação-de-modelos)
  - [Avaliação Básica](#avaliação-básica)
  - [Métricas de Avaliação](#métricas-de-avaliação)
  - [Matriz de Confusão](#matriz-de-confusão)
  - [Ajuste de Limiar](#ajuste-de-limiar)
  - [Validação Cruzada](#validação-cruzada)
- [Análise de Desempenho](#análise-de-desempenho)
  - [Velocidade de Detecção](#velocidade-de-detecção)
  - [Uso de Recursos](#uso-de-recursos)
  - [Comparação de Tamanhos de Modelo](#comparação-de-tamanhos-de-modelo)
- [Visualização de Resultados](#visualização-de-resultados)
  - [Gerando Sobreposições de Detecção](#gerando-sobreposições-de-detecção)
  - [Visualização Interativa](#visualização-interativa)
  - [Processamento em Lote](#processamento-em-lote)
  - [Exportando Resultados](#exportando-resultados)
- [Análise de Erros](#análise-de-erros)
  - [Falsos Positivos](#falsos-positivos)
  - [Falsos Negativos](#falsos-negativos)
  - [Erros de Classificação](#erros-de-classificação)
  - [Erros de Localização](#erros-de-localização)
- [Análise Estatística](#análise-estatística)
  - [Mapas de Densidade](#mapas-de-densidade)
  - [Distribuição de Tamanho](#distribuição-de-tamanho)
  - [Análise Espacial](#análise-espacial)
  - [Análise Temporal](#análise-temporal)
- [Relatórios](#relatórios)
  - [Gerando Relatórios PDF](#gerando-relatórios-pdf)
  - [Exportando para CSV](#exportando-para-csv)
  - [Dashboards Interativos](#dashboards-interativos)
- [Melhores Práticas](#melhores-práticas)
  - [Seleção de Modelo](#seleção-de-modelo)
  - [Considerações sobre o Dataset](#considerações-sobre-o-dataset)
  - [Melhoria Iterativa](#melhoria-iterativa)
- [Solução de Problemas](#solução-de-problemas)

## Introdução

A avaliação de modelos é uma etapa crítica no fluxo de trabalho de detecção de microorganismos. Ela ajuda a:

- Avaliar a precisão e confiabilidade do modelo
- Identificar áreas para melhoria
- Comparar diferentes configurações de modelo
- Determinar as configurações ideais para implantação

O MicroDetect fornece ferramentas abrangentes para avaliação de modelos e análise de resultados de detecção.

## Avaliação de Modelos

### Avaliação Básica

Para avaliar um modelo treinado em um dataset de teste:

```bash
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --data_yaml dataset/data.yaml
```

Este comando gera um relatório de avaliação abrangente incluindo:
- Precisão, recall e F1-score para cada classe
- Métricas mAP50 e mAP50-95
- Velocidade de inferência
- Matriz de confusão (se habilitada)

### Métricas de Avaliação

O MicroDetect calcula várias métricas-chave:

- **Precisão**: A proporção de detecções verdadeiro-positivas entre todas as detecções
- **Recall**: A proporção de detecções verdadeiro-positivas entre todos os objetos reais
- **F1-score**: A média harmônica de precisão e recall
- **mAP50**: Precisão Média (AP) com limiar IoU de 0.5
- **mAP50-95**: Precisão Média (AP) calculada como média de limiares IoU de 0.5 a 0.95

Exemplo de saída:

```
Classe        Imagens   Rótulos  Precisão   Recall   mAP50  mAP50-95
Todas         50        230      0.962      0.921    0.947   0.736
Classe 0      50        98       0.981      0.934    0.972   0.762
Classe 1      50        87       0.953      0.932    0.943   0.726
Classe 2      50        45       0.951      0.897    0.925   0.721
```

### Matriz de Confusão

Para gerar uma matriz de confusão para análise detalhada de erros:

```bash
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --confusion_matrix
```

A visualização da matriz de confusão mostra:
- Verdadeiros positivos (elementos da diagonal)
- Falsos positivos (elementos fora da diagonal nas colunas)
- Falsos negativos (elementos fora da diagonal nas linhas)
- Detecções de fundo ou objetos perdidos

### Ajuste de Limiar

Você pode ajustar os limiares de confiança e IoU para otimizar o desempenho:

```bash
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --conf_threshold 0.4 --iou_threshold 0.6
```

Para encontrar os limiares ideais:

```python
# Script Python para varrer valores de limiar
import numpy as np
from microdetect.training.evaluate import ModelEvaluator

evaluator = ModelEvaluator()
model_path = "runs/train/exp/weights/best.pt"
data_yaml = "dataset/data.yaml"

# Varrer limiares de confiança
conf_thresholds = np.arange(0.1, 0.9, 0.1)
results = []

for conf in conf_thresholds:
    metrics = evaluator.evaluate_model(model_path, data_yaml, conf_threshold=conf)
    results.append({
        'conf_threshold': conf,
        'mAP50': metrics['metricas_gerais']['Precisão (mAP50)'],
        'recall': metrics['metricas_gerais']['Recall']
    })
    
# Imprimir tabela de resultados
for result in results:
    print(f"Conf: {result['conf_threshold']:.1f}, mAP50: {result['mAP50']:.4f}, Recall: {result['recall']:.4f}")
```

### Validação Cruzada

Para uma avaliação mais robusta, especialmente com dados limitados, use validação cruzada:

```python
from microdetect.training.cross_validate import CrossValidator

validator = CrossValidator(
    base_dataset_dir="dataset",
    output_dir="cross_val_results",
    model_size="m",
    epochs=100,
    folds=5
)

results = validator.run()
validator.generate_report()
```

Isso realiza validação cruzada k-fold, treinando e avaliando o modelo em diferentes divisões de dados.

## Análise de Desempenho

### Velocidade de Detecção

Para avaliar a velocidade de detecção:

```bash
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --benchmark_speed
```

Isso mede:
- Tempo de inferência por imagem (ms)
- Quadros por segundo (FPS)
- Tempos de pré-processamento e pós-processamento

Para velocidade de inferência em lote:

```python
from microdetect.training.evaluate import SpeedBenchmark

benchmark = SpeedBenchmark(model_path="runs/train/exp/weights/best.pt")
results = benchmark.run(
    batch_sizes=[1, 2, 4, 8, 16],
    image_sizes=[640, 960, 1280],
    iterations=100
)
benchmark.plot_results("speed_benchmark.png")
```

### Uso de Recursos

Para monitorar a memória da GPU e uso de CPU durante a inferência:

```python
from microdetect.utils.resource_monitor import ResourceMonitor
from microdetect.training.evaluate import ModelEvaluator

monitor = ResourceMonitor()
monitor.start()

evaluator = ModelEvaluator()
evaluator.evaluate_model("runs/train/exp/weights/best.pt", "dataset/data.yaml")

stats = monitor.stop()
monitor.plot_usage("resource_usage.png")
```

### Comparação de Tamanhos de Modelo

Para comparar modelos de diferentes tamanhos:

```bash
microdetect evaluate --model_path runs/train/exp1/weights/best.pt,runs/train/exp2/weights/best.pt --dataset_dir dataset --output_dir comparison
```

Isso gera um relatório de comparação incluindo:
- Tamanho do modelo (parâmetros, tamanho do arquivo)
- Métricas de precisão
- Velocidade de inferência
- Visualização de trade-off (precisão vs. velocidade)

## Visualização de Resultados

### Gerando Sobreposições de Detecção

Para visualizar detecções em imagens:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens --output_dir caminho/para/saida
```

Isso cria imagens com caixas delimitadoras, rótulos de classe e pontuações de confiança.

### Visualização Interativa

Para visualização interativa de resultados:

```bash
microdetect visualize_results --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens
```

Isso abre uma interface onde você pode:
- Visualizar detecções
- Ajustar limiares de confiança em tempo real
- Filtrar classes
- Comparar com a verdade fundamental (se disponível)

### Processamento em Lote

Para datasets grandes, use processamento em lote:

```bash
microdetect batch_detect --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens --output_dir caminho/para/saida --batch_size 16
```

### Exportando Resultados

Para exportar resultados de detecção para análise adicional:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens --save_txt --save_json
```

Isso salva:
- Arquivos de texto com anotações no formato YOLO
- Arquivo JSON com informações detalhadas de detecção
- Arquivo CSV resumindo todas as detecções

## Análise de Erros

### Falsos Positivos

Para analisar detecções de falsos positivos:

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --focus false_positives --output_dir error_analysis
```

Isso gera:
- Imagens mostrando detecções de falsos positivos
- Análise de padrões comuns de erro
- Sugestões para melhoria

### Falsos Negativos

Para analisar detecções de falsos negativos (objetos não detectados):

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --focus false_negatives --output_dir error_analysis
```

### Erros de Classificação

Para analisar erros de classificação (detecção correta mas classe errada):

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --focus classification_errors --output_dir error_analysis
```

### Erros de Localização

Para analisar erros de localização (IoU abaixo do limiar):

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --focus localization_errors --output_dir error_analysis
```

## Análise Estatística

### Mapas de Densidade

Para gerar mapas de densidade mostrando a distribuição de microorganismos:

```bash
microdetect analyze_distribution --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens --output_dir density_maps
```

Isso cria mapas de calor mostrando a distribuição espacial dos microorganismos detectados.

### Distribuição de Tamanho

Para analisar a distribuição de tamanho dos microorganismos detectados:

```bash
microdetect analyze_size --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens --output_dir size_analysis
```

Isso gera histogramas e estatísticas sobre tamanhos de microorganismos por classe.

### Análise Espacial

Para análise de relacionamento espacial:

```bash
microdetect analyze_spatial --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens --output_dir spatial_analysis
```

Isso analisa:
- Distâncias entre vizinhos mais próximos
- Padrões de agrupamento
- Correlações espaciais entre diferentes classes

### Análise Temporal

Se você tem imagens de séries temporais, analise mudanças ao longo do tempo:

```bash
microdetect analyze_temporal --model_path runs/train/exp/weights/best.pt --source caminho/para/series_temporais --output_dir temporal_analysis
```

Isso gera:
- Gráficos de séries temporais de contagens de microorganismos
- Análise de taxas de crescimento/declínio
- Visualização de mudanças ao longo do tempo

## Relatórios

### Gerando Relatórios PDF

Para gerar um relatório PDF abrangente:

```bash
microdetect generate_report --results_dir runs/detect/exp --output_file relatorio.pdf
```

Isso cria um PDF incluindo:
- Resumo do modelo
- Métricas de avaliação
- Imagens de amostra de detecção
- Análise de erros
- Insights estatísticos

### Exportando para CSV

Para exportar dados para análise em outras ferramentas:

```bash
microdetect export_results --results_dir runs/detect/exp --format csv --output_file resultados.csv
```

### Dashboards Interativos

Para exploração de dados interativa:

```bash
microdetect dashboard --results_dir runs/detect/exp --port 8050
```

Isso inicia um dashboard web com:
- Visualizações interativas
- Capacidades de filtragem
- Opções de exportação
- Ferramentas de comparação

## Melhores Práticas

### Seleção de Modelo

Diretrizes para selecionar o modelo apropriado:

- **YOLOv8-n**: Inferência rápida, menor precisão, adequado para ambientes com recursos limitados
- **YOLOv8-s**: Equilíbrio entre velocidade e precisão para muitas aplicações
- **YOLOv8-m**: Maior precisão com velocidade moderada, bom para detecção geral
- **YOLOv8-l**: Alta precisão, velocidade mais lenta, para aplicações que exigem precisão
- **YOLOv8-x**: Maior precisão, velocidade mais lenta, para pesquisa ou quando velocidade não é crítica

### Considerações sobre o Dataset

Para avaliação ideal:

- Use um dataset de teste representativo
- Garanta distribuição adequada de classes
- Inclua casos desafiadores
- Mantenha independência de dados (sem sobreposição com dados de treinamento)
- Considere condições do mundo real

### Melhoria Iterativa

Processo para melhoria contínua do modelo:

1. Avalie o modelo atual
2. Analise erros e limitações
3. Colete dados adicionais direcionados para fraquezas
4. Refine diretrizes de anotação se necessário
5. Retreine com dados melhorados
6. Reavalie e compare com versões anteriores

## Solução de Problemas

**Problema**: Baixa precisão apesar de alta acurácia de treinamento
**Solução**: Verifique vazamento de dados entre conjuntos de treino e teste; analise falsos positivos

**Problema**: Baixo recall apesar de boas métricas de validação
**Solução**: Verifique desequilíbrio de classes; revise consistência de anotação; analise falsos negativos

**Problema**: Avaliação muito lenta
**Solução**: Reduza o tamanho do batch; use tamanho de imagem menor; verifique utilização de hardware

**Problema**: Falta de memória durante avaliação
**Solução**: Reduza tamanho do batch; use device="cpu" para modelos grandes em hardware limitado

**Problema**: Métricas inconsistentes entre execuções
**Solução**: Defina uma semente aleatória fixa; aumente o tamanho do dataset de teste; verifique casos extremos

Para solução de problemas mais detalhada, consulte o [Guia de Solução de Problemas](troubleshooting.md).