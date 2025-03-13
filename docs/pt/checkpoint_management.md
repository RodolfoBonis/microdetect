# Guia de Gerenciamento de Checkpoints

Este guia explica como gerenciar efetivamente checkpoints ao treinar modelos YOLOv8 com o MicroDetect, incluindo salvamento, retomada de treinamento e melhores práticas.

## Visão Geral

O gerenciamento de checkpoints é crucial para o desenvolvimento eficiente de modelos. A funcionalidade de checkpoint do MicroDetect permite:

- Salvar o estado do modelo em intervalos regulares durante o treinamento
- Retomar o treinamento a partir de um checkpoint salvo
- Exportar o melhor modelo para implantação
- Analisar diferentes checkpoints para entender a melhoria do modelo ao longo do tempo

## Entendendo Checkpoints

No MicroDetect, um checkpoint é um estado salvo do modelo durante o treinamento, contendo:

- Pesos do modelo
- Estado do otimizador
- Época de treinamento
- Melhores métricas alcançadas
- Estado do agendamento de taxa de aprendizado
- Outros metadados de treinamento

Isso permite continuar o treinamento de onde você parou sem precisar começar do zero.

## Operações Básicas de Checkpoint

### Salvando Checkpoints

Por padrão, o MicroDetect salva automaticamente checkpoints durante o treinamento:

```bash
microdetect train --dataset_dir dataset --model_size s --epochs 100
```

Isso salvará:
- `last.pt`: O estado mais recente do modelo
- `best.pt`: O modelo com o melhor desempenho de validação

Você pode personalizar a frequência de salvamento de checkpoints:

```bash
microdetect train --dataset_dir dataset --save_period 10
```

Isso salva um checkpoint a cada 10 épocas.

### Retomando o Treinamento

Para retomar o treinamento a partir de um checkpoint:

```bash
microdetect resume --checkpoint_path runs/train/yolov8_s_custom/weights/last.pt --epochs 50
```

Isso irá:
1. Carregar o estado do modelo a partir do checkpoint
2. Continuar o treinamento por 50 épocas adicionais
3. Salvar os resultados em um novo diretório (por padrão)

### Opções de Linha de Comando

| Parâmetro | Descrição | Padrão |
|-----------|-------------|---------|
| `--checkpoint_path` | Caminho para o arquivo de checkpoint | |
| `--data_yaml` | Caminho para o arquivo data.yaml | `dataset/data.yaml` |
| `--epochs` | Épocas adicionais para treinar | `None` (usa as épocas originais) |
| `--batch_size` | Tamanho do batch para treinamento contínuo | `None` (usa o tamanho de batch original) |
| `--output_dir` | Diretório para salvar novos resultados | `runs/train` |

## Gerenciamento Avançado de Checkpoints

### Usando a API Python

Para mais controle, você pode usar a classe `YOLOTrainer` diretamente em Python:

```python
from microdetect.training.train import YOLOTrainer

# Retomar treinamento com parâmetros personalizados
trainer = YOLOTrainer(
    model_size="s",  # Isso não é usado ao retomar, mas ainda é necessário
    batch_size=16,   # Substituir o tamanho de batch original
    output_dir="runs/treinamento_retomado"
)

# Retomar treinamento com 50 épocas adicionais
results = trainer.resume_training(
    checkpoint_path="runs/train/yolov8_s_custom/weights/last.pt",
    data_yaml="dataset/data.yaml",
    additional_epochs=50
)

print(f"Treinamento retomado e concluído. Melhor mAP: {results.best_map}")
```

### Estratégias de Frequência de Checkpoint

Diferentes estratégias de salvamento de checkpoint são adequadas para diferentes cenários:

#### Para Execuções Longas de Treinamento
```bash
microdetect train --dataset_dir dataset --model_size l --epochs 300 --save_period 10
```
Salve a cada 10 épocas para acompanhar o progresso sem uso excessivo de disco.

#### Para Execuções de Fine-tuning
```bash
microdetect train --dataset_dir dataset --model_size s --epochs 20 --save_period 1
```
Salve a cada época para capturar pequenas melhorias durante o fine-tuning.

#### Para Ambientes Voláteis
```bash
microdetect train --dataset_dir dataset --model_size m --epochs 100 --save_period 5
```
Checkpoints mais frequentes reduzem a potencial perda de dados em ambientes de computação instáveis.

