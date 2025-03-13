# Guia de Comparação de Modelos

Este guia explica como usar as ferramentas de comparação de modelos do MicroDetect para avaliar e selecionar o melhor modelo para suas tarefas de detecção de microorganismos.

## Sumário
- [Introdução](#introdução)
- [Comparando Modelos](#comparando-modelos)
  - [Comparação Básica](#comparação-básica)
  - [Comparação Avançada](#comparação-avançada)
  - [Dashboard de Comparação Interativo](#dashboard-de-comparação-interativo)
- [Métricas de Comparação](#métricas-de-comparação)
  - [Métricas de Precisão](#métricas-de-precisão)
  - [Métricas de Desempenho](#métricas-de-desempenho)
  - [Métricas de Tamanho e Recursos](#métricas-de-tamanho-e-recursos)
- [Visualizando Resultados de Comparação](#visualizando-resultados-de-comparação)
  - [Gráficos de Comparação](#gráficos-de-comparação)
  - [Visualização de Trade-off](#visualização-de-trade-off)
  - [Comparação de Detecção](#comparação-de-detecção)
- [Framework de Tomada de Decisão](#framework-de-tomada-de-decisão)
- [Melhores Práticas](#melhores-práticas)
- [Solução de Problemas](#solução-de-problemas)

## Introdução

A comparação de modelos é essencial para selecionar o modelo ideal para suas necessidades de detecção de microorganismos. Diferentes modelos oferecem diferentes compromissos entre:

- Precisão de detecção
- Velocidade de inferência
- Requisitos de recursos
- Tamanho do modelo

O MicroDetect fornece ferramentas abrangentes para comparar múltiplos modelos nessas dimensões, ajudando você a tomar decisões informadas com base em seus requisitos específicos.

## Comparando Modelos

### Comparação Básica

Para comparar diferentes modelos ou configurações de modelo:

```bash
microdetect compare_models --model_paths model1.pt,model2.pt,model3.pt --data_yaml dataset/data.yaml
```

Este comando avalia os modelos especificados no conjunto de dados de teste definido no `data.yaml` e gera um relatório de comparação incluindo:

- Métricas de desempenho (mAP50, mAP50-95, precisão, recall) para cada modelo
- Medições de velocidade de inferência
- Comparação de tamanho de modelo
- Comparação de métricas por classe

Exemplo de saída:
```
+-------------+-------+--------+----------+--------+-------------+----------+
| Modelo      | mAP50 | mAP50- | Precisão | Recall | Tempo Infer.| Tamanho  |
|             |       | 95     |          |        | (ms/img)    | (MB)     |
+-------------+-------+--------+----------+--------+-------------+----------+
| yolov8n_m1  | 0.823 | 0.615  | 0.856    | 0.827  | 4.5         | 6.2      |
| yolov8s_m2  | 0.867 | 0.654  | 0.895    | 0.843  | 8.7         | 22.8     |
| yolov8m_m3  | 0.892 | 0.703  | 0.912    | 0.867  | 19.2        | 52.1     |
+-------------+-------+--------+----------+--------+-------------+----------+
```

### Comparação Avançada

Para comparação mais detalhada com métricas adicionais e personalização:

```python
from microdetect.training import ModelComparator

comparator = ModelComparator(output_dir="resultados_comparacao")

# Comparar múltiplos modelos com configurações personalizadas
results = comparator.compare_models(
    model_paths=[
        "runs/train/yolov8n_custom/weights/best.pt",
        "runs/train/yolov8s_custom/weights/best.pt",
        "runs/train/yolov8m_custom/weights/best.pt"
    ],
    data_yaml="dataset/data.yaml",
    conf_threshold=0.25,
    iou_threshold=0.7,
    batch_size=16,
    device="0",  # Usar GPU específica
    include_precision_recall_curve=True,
    include_class_metrics=True,
    save_json=True
)

# Gerar relatório de comparação abrangente
comparator.generate_comparison_report(
    results=results,
    output_file="relatorio_comparacao_modelos.pdf",
    include_images=True,
    include_charts=True
)
```

Isso gera uma comparação abrangente com:
- Métricas detalhadas por classe
- Curvas de precisão-recall
- Curvas de pontuação F1 vs. limiar de confiança
- Gráficos de trade-off de tamanho e desempenho
- Imagens de exemplo de detecção de cada modelo

### Dashboard de Comparação Interativo

Para exploração interativa de comparações de modelos:

```bash
microdetect compare_models --model_paths model1.pt,model2.pt,model3.pt --data_yaml dataset/data.yaml --dashboard
```

Isso inicia um dashboard interativo permitindo que você:
- Visualize métricas lado a lado
- Filtre comparação por classe
- Ajuste limiares de confiança e IoU em tempo real
- Compare resultados de detecção em imagens de exemplo
- Crie gráficos de comparação personalizados
- Exporte resultados em vários formatos

## Métricas de Comparação

### Métricas de Precisão

O MicroDetect compara modelos usando as seguintes métricas de precisão:

1. **mAP50**: Precisão Média significativa em limiar de IoU de 0.5
2. **mAP50-95**: Precisão Média significativa com média entre limiares de IoU de 0.5 a 0.95
3. **Precisão**: Proporção de verdadeiros positivos para todas as detecções
4. **Recall**: Proporção de verdadeiros positivos para todos os objetos de verdade fundamental
5. **Pontuação F1**: Média harmônica de precisão e recall

Para comparações específicas por classe, essas métricas são calculadas para cada classe, permitindo identificar qual modelo tem melhor desempenho para tipos específicos de microorganismos.

### Métricas de Desempenho

Para comparar desempenho e eficiência do modelo:

1. **Tempo de Inferência**: Tempo médio para processar uma imagem (ms/imagem)
2. **Quadros Por Segundo (FPS)**: Número de imagens que podem ser processadas por segundo
3. **Latência**: Tempo da entrada à saída
4. **Throughput**: Número de objetos processados por segundo em tamanho de lote

Essas métricas são medidas em diferentes:
- Tamanhos de lote (1, 2, 4, 8, 16)
- Tamanhos de imagem (640, 960, 1280)
- Configurações de hardware (CPU, GPU, diferentes dispositivos)

### Métricas de Tamanho e Recursos

Para avaliar requisitos de implantação do modelo:

1. **Tamanho do Modelo**: Tamanho do arquivo do modelo em megabytes
2. **Contagem de Parâmetros**: Número de parâmetros no modelo
3. **Uso de Memória**: Consumo máximo de RAM durante inferência
4. **Memória GPU**: VRAM necessária para inferência
5. **Uso de CPU**: Utilização de CPU durante inferência

## Visualizando Resultados de Comparação

### Gráficos de Comparação

O MicroDetect gera vários gráficos para auxiliar na comparação de modelos:

1. **Gráficos de Radar**: Comparação multidimensional de modelos em métricas-chave
2. **Gráficos de Barras**: Comparação lado a lado de métricas individuais
3. **Gráficos de Linha**: Métricas em diferentes limiares de confiança ou tamanhos de lote
4. **Gráficos de Dispersão**: Visualização de trade-off (precisão vs. velocidade)

Exemplos de visualizações:
- Curvas de Precisão-Recall para cada modelo
- Gráfico de mAP vs. tamanho do modelo
- Tempo de inferência vs. tamanho do modelo
- Gráfico de barras de mAP por classe

### Visualização de Trade-off

Para entender os compromissos de desempenho entre modelos:

```bash
microdetect compare_models --model_paths model1.pt,model2.pt,model3.pt --data_yaml dataset/data.yaml --plot_tradeoff
```

Isso gera um gráfico de dispersão mostrando:
- mAP50 no eixo Y
- Tempo de inferência no eixo X
- Tamanho do modelo representado pelo tamanho da bolha
- Cada modelo como um ponto no gráfico

Esta visualização ajuda você a identificar rapidamente modelos que oferecem o melhor equilíbrio entre precisão e velocidade para suas necessidades.

### Comparação de Detecção

Para comparar visualmente resultados de detecção de múltiplos modelos:

```bash
microdetect compare_detections --model_paths model1.pt,model2.pt,model3.pt --source caminho/para/imagens --output_dir comparacao_deteccoes
```

Isso cria visualizações mostrando:
- Detecções de cada modelo com caixas delimitadoras de cores diferentes
- Pontuações de confiança para cada detecção
- Rótulos de classe e identificador do modelo
- Detecções sobrepostas e únicas

Essas visualizações ajudam você a entender diferenças qualitativas entre saídas de modelos.

## Framework de Tomada de Decisão

Ao selecionar o modelo ideal, considere o seguinte framework:

1. **Definir Requisitos**:
   - Limiar de precisão (mAP mínimo aceitável)
   - Requisitos de velocidade (FPS mínimo necessário)
   - Restrições de recursos (memória, computação)
   - Limitações de tamanho (para implantação em dispositivos)

2. **Priorizar Métricas**:
   - Aplicações de pesquisa: Priorizar precisão (mAP, recall)
   - Aplicações em tempo real: Priorizar velocidade (FPS, latência)
   - Implantação em dispositivos: Priorizar tamanho e eficiência do modelo

3. **Avaliar Trade-offs**:
   - Plotar mAP vs. tempo de inferência para encontrar modelos Pareto-ótimos
   - Calcular pontuações de eficiência (mAP/tamanho ou mAP/tempo de inferência)
   - Considerar desempenho específico por classe para aplicações especializadas

4. **Testar no Ambiente Alvo**:
   - Validar modelos pré-selecionados em condições reais de implantação
   - Medir métricas de desempenho do mundo real
   - Testar com dados representativos

## Melhores Práticas

1. **Use configurações de avaliação consistentes**: Compare modelos usando o mesmo limiar de confiança, limiar de IoU e conjunto de dados de teste

2. **Realize múltiplas execuções**: Faça a média dos resultados de múltiplas execuções de avaliação para comparações confiáveis

3. **Teste em amostras diversas**: Use um conjunto de teste representativo que cubra várias condições e casos limites

4. **Considere métricas específicas do domínio**: Para detecção de microorganismos, métricas específicas por classe podem ser mais importantes que métricas gerais

5. **Documente condições de comparação**: Registre hardware, versões de software e configurações específicas para reprodutibilidade

6. **Combine ambiente de teste com implantação**: Avalie modelos em condições similares ao seu ambiente de implantação pretendido

7. **Compare com linhas de base**: Inclua modelos estabelecidos como linhas de base em sua comparação

## Solução de Problemas

**Problema**: Grande disparidade em métricas entre modelos
**Solução**: Verifique se todos os modelos foram treinados em dados similares; verifique overfitting em modelos de alto desempenho

**Problema**: Medições de velocidade inconsistentes
**Solução**: Garanta que as condições de hardware sejam consistentes; use mais iterações com períodos de aquecimento

**Problema**: Dashboard falha ao carregar
**Solução**: Verifique se as dependências necessárias estão instaladas (`pip install dash dash-bootstrap-components plotly`)

**Problema**: Erro ao comparar modelos com classes diferentes
**Solução**: Garanta que todos os modelos tenham configurações de classe compatíveis; use a opção `--force_merge_classes`

**Problema**: Problemas de memória ao comparar múltiplos modelos grandes
**Solução**: Compare modelos sequencialmente em vez de simultaneamente; reduza o tamanho do lote; use modo CPU se a VRAM for limitada

**Problema**: Visualizações de comparação de detecção muito aglomeradas
**Solução**: Reduza o número de modelos sendo comparados de uma vez; aumente o limiar de confiança; compare em imagens mais simples

Para solução de problemas mais detalhada, consulte o [Guia de Solução de Problemas](troubleshooting.md).