# Guia de Análise de Erros

Este guia explica como usar as capacidades de análise de erros do MicroDetect para identificar e compreender erros de detecção.

## Sumário
- [Introdução](#introdução)
- [Tipos de Erros de Detecção](#tipos-de-erros-de-detecção)
- [Usando a Ferramenta de Análise de Erros](#usando-a-ferramenta-de-análise-de-erros)
- [Analisando Visualizações de Erros](#analisando-visualizações-de-erros)
- [Compreendendo Distribuições de Erros](#compreendendo-distribuições-de-erros)
- [Melhorando o Desempenho do Modelo](#melhorando-o-desempenho-do-modelo)
- [Melhores Práticas](#melhores-práticas)
- [Solução de Problemas](#solução-de-problemas)

## Introdução

A análise de erros é uma etapa crítica no refinamento de modelos de detecção de objetos. Ela ajuda você a entender:

- Onde e por que seu modelo falha
- Quais tipos de erros são mais comuns
- Como melhorar o desempenho do seu modelo
- Qual augmentação de dados pode ser benéfica

O MicroDetect oferece ferramentas abrangentes para analisar diferentes tipos de erros de detecção, visualizá-los e gerar insights acionáveis.

## Tipos de Erros de Detecção

O MicroDetect identifica e analisa quatro tipos principais de erros de detecção:

1. **Falsos Positivos**: Detecções que não correspondem a objetos reais
   - O modelo detecta algo que não existe
   - Ocorre frequentemente com características de fundo que se assemelham a microorganismos

2. **Falsos Negativos**: Objetos que o modelo não consegue detectar
   - O modelo não identifica objetos presentes na imagem
   - Comum com microorganismos pequenos, desfocados ou parcialmente visíveis

3. **Erros de Classificação**: Detecção correta, mas classe errada
   - O modelo detecta um objeto, mas atribui a classe errada
   - Comum com tipos de microorganismos semelhantes

4. **Erros de Localização**: Objetos detectados, mas com baixa precisão na caixa delimitadora
   - O modelo detecta o objeto, mas não define com precisão seus limites
   - IoU (Intersection over Union) está abaixo do limiar ideal, mas ainda acima do limiar de detecção

## Usando a Ferramenta de Análise de Erros

### Uso Básico

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt \
                          --data_yaml dataset/data.yaml \
                          --dataset_dir dataset
```

Este comando analisa todos os tipos de erros no conjunto de teste e gera visualizações.

### Focando em Tipos Específicos de Erros

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt \
                          --data_yaml dataset/data.yaml \
                          --dataset_dir dataset \
                          --error_type false_positives
```

Tipos de erros válidos:
- `all` - Analisar todos os tipos de erros (padrão)
- `false_positives` - Focar em detecções de falsos positivos
- `false_negatives` - Focar em objetos não detectados
- `classification_errors` - Focar em detecções corretas com classe errada
- `localization_errors` - Focar em detecções com baixa precisão da caixa delimitadora

### Opções Adicionais

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt \
                          --data_yaml dataset/data.yaml \
                          --dataset_dir dataset \
                          --output_dir analise_erros \
                          --conf_threshold 0.3 \
                          --iou_threshold 0.5 \
                          --max_samples 30
```

- `--output_dir`: Diretório para salvar os resultados da análise de erros (padrão: error_analysis)
- `--conf_threshold`: Limiar de confiança para detecções (padrão: 0.25)
- `--iou_threshold`: Limiar de IoU para corresponder detecções com a verdade fundamental (padrão: 0.5)
- `--max_samples`: Número máximo de exemplos a serem salvos para cada tipo de erro (padrão: 20)

## Analisando Visualizações de Erros

A ferramenta de análise de erros gera visualizações para cada tipo de erro. Essas visualizações mostram:

1. **Falsos Positivos**: Caixas delimitadoras vermelhas mostrando detecções sem correspondência na verdade fundamental
   - Formato: "FP: [nome_da_classe] ([confiança])"
   
2. **Falsos Negativos**: Caixas delimitadoras verdes mostrando verdade fundamental que foi perdida
   - Formato: "FN: [nome_da_classe]"
   
3. **Erros de Classificação**: Caixas delimitadoras azuis mostrando detecções classificadas incorretamente
   - Formato: "CE: [classe_detectada] (GT: [classe_verdade_fundamental])"
   
4. **Erros de Localização**: Caixas delimitadoras ciano mostrando detecções com localização ruim
   - Formato: "LE: IoU=[valor_iou]"
   - Também mostra a verdade fundamental em contorno verde fino

As visualizações são salvas no diretório de saída, organizadas por tipo de erro:
```
error_analysis/
├── false_positives/
├── false_negatives/
├── classification_errors/
├── localization_errors/
├── error_analysis_report.json
└── error_summary.png
```

## Compreendendo Distribuições de Erros

A ferramenta também gera um gráfico de resumo de erros (`error_summary.png`) mostrando a distribuição de diferentes tipos de erros.

Este gráfico de barras ajuda você a entender:
- Quais tipos de erros são mais comuns
- As proporções relativas de diferentes erros
- Contagem total de erros

O relatório de análise de erros (`error_analysis_report.json`) contém estatísticas detalhadas sobre os erros:

```json
{
  "model": "yolov8s_custom.pt",
  "conf_threshold": 0.25,
  "iou_threshold": 0.5,
  "images_analyzed": 50,
  "error_counts": {
    "false_positives": 24,
    "false_negatives": 18,
    "classification_errors": 7,
    "localization_errors": 12
  },
  "error_examples": {
    "false_positives": 20,
    "false_negatives": 18,
    "classification_errors": 7,
    "localization_errors": 12
  }
}
```

## Melhorando o Desempenho do Modelo

Com base na análise de erros, você pode tomar as seguintes ações para melhorar seu modelo:

### Para Falsos Positivos:
- Aumentar o limiar de confiança
- Adicionar mais exemplos negativos (imagens sem microorganismos)
- Adicionar negativos difíceis (características de fundo que se assemelham a microorganismos)
- Revisar a qualidade das anotações para possíveis erros

### Para Falsos Negativos:
- Diminuir o limiar de confiança (mas observe o aumento de falsos positivos)
- Adicionar mais dados de treinamento para casos sub-representados
- Usar técnicas de augmentação de dados para aumentar a variação
- Considerar o uso de um modelo com mais capacidade

### Para Erros de Classificação:
- Adicionar mais dados de treinamento para classes confundidas
- Garantir que as diretrizes de anotação sejam claras para classes semelhantes
- Considerar a fusão de classes muito semelhantes se a distinção não for crítica
- Usar augmentação de dados especializada para classes difíceis

### Para Erros de Localização:
- Revisar as diretrizes de anotação para consistência na colocação de caixas delimitadoras
- Considerar o uso de um modelo maior com melhores capacidades de localização
- Adicionar mais exemplos de treinamento para objetos com limites difíceis
- Treinar por mais épocas para melhorar a precisão

## Melhores Práticas

1. **Comece com análise equilibrada**: Primeiro analise todos os tipos de erro para ter uma visão completa

2. **Concentre-se nos erros mais comuns**: Aborde primeiro os tipos de erro com as contagens mais altas

3. **Procure por padrões**: Analise vários exemplos para identificar padrões nos erros
   - Os falsos positivos são mais comuns em certas regiões da imagem?
   - Os falsos negativos estão associados a objetos menores?
   - Os erros de classificação estão ocorrendo entre classes específicas?

4. **Itere metodicamente**: Faça uma mudança de cada vez e avalie seu impacto

5. **Combine com outras análises**: Use junto com outras ferramentas como:
   - Comparação de modelos (`microdetect compare_models`)
   - Análise estatística (`microdetect analyze_distribution`)
   - Benchmarking de desempenho

## Solução de Problemas

### Problema: Nenhum erro encontrado apesar do baixo desempenho do modelo
**Solução**: Verifique os caminhos do conjunto de dados de teste e os formatos de anotação; tente diminuir o limiar de confiança

### Problema: Muitos erros de localização
**Solução**: Revise a consistência da anotação; considere retreinar com mais foco na precisão das caixas delimitadoras

### Problema: A análise de erros é muito lenta
**Solução**: Reduza o tamanho do conjunto de dados de teste ou use o parâmetro `--max_samples` para limitar exemplos

### Problema: Problemas de memória durante a análise
**Solução**: Processe menos imagens de cada vez com um tamanho de lote menor

Para mais informações sobre solução de problemas, consulte o [Guia de Solução de Problemas](troubleshooting.md).