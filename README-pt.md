# Projeto de Detecção de Microrganismos

Este projeto fornece um pipeline completo para detecção e classificação de microrganismos (leveduras, fungos e micro-algas) utilizando YOLOv8. As ferramentas incluem anotação de imagens, aumento de dados, treinamento e funcionalidades de avaliação.

**Idiomas da Documentação:**
- [Inglês/English](README.md)
- [Português](README-pt.md) (atual)

## Funcionalidades

- Ferramenta de anotação manual para criar caixas delimitadoras
- Aumento de dados para expandir seu conjunto de treinamento
- Conversão de imagens TIFF para PNG
- Visualização e validação de anotações
- Pipeline de treinamento com YOLOv8
- Avaliação de modelos com métricas detalhadas e relatórios
- Suporte para múltiplos sistemas operacionais

## Requisitos

- Python 3.8+
- OpenCV
- PyTorch
- Ultralytics YOLOv8
- NumPy
- Pillow
- YAML
- TensorBoard (para visualização do treinamento)
- GPU compatível com CUDA (recomendado para treinamento)

## Instalação

### Windows

```bash
# Clone o repositório
git clone https://github.com/seuusuario/microorganism-detection.git
cd microorganism-detection

# Crie e ative o ambiente conda
make setup-win
conda activate yeast_detection

# Instale as dependências
make install
```

### macOS/Linux

```bash
# Clone o repositório
git clone https://github.com/seuusuario/microorganism-detection.git
cd microorganism-detection

# Crie e ative o ambiente conda
make setup
conda activate yeast_detection

# Instale as dependências
make install
```

### Instalação Manual (Qualquer SO)

```bash
# Crie o ambiente conda
conda create -n yeast_detection python=3.12 -y
conda activate yeast_detection

# Instale as dependências
pip install ultralytics opencv-python-headless numpy pillow pyyaml tqdm
pip install torch torchvision
```

## Estrutura do Projeto

```
microorganism-detection/
├── data/
│   ├── images/         # Imagens brutas para anotação
│   └── labels/         # Arquivos de anotação no formato YOLO
├── dataset/            # Dataset processado com divisões train/val/test
├── scripts/            # Scripts auxiliares
├── runs/               # Resultados do treinamento e modelos
├── reports/            # Relatórios de avaliação e métricas
├── bounding_boxes.py   # Ferramenta de visualização
├── convert_tiff.py     # Utilitário de conversão TIFF
├── main.py             # Ferramenta de anotação
├── training_model.py   # Script de treinamento e avaliação
└── makefile            # Comandos de automação
```

## Uso

### Configuração de Diretórios

Crie os diretórios necessários para seu projeto:

```bash
make create-dirs
```

### Conversão de Imagens TIFF para PNG

Se suas imagens estão em formato TIFF, converta-as para PNG:

```bash
make convert-tiff
# ou manualmente:
python convert_tiff.py --input_dir data/images --output_dir data/images --use_opencv --delete_original
```

### Anotação de Imagens

Inicie a ferramenta de anotação para criar caixas delimitadoras:

```bash
make annotate
# ou manualmente:
python main.py annotate --image_dir data/images --output_dir data/labels
```

Instruções:
- Clique e arraste para criar caixas delimitadoras
- Use o menu suspenso de classe para selecionar o tipo de microrganismo
- 'r' para resetar, 'd' para deletar última caixa, 's' para salvar, 'q' para sair

### Visualização de Anotações

Verifique suas anotações visualmente:

```bash
make visualize
# ou manualmente:
python bounding_boxes.py --image_dir data/images --label_dir data/labels
```

Navegação:
- 'n' para próxima imagem, 'p' para imagem anterior
- '0', '1', '2' para alternar visibilidade das classes
- 'a' para mostrar todas as classes, 'q' para sair

### Preparação do Dataset

Divida seus dados anotados em conjuntos de treinamento, validação e teste:

```bash
make prepare-data
# ou manualmente:
python training_model.py --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset
```

### Aumento de Dados

Aumente seus dados de treinamento para melhorar o desempenho do modelo:

```bash
make augment
# ou manualmente:
python training_model.py --dataset_dir dataset --augment --augment_factor 20
```

### Treinar o Modelo

Treine o modelo YOLOv8 em seu dataset:

```bash
make train
# ou com aumentação:
make train-augmented
# ou manualmente:
python training_model.py --dataset_dir dataset --model_size s --epochs 50 --batch_size 32 --train
```

Opções de tamanho do modelo:
- `n`: nano (menor, mais rápido)
- `s`: small (pequeno)
- `m`: medium (médio)
- `l`: large (grande)
- `x`: xlarge (extra grande, mais preciso)

### Avaliar o Modelo

Gere métricas de avaliação e relatórios:

```bash
make evaluate
# ou manualmente:
python training_model.py --evaluate --model_path runs/train/yolov8_s_custom/weights/best.pt --dataset_dir dataset
```

## Problemas Comuns e Soluções

### Compatibilidade PyTorch/Torchvision
Se você encontrar problemas de compatibilidade:
```bash
make fix-torch
# ou
make update-torch
```

### Aceleração GPU
- O script seleciona automaticamente o melhor dispositivo disponível (GPU CUDA, Apple Metal ou CPU)
- Para desempenho ideal de treinamento, use uma GPU NVIDIA compatível com CUDA

### Problemas de Memória
Se você encontrar erros de memória insuficiente CUDA:
- Reduza o tamanho do lote: `--batch_size 8` ou menor
- Use um modelo menor: `--model_size s` ou `--model_size n`
- Reduza o tamanho da imagem: `--image_size 416`

## Exemplo de Fluxo de Trabalho Completo

```bash
# 1. Configuração do ambiente
make setup
conda activate yeast_detection
make install

# 2. Conversão de imagens TIFF (se necessário)
make convert-tiff

# 3. Anotação de imagens
make annotate

# 4. Visualização de anotações
make visualize

# 5. Preparação do dataset
make prepare-data

# 6. Aumento dos dados de treinamento
make augment

# 7. Treinamento do modelo
make train-augmented

# 8. Avaliação do modelo
make evaluate
```

## Licença

Este projeto está licenciado sob [Licença Proprietária](LICENSE) - consulte o arquivo LICENSE para detalhes.