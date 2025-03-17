# Documentação: Fluxo de Trabalho Completo com MicroDetect

## Visão Geral

Este documento descreve o fluxo de trabalho completo para utilização do framework MicroDetect para detecção de microorganismos com YOLOv8, desde a preparação inicial dos dados até a geração de relatórios e dashboards para apresentação dos resultados.

## Pré-requisitos

- MicroDetect instalado e configurado
- Python 3.8+ com dependências instaladas
- Acesso às imagens de microorganismos
- GPU recomendada para treinamento (opcional, mas desejável)

## 1. Preparação do Ambiente e Dados

### 1.1 Inicialização do Projeto

```bash
microdetect init --project nome_do_projeto
```

**Descrição**: Este comando cria a estrutura base de diretórios para o projeto, incluindo pastas para datasets, modelos, resultados e relatórios. Também configura arquivos de configuração iniciais.

**Parâmetros**:
- `--project`: Nome do projeto/diretório a ser criado

### 1.2 Conversão de Imagens

```bash
microdetect convert --source caminho/para/imagens --format yolo --output datasets/raw
```

**Descrição**: Converte as imagens do formato original para um formato padronizado compatível com o pipeline de treinamento e anotação do YOLO.

**Parâmetros**:
- `--source`: Diretório contendo as imagens originais
- `--format`: Formato de saída desejado (geralmente 'yolo')
- `--output`: Diretório de destino para as imagens convertidas

### 1.3 Anotação de Imagens

```bash
microdetect annotate --images datasets/raw/images --output datasets/raw/labels
```

**Descrição**: Abre a interface de anotação para marcar objetos nas imagens manualmente. Esta etapa é necessária apenas se as imagens ainda não estiverem anotadas.

**Parâmetros**:
- `--images`: Diretório contendo as imagens a serem anotadas
- `--output`: Diretório onde as anotações serão salvas

## 2. Organização e Aumento do Dataset

### 2.1 Aumento de Dataset (Data Augmentation)

```bash
microdetect augment --images datasets/raw/images --labels datasets/raw/labels --output datasets/augmented --factor 3 --techniques flip,rotate,brightness
```

**Descrição**: Aplica técnicas de aumento de dados para expandir o conjunto de treinamento, melhorando a capacidade de generalização do modelo.

**Parâmetros**:
- `--images`: Caminho para as imagens originais
- `--labels`: Caminho para as anotações originais
- `--output`: Diretório para salvar as imagens e anotações aumentadas
- `--factor`: Fator de multiplicação do dataset (3 = tamanho final 3x maior)
- `--techniques`: Lista de técnicas de aumento a serem aplicadas

### 2.2 Organização do Dataset

```bash
microdetect dataset --source datasets/augmented --output datasets/final --split 70,20,10
```

**Descrição**: Organiza o dataset em conjuntos de treino, validação e teste, aplicando a divisão especificada.

**Parâmetros**:
- `--source`: Diretório contendo o dataset aumentado
- `--output`: Diretório para o dataset final organizado
- `--split`: Proporção da divisão treino/validação/teste em porcentagem

## 3. Treinamento de Modelos

### 3.1 Treinamento do Modelo Base

```bash
microdetect train --data datasets/final/data.yaml --model yolov8n.pt --epochs 100 --batch 16 --name modelo_base --img 640 --patience 20
```

**Descrição**: Treina um modelo YOLOv8 nano usando o dataset preparado.

**Parâmetros**:
- `--data`: Arquivo YAML descrevendo o dataset
- `--model`: Modelo base pré-treinado para fine-tuning
- `--epochs`: Número de épocas de treinamento
- `--batch`: Tamanho do lote (batch size)
- `--name`: Nome do experimento
- `--img`: Resolução das imagens de treinamento
- `--patience`: Número de épocas para early stopping

### 3.2 Treinamento de Modelos Variantes

```bash
microdetect train --data datasets/final/data.yaml --model yolov8s.pt --epochs 100 --batch 16 --name modelo_medio --img 640 --patience 20
```

```bash
microdetect train --data datasets/final/data.yaml --model yolov8m.pt --epochs 100 --batch 8 --name modelo_grande --img 640 --patience 20
```

