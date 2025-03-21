# Guia de Treinamento

## Visão Geral

O MicroDetect fornece um fluxo de trabalho abrangente para treinar modelos YOLOv8 para detectar microorganismos em imagens de microscopia. Este guia irá orientá-lo através do processo de preparação dos dados, treinamento de modelos e avaliação de resultados.

## Pré-requisitos

- Dataset anotado preparado usando a ferramenta de anotação do Microdetect
- Ambiente Python com as dependências necessárias instaladas

## Preparando Seu Dataset

Antes do treinamento, você precisa organizar seu dataset no formato YOLOv8:

```bash
microdetect dataset --source_img_dir /caminho/para/imagens --source_label_dir /caminho/para/labels --val_split 0.2 --test_split 0.1
```

Este comando:
1. Cria divisões de treino/validação/teste a partir dos seus dados
2. Organiza imagens e labels nos diretórios corretos
3. Gera um arquivo de configuração `data.yaml` para o YOLOv8

### Opções:

- `--val_split`: Proporção de dados para usar na validação (padrão: 0.2)
- `--test_split`: Proporção de dados para usar nos testes (padrão: 0.1)
- `--classes`: Lista de nomes de classes separadas por vírgula (padrão: levedura,fungos,microalgas)
- `--output_dir`: Diretório de saída para o dataset (padrão: "dataset")

## Treinando um Modelo

Uma vez que seu dataset esteja preparado, você pode treinar um modelo YOLOv8:

```bash
microdetect train --dataset_dir dataset --model_size m --epochs 100 --batch_size 16
```

### Opções:

- `--dataset_dir`: Caminho para o diretório do dataset contendo data.yaml
- `--model_size`: Tamanho do modelo YOLOv8 (n, s, m, l, x) (padrão: "m")
- `--epochs`: Número de épocas de treinamento (padrão: 100)
- `--batch_size`: Tamanho do lote para treinamento (padrão: 16)
- `--img_size`: Tamanho da imagem de entrada (padrão: 640)
- `--patience`: Paciência para parada antecipada (padrão: 20)
- `--device`: Dispositivo a ser usado (cpu, mps, 0, 1, etc.) (padrão: detecção automática)
- `--resume`: Retomar treinamento do último checkpoint
- `--pretrained`: Usar pesos pré-treinados
- `--freeze`: Número de camadas para congelar (padrão: 0)

## Otimização de Hiperparâmetros

O MicroDetect suporta otimização de hiperparâmetros para encontrar a melhor configuração de modelo:

```bash
microdetect optimize --dataset_dir dataset --iterations 20 --metric map
```

### Opções:

- `--dataset_dir`: Caminho para o diretório do dataset contendo data.yaml
- `--iterations`: Número de combinações de hiperparâmetros para tentar (padrão: 20)
- `--metric`: Métrica a ser otimizada (map, precision, recall, F1) (padrão: "map")
- `--params`: Lista de parâmetros separados por vírgula para otimizar (model_size,lr,batch_size,img_size)

## Validação Cruzada

Para avaliar melhor o desempenho do modelo, especialmente com datasets pequenos, use validação cruzada:

```bash
microdetect cross_validate --dataset_dir dataset --model_size m --folds 5
```

### Opções:

- `--dataset_dir`: Caminho para o diretório do dataset contendo data.yaml
- `--model_size`: Tamanho do modelo YOLOv8 (n, s, m, l, x) (padrão: "m")
- `--folds`: Número de dobras de validação cruzada (padrão: 5)
- `--epochs`: Número de épocas de treinamento por dobra (padrão: 50)

## Avaliando Modelos

Após o treinamento, avalie o desempenho do seu modelo:

```bash
microdetect evaluate --model_path runs/train/yolov8_m_custom/weights/best.pt --dataset_dir dataset
```

### Opções:

