# Guia de Análise Estatística

Este guia explica como usar as ferramentas de análise estatística do MicroDetect para extrair insights dos resultados de detecção.

## Sumário
- [Introdução](#introdução)
- [Análise de Densidade](#análise-de-densidade)
  - [Gerando Mapas de Densidade](#gerando-mapas-de-densidade)
  - [Interpretando Mapas de Densidade](#interpretando-mapas-de-densidade)
  - [Análise de Densidade por Classe](#análise-de-densidade-por-classe)
- [Análise de Distribuição de Tamanho](#análise-de-distribuição-de-tamanho)
  - [Análise Básica de Tamanho](#análise-básica-de-tamanho)
  - [Estatísticas de Tamanho](#estatísticas-de-tamanho)
  - [Comparando Classes](#comparando-classes)
- [Análise Espacial](#análise-espacial)
  - [Análise de Distância](#análise-de-distância)
  - [Análise de Agrupamento](#análise-de-agrupamento)
  - [Análise de Relacionamento entre Classes](#análise-de-relacionamento-entre-classes)
- [Análise Temporal](#análise-temporal)
  - [Rastreando Mudanças ao Longo do Tempo](#rastreando-mudanças-ao-longo-do-tempo)
  - [Análise de Taxa de Crescimento](#análise-de-taxa-de-crescimento)
- [Processamento em Lote](#processamento-em-lote)
  - [Processando Múltiplas Imagens](#processando-múltiplas-imagens)
  - [Funções de Análise Personalizadas](#funções-de-análise-personalizadas)
- [Integração com Outras Ferramentas](#integração-com-outras-ferramentas)
- [Melhores Práticas](#melhores-práticas)
- [Solução de Problemas](#solução-de-problemas)

## Introdução

A análise estatística dos resultados de detecção ajuda a extrair padrões significativos e insights dos dados de microorganismos. O MicroDetect fornece várias ferramentas para analisar:

- **Distribuição Espacial**: Onde os microorganismos aparecem nas imagens
- **Distribuição de Tamanho**: Como os tamanhos dos microorganismos variam
- **Padrões de Densidade**: Concentrações e agrupamentos
- **Relacionamentos**: Como diferentes classes se relacionam espacialmente
- **Mudanças Temporais**: Como as populações mudam ao longo do tempo

Essas análises ajudam você a:
- Entender características da população de microorganismos
- Identificar padrões espaciais e relacionamentos
- Rastrear mudanças nas populações ao longo do tempo
- Tomar decisões baseadas em dados

## Análise de Densidade

A análise de densidade visualiza a concentração de detecções nas imagens, mostrando onde os microorganismos comumente aparecem.

### Gerando Mapas de Densidade

Para criar mapas de densidade a partir dos resultados de detecção:

```python
from microdetect.analysis import StatisticalAnalyzer

analyzer = StatisticalAnalyzer(output_dir="analysis_results")

# Gerar um mapa de densidade a partir de detecções
density_map_path = analyzer.generate_density_map(
    detections=resultados_deteccao,            # Lista de dicionários de detecção
    image_size=(1280, 960),                    # Largura, altura da imagem
    output_path="mapa_densidade.png",          # Caminho para salvar o mapa
    sigma=10.0,                                # Parâmetro de suavização
    by_class=False                             # Gerar um único mapa para todas as classes
)
```

Você também pode usar a interface de linha de comando:

```bash
microdetect analyze_distribution --model_path runs/train/exp/weights/best.pt \
                                --source caminho/para/imagens \
                                --output_dir mapas_densidade \
                                --sigma 10.0
```

### Interpretando Mapas de Densidade

Os mapas de densidade usam gradientes de cores para mostrar concentração:
- **Áreas vermelhas/amarelas**: Alta concentração de detecções
- **Áreas verdes**: Concentração moderada
- **Áreas azuis**: Baixa concentração
- **Áreas azul escuro**: Poucas ou nenhuma detecção

Os mapas de densidade ajudam a identificar:
- Pontos críticos onde microorganismos frequentemente aparecem
- Regiões vazias com poucas ou nenhuma detecção
- Gradientes que podem indicar fatores ambientais

### Análise de Densidade por Classe

Para analisar padrões de densidade para classes específicas:

```python
# Gerar mapas de densidade separados para cada classe
mapas_densidade_classe = analyzer.generate_density_map(
    detections=resultados_deteccao,
    image_size=(1280, 960),
    output_path="mapas_densidade/todas_classes.png",
    by_class=True                  # Gerar mapas separados para cada classe
)

# Acessar mapas individuais por classe
print(f"Mapa para classe 0: {mapas_densidade_classe['0']}")
print(f"Mapa para classe 1: {mapas_densidade_classe['1']}")
```

Usando a interface de linha de comando com a flag `--by_class`:

```bash
microdetect analyze_distribution --model_path runs/train/exp/weights/best.pt \
                                --source caminho/para/imagens \
                                --output_dir mapas_densidade \
                                --by_class
```

## Análise de Distribuição de Tamanho

A análise de distribuição de tamanho examina a variação nos tamanhos de microorganismos em seu dataset.

### Análise Básica de Tamanho

Para analisar a distribuição de tamanho dos microorganismos detectados:

```python
from microdetect.analysis import StatisticalAnalyzer

analyzer = StatisticalAnalyzer(output_dir="analysis_results")

# Analisar distribuição de tamanho
resultados_analise_tamanho = analyzer.analyze_size_distribution(
    detections=resultados_deteccao,            # Lista de dicionários de detecção
    output_dir="analise_tamanho",              # Diretório para salvar resultados
    by_class=True                              # Análise separada por classe
)
```

Usando a interface de linha de comando:

```bash
microdetect analyze_size --model_path runs/train/exp/weights/best.pt \
                        --source caminho/para/imagens \
                        --output_dir analise_tamanho
```

Isso gera:
- Histogramas mostrando a distribuição geral de tamanho
- Histogramas de distribuição de tamanho específicos por classe
- Dados CSV para análise adicional
- Resumo estatístico em formato JSON

### Estatísticas de Tamanho

A análise de tamanho produz um arquivo JSON (`size_stats.json`) com estatísticas:

```json
{
  "all": {
    "mean": 124.5,
    "median": 118.2,
    "std": 32.7,
    "min": 45.3,
    "max": 278.9,
    "count": 523
  },
  "class_0": {
    "mean": 135.8,
    "median": 129.4,
    "std": 35.2,
    "min": 48.7,
    "max": 278.9,
    "count": 312
  },
  "class_1": {
    "mean": 107.3,
    "median": 102.8,
    "std": 22.5,
    "min": 45.3,
    "max": 189.6,
    "count": 211
  }
}
```

Essas estatísticas ajudam você a:
- Entender a faixa de tamanho típica para cada tipo de microorganismo
- Identificar outliers que podem indicar erros de detecção
- Comparar distribuições de tamanho entre classes

### Comparando Classes

A visualização `size_distribution_by_class.png` mostra distribuições de tamanho para todas as classes em um único gráfico, facilitando a comparação:
- Faixas de tamanho entre diferentes tipos de microorganismos
- Sobreposição entre distribuições de tamanho
- Potenciais regras de classificação baseadas em tamanho

## Análise Espacial

A análise espacial examina os relacionamentos e padrões nas posições dos microorganismos detectados.

### Análise de Distância

Para analisar as distâncias entre microorganismos detectados:

```python
from microdetect.analysis import StatisticalAnalyzer

analyzer = StatisticalAnalyzer(output_dir="analysis_results")

# Analisar relacionamentos espaciais
resultados_espaciais = analyzer.analyze_spatial_relationships(
    detections=resultados_deteccao,            # Lista de dicionários de detecção
    output_dir="analise_espacial",             # Diretório para salvar resultados
    min_distance=0.02,                         # Distância mínima para agrupamento
    by_class=True                              # Analisar relacionamentos entre classes
)
```

Usando a interface de linha de comando:

```bash
microdetect analyze_spatial --model_path runs/train/exp/weights/best.pt \
                           --source caminho/para/imagens \
                           --output_dir analise_espacial \
                           --min_distance 0.02
```

A análise de distância produz:
- Histograma de distâncias entre microorganismos
- Gráfico de dispersão mostrando distribuição espacial
- Estatísticas de vizinhos mais próximos

### Análise de Agrupamento

A análise de agrupamento identifica grupos de microorganismos que aparecem próximos uns dos outros:

```python
# A função analyze_spatial_relationships também realiza agrupamento
# Defina um min_distance menor para agrupamentos mais compactos
resultados_espaciais = analyzer.analyze_spatial_relationships(
    detections=resultados_deteccao,
    output_dir="analise_espacial",
    min_distance=0.015,                       # Distância menor para agrupamentos mais compactos
    by_class=True
)
```

A visualização de agrupamento mostra:
- Agrupamentos identificados com diferentes cores
- Número de microorganismos em cada agrupamento
- Limites e distribuição de agrupamentos

### Análise de Relacionamento entre Classes

A análise de relacionamento entre classes examina como diferentes tipos de microorganismos interagem espacialmente:

```bash
microdetect analyze_spatial --model_path runs/train/exp/weights/best.pt \
                           --source caminho/para/imagens \
                           --output_dir analise_espacial \
                           --by_class
```

Isso gera um mapa de calor de co-ocorrência mostrando:
- Quais classes tendem a aparecer juntas
- Quais classes raramente co-ocorrem
- Associações espaciais entre classes

A razão de co-ocorrência indica:
- Valores > 1: Classes co-ocorrem mais frequentemente do que o esperado pelo acaso (associação positiva)
- Valores = 1: Classes co-ocorrem conforme esperado pelo acaso (sem associação)
- Valores < 1: Classes co-ocorrem menos frequentemente do que o esperado pelo acaso (associação negativa)

## Análise Temporal

A análise temporal rastreia mudanças nas populações de microorganismos ao longo do tempo, útil para estudar crescimento, declínio ou mudanças ecológicas.

### Rastreando Mudanças ao Longo do Tempo

Para analisar mudanças ao longo do tempo em suas detecções:

```python
from microdetect.analysis import StatisticalAnalyzer

analyzer = StatisticalAnalyzer(output_dir="analysis_results")

# Preparar dados de série temporal
dados_serie_temporal = [
    {
        "timestamp": "2023-01-01",
        "count": 245,
        "class_counts": {"0": 125, "1": 85, "2": 35}
    },
    {
        "timestamp": "2023-01-08",
        "count": 278,
        "class_counts": {"0": 142, "1": 92, "2": 44}
    },
    # Pontos de tempo adicionais...
]

# Analisar dados temporais
resultados_temporais = analyzer.analyze_temporal_data(
    time_series_data=dados_serie_temporal,     # Lista de dicionários de pontos de tempo
    output_dir="analise_temporal",             # Diretório para salvar resultados
    date_format="%Y-%m-%d"                     # Formato das strings de data
)
```

Usando a interface de linha de comando (com um arquivo CSV contendo dados de série temporal):

```bash
microdetect analyze_temporal --data_file serie_temporal.csv \
                            --output_dir analise_temporal
```

Isso gera:
- Gráficos de linha mostrando mudanças na população ao longo do tempo
- Gráficos de área empilhada mostrando proporções de classe
- Gráficos de taxa de crescimento

### Análise de Taxa de Crescimento

A análise temporal calcula taxas de crescimento entre pontos de tempo:

```python
# A função analyze_temporal_data calcula taxas de crescimento
# Os resultados incluem gráfico de taxa de crescimento e estatísticas
resultados_temporais = analyzer.analyze_temporal_data(
    time_series_data=dados_serie_temporal,
    output_dir="analise_temporal"
)
```

A visualização da taxa de crescimento mostra:
- Mudança percentual entre pontos de tempo
- Períodos de crescimento e declínio
- Diferenças na taxa de crescimento entre classes

A análise também fornece estatísticas resumidas:
- Taxa de crescimento média
- Taxas de crescimento máxima e mínima
- Variabilidade da taxa de crescimento

## Processamento em Lote

Para analisar grandes conjuntos de dados, o MicroDetect fornece capacidades de processamento em lote.

### Processando Múltiplas Imagens

Para processar um lote de imagens:

```python
from microdetect.analysis import BatchProcessor

processor = BatchProcessor(num_workers=4)      # Usar 4 workers paralelos

# Processar um lote de imagens
resultados = processor.process_batch(
    model_path="runs/train/exp/weights/best.pt",  # Caminho para o modelo
    source_dir="caminho/para/imagens",            # Diretório com imagens
    output_dir="resultados_lote",                 # Diretório para resultados
    batch_size=16,                                # Imagens por lote
    conf_threshold=0.25,                          # Limiar de confiança
    save_txt=True,                                # Salvar anotações em formato YOLO
    save_json=True                                # Salvar resultados em JSON
)
```

Usando a interface de linha de comando:

```bash
microdetect batch_detect --model_path runs/train/exp/weights/best.pt \
                        --source caminho/para/imagens \
                        --output_dir resultados_lote \
                        --batch_size 16 \
                        --save_json
```

### Funções de Análise Personalizadas

Para análises avançadas, você pode definir funções de processamento personalizadas:

```python
from microdetect.analysis import BatchProcessor

# Definir uma função worker personalizada
def analise_personalizada(model, image_path, output_dir, **kwargs):
    # Executar detecção
    results = model(image_path, **kwargs)
    
    # Realizar análise personalizada
    # ...
    
    return {
        "metrica_personalizada": valor_personalizado,
        "deteccoes": deteccoes
    }

# Processar com função personalizada
processor = BatchProcessor(num_workers=4)
resultados = processor.process_parallel(
    model_path="runs/train/exp/weights/best.pt",
    source_dir="caminho/para/imagens",
    output_dir="analise_personalizada",
    worker_function=analise_personalizada,
    worker_args={
        "conf": 0.25,
        "iou": 0.45
    }
)
```

## Integração com Outras Ferramentas

As ferramentas de análise estatística do MicroDetect podem ser integradas com outras ferramentas:

### Exportando para CSV para Análise Externa

```python
# Exportar para CSV para análise em outras ferramentas
analyzer.export_to_csv(
    data=resultados_deteccao,
    output_file="deteccoes.csv"
)
```

O arquivo CSV pode ser importado em:
- Aplicativos de planilha (Excel, Google Sheets)
- Pacotes estatísticos (R, SPSS)
- Ferramentas de visualização de dados (Tableau, Power BI)

### Integração com Ecossistema Científico Python

```python
# Converter resultados para pandas DataFrame para análise adicional
import pandas as pd

# Dados de análise de tamanho
size_df = pd.read_csv("analise_tamanho/size_distribution_data.csv")

# Análise adicional com pandas
tamanho_por_classe = size_df.groupby('classe')['tamanho'].agg(['mean', 'std', 'min', 'max'])
print(tamanho_por_classe)

# Testes estatísticos (usando scipy)
from scipy import stats
t_stat, p_value = stats.ttest_ind(
    size_df[size_df['classe'] == 0]['tamanho'],
    size_df[size_df['classe'] == 1]['tamanho']
)
print(f"estatística-t: {t_stat}, p-valor: {p_value}")
```

## Melhores Práticas

1. **Comece com análise exploratória**: Use mapas de densidade e distribuição de tamanho antes de análises mais complexas

2. **Combine análises**: Integre insights de diferentes análises para uma visão completa

3. **Valide com conhecimento de domínio**: Interprete resultados no contexto de princípios microbiológicos

4. **Verifique detecções primeiro**: Execute análise de erros antes da análise estatística para garantir dados de entrada confiáveis

5. **Considere a escala**: Leve em conta a escala/ampliação da imagem ao comparar tamanhos entre diferentes conjuntos de dados

6. **Use suavização apropriada**: Ajuste o parâmetro sigma para mapas de densidade com base na resolução da imagem

7. **Documente parâmetros de análise**: Registre parâmetros como min_distance para reprodutibilidade

8. **Valide resultados de agrupamento**: Experimente diferentes valores de min_distance para garantir identificação robusta de agrupamentos

## Solução de Problemas

### Problema: Mapas de densidade aparecem muito suaves ou muito ruidosos
**Solução**: Ajuste o parâmetro sigma (maior para mais suave, menor para detalhes mais finos)

### Problema: Análise de tamanho mostra resultados inesperados
**Solução**: Verifique se as caixas delimitadoras estão normalizadas (0-1) ou em pixels absolutos; verifique a qualidade da detecção

### Problema: Nenhum agrupamento encontrado na análise espacial
**Solução**: Tente aumentar o parâmetro min_distance; verifique se as detecções têm coordenadas adequadas

### Problema: Análise temporal mostra mudanças abruptas
**Solução**: Verifique configurações de detecção consistentes em todos os pontos de tempo; verifique problemas de coleta de dados

### Problema: Processamento em lote está lento
**Solução**: Reduza o tamanho do lote; aumente num_workers se a CPU tiver muitos núcleos; use um tamanho de modelo menor

### Problema: Erros de memória durante processamento em lote
**Solução**: Reduza o tamanho do lote; processe imagens em grupos menores; use uma resolução menor

Para mais informações sobre solução de problemas, consulte o [Guia de Solução de Problemas](troubleshooting.md).