**Descrição**: Treina modelos YOLOv8 variantes (small e medium) para possibilitar comparação de desempenho entre diferentes tamanhos de modelo.

## 4. Avaliação e Comparação de Modelos

### 4.1 Avaliação Individual de Modelos

```bash
microdetect evaluate --model runs/train/modelo_base/weights/best.pt --data datasets/final/data.yaml --batch 16 --output_dir reports/evaluation/modelo_base
```

**Descrição**: Avalia o desempenho do modelo treinado no conjunto de teste, gerando métricas detalhadas.

**Parâmetros**:
- `--model`: Caminho para o arquivo de pesos do modelo
- `--data`: Arquivo YAML do dataset
- `--batch`: Tamanho do lote para avaliação
- `--output_dir`: Diretório para salvar os resultados da avaliação

### 4.2 Comparação de Múltiplos Modelos

```bash
microdetect compare_models --model_paths runs/train/modelo_base/weights/best.pt,runs/train/modelo_medio/weights/best.pt,runs/train/modelo_grande/weights/best.pt --data_yaml datasets/final/data.yaml --output_dir reports/comparacao_modelos --conf_threshold 0.25 --iou_threshold 0.45 --dashboard
```

**Descrição**: Compara os diferentes modelos treinados, gerando tabelas e gráficos comparativos de métricas de desempenho.

**Parâmetros**:
- `--model_paths`: Lista separada por vírgulas dos caminhos para os modelos a serem comparados
- `--data_yaml`: Arquivo YAML do dataset
- `--output_dir`: Diretório para salvar os resultados da comparação
- `--conf_threshold`: Limiar de confiança para detecções
- `--iou_threshold`: Limiar de IoU para avaliação
- `--dashboard`: Gera um dashboard interativo com os resultados da comparação

### 4.3 Análise de Erros

```bash
microdetect analyze_errors --model_path runs/train/modelo_medio/weights/best.pt --data_yaml datasets/final/data.yaml --dataset_dir datasets/final/test --error_type all --output_dir reports/analise_erros
```

**Descrição**: Analisa diferentes tipos de erros cometidos pelo modelo, categorizando-os e fornecendo exemplos visuais.

**Parâmetros**:
- `--model_path`: Caminho para o arquivo de pesos do modelo
- `--data_yaml`: Arquivo YAML do dataset
- `--dataset_dir`: Diretório contendo o conjunto de teste
- `--error_type`: Tipo de erro a analisar ('false_positives', 'false_negatives', 'classification', 'localization', ou 'all')
- `--output_dir`: Diretório para salvar os resultados da análise

## 5. Processamento de Imagens e Visualização

### 5.1 Detecção em Lote

```bash
microdetect batch_detect --model_path runs/train/modelo_medio/weights/best.pt --source datasets/final/test/images --output_dir results/batch_detections --conf_threshold 0.25 --batch_size 16 --save_txt --save_img --save_json
```

**Descrição**: Processa um conjunto de imagens com o modelo treinado, gerando visualizações e arquivos de detecção.

**Parâmetros**:
- `--model_path`: Caminho para o arquivo de pesos do modelo
- `--source`: Diretório contendo as imagens a serem processadas
- `--output_dir`: Diretório para salvar os resultados
- `--conf_threshold`: Limiar de confiança para detecções
- `--batch_size`: Tamanho do lote para processamento
- `--save_txt`: Salva as detecções em formato texto (YOLO)
- `--save_img`: Salva as imagens com as detecções desenhadas
- `--save_json`: Salva as detecções em formato JSON

### 5.2 Visualização Interativa de Detecções

```bash
microdetect visualize_detections --model_path runs/train/modelo_medio/weights/best.pt --source results/batch_detections/images --conf_threshold 0.25
```

**Descrição**: Abre uma interface interativa para visualizar e explorar as detecções realizadas pelo modelo.

**Parâmetros**:
- `--model_path`: Caminho para o arquivo de pesos do modelo
- `--source`: Diretório contendo as imagens a serem visualizadas
- `--conf_threshold`: Limiar de confiança para detecções

## 6. Geração de Relatório e Dashboard

### 6.1 Geração de Relatório