## Análise e Gerenciamento de Checkpoints

### Comparando Checkpoints

Você pode avaliar e comparar múltiplos checkpoints:

```bash
microdetect compare_checkpoints --checkpoints runs/train/exp1/weights/epoch_10.pt,runs/train/exp1/weights/epoch_20.pt,runs/train/exp1/weights/best.pt --data_yaml dataset/data.yaml
```

Isso gera um relatório de comparação mostrando métricas para cada checkpoint.

### Gerenciamento do Ciclo de Vida de Checkpoints

Para projetos de longo prazo com muitas execuções de treinamento:

```bash
microdetect manage_checkpoints --base_dir runs/train --keep best,last,epoch_50,epoch_100
```

Isso limpa checkpoints desnecessários, mantendo apenas os especificados para economizar espaço em disco.

### Criando Ensembles de Checkpoints

Combine múltiplos checkpoints para um desempenho potencialmente melhor:

```bash
microdetect create_ensemble --checkpoints runs/train/exp1/weights/best.pt,runs/train/exp2/weights/best.pt,runs/train/exp3/weights/best.pt --output ensemble.pt
```

## Cenários Especiais de Treinamento

### Treinamento Parcialmente Congelado

Retome o treinamento com certas camadas congeladas:

```bash
microdetect resume --checkpoint_path runs/train/exp1/weights/best.pt --freeze 10
```

Isso congela as primeiras 10 camadas do backbone, útil para fine-tuning.

### Ajuste de Taxa de Aprendizado

Retome com uma taxa de aprendizado diferente:

```bash
microdetect resume --checkpoint_path runs/train/exp1/weights/best.pt --lr0 0.001
```

Isso é útil ao fazer fine-tuning ou quando a taxa de aprendizado no checkpoint está muito alta/baixa.

### Treinamento Consolidado

Para múltiplas sessões curtas de treinamento:

```bash
# Primeira sessão de treinamento
microdetect train --dataset_dir dataset --model_size s --epochs 50

# Retome com dados adicionais
microdetect resume --checkpoint_path runs/train/exp1/weights/best.pt --data_yaml novo_dataset/data.yaml --epochs 50
```

Isso permite treinamento incremental à medida que novos dados ficam disponíveis.

## Melhores Práticas

### Frequência de Checkpoint

- Para modelos que levam >1 hora para treinar: Salve a cada 5-10 épocas
- Para experimentos rápidos (<30 min): Salve a cada época
- Sempre mantenha os checkpoints best e last

### Gerenciamento de Armazenamento

- Checkpoints regulares podem consumir espaço significativo em disco
- Use `manage_checkpoints` para limpar arquivos desnecessários
- Considere arquivar checkpoints importantes em armazenamento externo

### Convenções de Nomenclatura

Adote uma convenção clara de nomenclatura:

```bash
microdetect train --dataset_dir dataset --model_size s --name "yolov8s_microalga_v1"
```

Isso cria checkpoints com nomes significativos que indicam o tamanho do modelo e o dataset.

### Documentação

Mantenha anotações sobre execuções de treinamento e checkpoints:

```bash
microdetect log_experiment --checkpoint_path runs/train/exp1/weights/best.pt --notes "Aumentada augmentação, foco em objetos pequenos" --metrics "mAP50=0.876, precision=0.92"
```

## Solução de Problemas

### Problemas Comuns

| Problema | Solução |
|----------|---------|
| Não é possível retomar o treinamento (incompatibilidade de versão) | Garanta que a mesma versão do YOLOv8/MicroDetect foi usada |
| Baixo desempenho após retomar | Verifique se a taxa de aprendizado foi redefinida corretamente |
| Problemas de espaço em disco com muitos checkpoints | Use `manage_checkpoints` para limpar checkpoints antigos |
| Arquivo de checkpoint corrompido | Sempre mantenha múltiplos checkpoints (best, last, periódicos) |

## Próximos Passos

Após dominar o gerenciamento de checkpoints:

- [Guia de Otimização de Hiperparâmetros](hyperparameter_optimization.md) - Ajuste fino do desempenho do seu modelo
- [Guia de Avaliação de Modelos](model_evaluation_analysis.md) - Avalie seu modelo treinado
- [Guia de Implantação de Modelos](model_deployment.md) - Implante seu modelo para inferência