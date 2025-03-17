# Guia de Avaliação Básica

Este guia explica os métodos fundamentais para avaliar modelos no MicroDetect, fornecendo uma introdução à avaliação de modelos antes de mergulhar em técnicas mais avançadas de avaliação.

## Sumário
- [Introdução](#introdução)
- [Avaliação Básica de Modelos](#avaliação-básica-de-modelos)
  - [Avaliando um Modelo Treinado](#avaliando-um-modelo-treinado)
  - [Compreendendo Métricas de Avaliação](#compreendendo-métricas-de-avaliação)
  - [Interpretando Resultados](#interpretando-resultados)
- [Validação Durante o Treinamento](#validação-durante-o-treinamento)
  - [Métricas de Validação](#métricas-de-validação)
  - [Curvas de Aprendizado](#curvas-de-aprendizado)
- [Testando em Novas Imagens](#testando-em-novas-imagens)
  - [Teste de Imagem Única](#teste-de-imagem-única)
  - [Teste em Lote](#teste-em-lote)
- [Ajustando Parâmetros de Detecção](#ajustando-parâmetros-de-detecção)
  - [Limiar de Confiança](#limiar-de-confiança)
  - [Limiar de IoU](#limiar-de-iou)
- [Salvando e Exportando Resultados](#salvando-e-exportando-resultados)
- [Próximos Passos](#próximos-passos)

## Introdução

A avaliação de modelos é uma etapa crítica no desenvolvimento de sistemas eficazes de detecção de microorganismos. Ela ajuda você a entender:

- Quão bem seu modelo está performando
- Se ele está pronto para uso prático
- Quais áreas precisam de melhoria

O MicroDetect fornece várias ferramentas para avaliação básica de modelos que não requerem conhecimento estatístico avançado, mas ainda fornecem insights valiosos sobre o desempenho do modelo.

## Avaliação Básica de Modelos

### Avaliando um Modelo Treinado

Para avaliar um modelo treinado em um conjunto de dados de teste:

```bash
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset
```

Parâmetros obrigatórios:
- `--model_path`: Caminho para o arquivo do modelo treinado (.pt)
- `--dataset_dir`: Diretório contendo o dataset com imagens e rótulos de teste

Parâmetros opcionais:
- `--conf_threshold`: Limiar de confiança para detecções (padrão: 0.25)
- `--iou_threshold`: Limiar de IoU para Non-Maximum Suppression (padrão: 0.7)
- `--batch_size`: Número de imagens a processar de uma vez (padrão: 16)

Este comando gera um relatório abrangente de avaliação no console e salva resultados detalhados no diretório do modelo.

### Compreendendo Métricas de Avaliação

A avaliação básica fornece as seguintes métricas-chave:

1. **Precisão**: A proporção de detecções que estão corretas (verdadeiros positivos divididos por todas as detecções)
   - Maior precisão significa menos falsos positivos
   - Intervalo: 0 a 1 (maior é melhor)

2. **Recall**: A proporção de microorganismos reais que foram detectados (verdadeiros positivos divididos por todos os objetos reais)
   - Maior recall significa menos falsos negativos (detecções perdidas)
   - Intervalo: 0 a 1 (maior é melhor)

3. **mAP50**: Precisão Média (AP) média com limiar de IoU de 0.5
   - Medida geral da qualidade de detecção, equilibrando precisão e recall
   - Intervalo: 0 a 1 (maior é melhor)

4. **Pontuação F1**: Média harmônica de precisão e recall
   - Métrica única equilibrando precisão e recall
   - Intervalo: 0 a 1 (maior é melhor)

Exemplo de saída:
```
Classe        Imagens   Rótulos  Precisão   Recall   mAP50  F1
Todas         50        230      0.962      0.921    0.947   0.941
Classe 0      50        98       0.981      0.934    0.972   0.957
Classe 1      50        87       0.953      0.932    0.943   0.942
Classe 2      50        45       0.951      0.897    0.925   0.923
```

### Interpretando Resultados

Como interpretar resultados de avaliação básica:

- **Bom desempenho**: Geralmente, mAP50 > 0.8 indica bom desempenho para detecção de microorganismos
- **Precisão e recall equilibrados**: Idealmente, tanto precisão quanto recall devem ser altos
- **Desequilíbrio de classe**: Verifique se o desempenho varia significativamente entre classes
- **Problemas comuns**:
  - Alta precisão mas baixo recall: Modelo está perdendo detecções (conservador)
  - Alto recall mas baixa precisão: Modelo tem muitos falsos positivos (muito permissivo)
  - Ambos baixos: Modelo precisa de melhoria ou retreinamento

## Validação Durante o Treinamento

### Métricas de Validação

Durante o treinamento, o MicroDetect valida automaticamente o modelo no conjunto de dados de validação em intervalos regulares. Essas métricas são salvas em:

```
runs/train/exp/results.csv
```

Este arquivo contém métricas por época incluindo:
- mAP50 de validação
- Precisão de validação
- Recall de validação
- Componentes de perda de treinamento (perda de caixa, perda de classe)

### Curvas de Aprendizado

Para visualizar curvas de aprendizado do treinamento:

```bash
microdetect plot_metrics --logdir runs/train/exp
```

Isso gera gráficos mostrando:
- Métricas de treinamento e validação ao longo do tempo
- Curvas de perda
- Desenvolvimento de precisão e recall
- Cronograma de taxa de aprendizado

Esses gráficos ajudam você a identificar:
- Se o modelo convergiu
- Se o modelo está sofrendo overfitting (métricas de treinamento melhoram enquanto métricas de validação pioram)
- Duração ideal de treinamento
- Efeito de mudanças na taxa de aprendizado

## Testando em Novas Imagens

### Teste de Imagem Única

Para testar seu modelo em uma única imagem:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source caminho/para/imagem.jpg
```

Isso executa inferência na imagem e exibe/salva o resultado com microorganismos detectados.

### Teste em Lote

Para testar em múltiplas imagens:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens
```

Opções:
- `--save_txt`: Salvar detecções em formato YOLO
- `--save_conf`: Incluir pontuações de confiança nos resultados salvos
- `--save_crop`: Salvar imagens recortadas de microorganismos detectados
- `--hide_labels`: Ocultar rótulos de classe nas imagens de saída
- `--hide_conf`: Ocultar pontuações de confiança nas imagens de saída

## Ajustando Parâmetros de Detecção

### Limiar de Confiança

O limiar de confiança controla quão confiante o modelo deve estar para reportar uma detecção:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens --conf_threshold 0.4
```

- **Limiar mais baixo** (ex: 0.1): Mais detecções, incluindo mais falsos positivos
- **Limiar mais alto** (ex: 0.7): Menos detecções, mas com maior confiança

Encontrando o limiar ideal:
- Comece com o padrão (0.25)
- Aumente se você vir muitos falsos positivos
- Diminua se estiver perdendo detecções que deseja capturar

### Limiar de IoU

O limiar de IoU (Interseção sobre União) controla quanto sobreposição as detecções precisam ter para serem consideradas duplicatas:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens --iou_threshold 0.5
```

- **Limiar mais baixo** (ex: 0.3): Mais agressivo na remoção de caixas sobrepostas
- **Limiar mais alto** (ex: 0.7): Mais permissivo com detecções sobrepostas

Este parâmetro é especialmente importante para microorganismos densamente agrupados.

## Salvando e Exportando Resultados

Para salvar resultados de avaliação para análise adicional:

```bash
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --save_json
```

Isso salva resultados em um arquivo JSON que inclui:
- Métricas gerais
- Métricas por classe
- Parâmetros de avaliação
- Estatísticas de desempenho

Você também pode exportar resultados em diferentes formatos:

```bash
# Exportar como CSV
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --format csv --output_file resultados.csv

# Gerar relatório HTML
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --format html --output_file relatorio.html
```

## Próximos Passos

Após a avaliação básica, considere estes próximos passos:

1. **Avaliação avançada**: Para insights mais profundos, veja o [Guia de Avaliação e Análise de Modelos](model_evaluation_analysis.md)

2. **Análise de erros**: Para entender as fraquezas do modelo, veja o [Guia de Análise de Erros](error_analysis.md)

3. **Comparação de modelos**: Para comparar diferentes modelos, veja o [Guia de Comparação de Modelos](model_comparison.md)

4. **Otimização de modelo**: Se o desempenho for insuficiente, tente:
   - Coletar mais dados de treinamento
   - Melhorar a qualidade da anotação
   - Usar um modelo maior (de nano para pequeno, médio ou grande)
   - Ajustar hiperparâmetros de treinamento

5. **Análise estatística**: Para analisar padrões de detecção, veja o [Guia de Análise Estatística](statistical_analysis.md)