```bash
microdetect generate_report --results_dir reports/comparacao_modelos --format pdf --output_file tcc_resultados.pdf --include_images results/batch_detections/images/exemplo1.jpg,results/batch_detections/images/exemplo2.jpg
```

**Descrição**: Gera um relatório completo em PDF contendo métricas, gráficos e exemplos de detecções.

**Parâmetros**:
- `--results_dir`: Diretório contendo os resultados da avaliação/comparação
- `--format`: Formato do relatório ('pdf', 'csv', 'json')
- `--output_file`: Caminho para o arquivo de saída
- `--include_images`: Lista separada por vírgulas de imagens a incluir no relatório

### 6.2 Criação de Dashboard

```bash
microdetect dashboard --results_dir reports/comparacao_modelos --port 8050 --no_browser
```

**Descrição**: Cria um dashboard web interativo para explorar os resultados das detecções e avaliações.

**Parâmetros**:
- `--results_dir`: Diretório contendo os resultados a serem visualizados
- `--port`: Porta para servir o dashboard (padrão: 8050)
- `--no_browser`: Não abre o navegador automaticamente

## Fluxo de Trabalho Completo (Script)

Para automatizar o processo completo, você pode criar um script com todos os comandos em sequência:

```bash
#!/bin/bash

# 1. Preparação do ambiente e dados
microdetect init --project tcc_microdetect
microdetect convert --source imagens_originais/ --format yolo --output datasets/raw

# Passo manual: anotação de imagens (se necessário)
# microdetect annotate --images datasets/raw/images --output datasets/raw/labels

# 2. Organização e aumento do dataset
microdetect augment --images datasets/raw/images --labels datasets/raw/labels --output datasets/augmented --factor 3 --techniques flip,rotate,brightness
microdetect dataset --source datasets/augmented --output datasets/final --split 70,20,10

# 3. Treinamento de modelos
microdetect train --data datasets/final/data.yaml --model yolov8n.pt --epochs 100 --batch 16 --name modelo_base
microdetect train --data datasets/final/data.yaml --model yolov8s.pt --epochs 100 --batch 16 --name modelo_medio
microdetect train --data datasets/final/data.yaml --model yolov8m.pt --epochs 100 --batch 8 --name modelo_grande

# 4. Avaliação e comparação
microdetect evaluate --model runs/train/modelo_base/weights/best.pt --data datasets/final/data.yaml --output_dir reports/evaluation/modelo_base
microdetect evaluate --model runs/train/modelo_medio/weights/best.pt --data datasets/final/data.yaml --output_dir reports/evaluation/modelo_medio
microdetect evaluate --model runs/train/modelo_grande/weights/best.pt --data datasets/final/data.yaml --output_dir reports/evaluation/modelo_grande

microdetect compare_models --model_paths runs/train/modelo_base/weights/best.pt,runs/train/modelo_medio/weights/best.pt,runs/train/modelo_grande/weights/best.pt --data_yaml datasets/final/data.yaml --output_dir reports/comparacao_modelos --dashboard

microdetect analyze_errors --model_path runs/train/modelo_medio/weights/best.pt --data_yaml datasets/final/data.yaml --dataset_dir datasets/final/test --output_dir reports/analise_erros

# 5. Processamento e visualização
microdetect batch_detect --model_path runs/train/modelo_medio/weights/best.pt --source datasets/final/test/images --output_dir results/batch_detections --save_txt --save_img --save_json

# 6. Relatório e dashboard
microdetect generate_report --results_dir reports/comparacao_modelos --format pdf --output_file tcc_resultados.pdf
microdetect dashboard --results_dir reports/comparacao_modelos
```

## Considerações Finais

- Escolha o melhor modelo baseado na comparação de métricas e requisitos (velocidade vs. precisão)
- Inclua exemplos visuais de sucessos e falhas do modelo no relatório final
- Documente todas as escolhas e experimentos realizados durante o desenvolvimento
- Mantenha os arquivos de métricas e resultados organizados para facilitar a escrita do TCC
- Para apresentações, o dashboard interativo oferece uma maneira dinâmica de mostrar os resultados

## Leitura Recomendada

- Documentação oficial do YOLOv8
- Artigos sobre técnicas de detecção de objetos em imagens microscópicas
- Guias sobre interpretação de métricas de avaliação para modelos de detecção de objetos