- `--model_path`: Caminho para o modelo treinado
- `--dataset_dir`: Caminho para o diretório do dataset contendo data.yaml
- `--conf`: Limiar de confiança (padrão: 0.25)
- `--iou`: Limiar de IoU (padrão: 0.5)
- `--batch_size`: Tamanho do lote para avaliação (padrão: 16)
- `--device`: Dispositivo a ser usado (cpu, mps, 0, 1, etc.) (padrão: detecção automática)

## Comparando Múltiplos Modelos

Compare o desempenho de diferentes modelos:

```bash
microdetect compare_models --model_paths modelo1.pt,modelo2.pt,modelo3.pt --data_yaml dataset/data.yaml
```

### Opções:

- `--model_paths`: Lista de caminhos de modelo separados por vírgula
- `--data_yaml`: Caminho para o arquivo data.yaml
- `--conf`: Limiar de confiança (padrão: 0.25)
- `--iou`: Limiar de IoU (padrão: 0.5)
- `--output_dir`: Diretório para salvar os resultados da comparação (padrão: "comparison_results")

## Opções Avançadas de Treinamento

### Gerenciamento de Checkpoints

O MicroDetect salva automaticamente checkpoints durante o treinamento, que podem ser usados para retomar sessões de treinamento interrompidas:

```bash
microdetect train --dataset_dir dataset --resume
```

### Aceleração de Hardware

O sistema de treinamento detecta e usa automaticamente a aceleração de hardware disponível:

- CUDA para GPUs NVIDIA
- MPS para Apple Silicon
- Fallback para CPU se nenhuma GPU estiver disponível

Você pode substituir isso com o parâmetro `--device`.

### Transfer Learning

Use pesos pré-treinados para acelerar o treinamento e melhorar a precisão:

```bash
microdetect train --dataset_dir dataset --pretrained --freeze 10
```

Isso carrega pesos pré-treinados e congela as primeiras 10 camadas do modelo.

## Exemplo de Fluxo de Trabalho de Treinamento

Fluxo de trabalho completo desde a anotação até a implantação:

```bash
# Preparar dataset
microdetect dataset --source_img_dir data/imagens --source_label_dir data/labels

# Treinar modelo inicial
microdetect train --dataset_dir dataset --model_size s --epochs 50 --pretrained

# Otimizar hiperparâmetros
microdetect optimize --dataset_dir dataset --iterations 15

# Treinar modelo final com parâmetros otimizados
microdetect train --dataset_dir dataset --model_size m --epochs 150 --batch_size 32 --img_size 800

# Avaliar modelo
microdetect evaluate --model_path runs/train/yolov8_m_custom/weights/best.pt --dataset_dir dataset

# Exportar modelo
microdetect export --model_path runs/train/yolov8_m_custom/weights/best.pt --format onnx
```

## Melhores Práticas

1. **Comece Pequeno**: Inicie com um tamanho de modelo menor (n ou s) para garantir que o pipeline de treinamento funcione
2. **Use Pesos Pré-treinados**: Sempre comece com pesos pré-treinados, a menos que seu domínio seja muito diferente
3. **Augmentação de Dados**: Use augmentação de dados para melhorar a robustez do modelo
4. **Ajuste de Hiperparâmetros**: Encontre hiperparâmetros ótimos para seu dataset específico
5. **Monitoramento do Treinamento**: Observe sinais de overfitting (desempenho de validação piora enquanto o treinamento melhora)
6. **Múltiplos Modelos**: Treine várias variantes do modelo e compare seu desempenho
7. **Análise de Erros**: Analise falsos positivos e falsos negativos para entender as limitações do modelo

## Solução de Problemas

### Problemas Comuns

1. **Erros de Falta de Memória**: Reduza o tamanho do lote ou do modelo
2. **Treinamento Lento**: Verifique se a aceleração de hardware está funcionando corretamente
3. **Convergência Ruim**: Tente diferentes taxas de aprendizado ou configurações de otimizador
4. **Overfitting**: Aumente a augmentação de dados ou use parada antecipada
5. **Underfitting**: Treine por mais épocas ou use um modelo maior

Para solução de problemas mais detalhada, consulte o [Guia de Solução de Problemas](troubleshooting.md).