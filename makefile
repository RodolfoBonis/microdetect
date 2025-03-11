# Makefile para Projeto MicroDetect

# Variáveis de configuração
CONDA_ENV_NAME = microdetect
PYTHON_VERSION = 3.12

# Diretórios principais
DATASET_DIR = dataset
SOURCE_IMG_DIR = data/images
SOURCE_LABEL_DIR = data/labels
OUTPUT_DIR = runs/train
REPORTS_DIR = reports

# Parâmetros de treinamento (podem ser sobrescritos com make VAR=valor)
MODEL_SIZE = s
EPOCHS = 100
BATCH_SIZE = 32
IMAGE_SIZE = 640
AUGMENT_FACTOR = 20

# Alvo padrão
all: help

# Configuração de ambiente
setup:
	@echo "Configurando ambiente..."
	@chmod +x scripts/setup.sh
	./scripts/setup.sh --create
	@echo "Agora ative o ambiente com: conda activate $(CONDA_ENV_NAME)"
	@echo "Em seguida execute: make install"

# Instalar dependências (após ativação do ambiente conda)
install:
	@echo "Instalando dependências..."
	@chmod +x scripts/setup.sh
	./scripts/setup.sh --install

# Configuração no Windows (alternativa ao alvo setup)
setup-win:
	@echo "Configurando ambiente no Windows..."
	scripts\setup.bat --create

install-win:
	@echo "Instalando dependências no Windows..."
	scripts\setup.bat --install

# Criar diretórios necessários
create-dirs:
	@echo "Criando diretórios necessários..."
	mkdir -p scripts $(DATASET_DIR) data/images data/labels $(OUTPUT_DIR) $(REPORTS_DIR)

# Converter imagens TIFF para PNG
convert-tiff:
	@echo "Convertendo imagens TIFF para PNG..."
	python -m microdetect convert --input_dir $(SOURCE_IMG_DIR) --output_dir $(SOURCE_IMG_DIR) --use_opencv --delete_original

# Ferramenta de anotação
annotate:
	@echo "Iniciando ferramenta de anotação..."
	python -m microdetect annotate --image_dir $(SOURCE_IMG_DIR) --output_dir $(SOURCE_LABEL_DIR)

# Visualizar anotações
visualize:
	@echo "Visualizando anotações..."
	python -m microdetect visualize --image_dir $(SOURCE_IMG_DIR) --label_dir $(SOURCE_LABEL_DIR)

# Preparar dataset (dividir em train/val/test)
prepare-data:
	@echo "Preparando dataset..."
	python -m microdetect dataset --source_img_dir $(SOURCE_IMG_DIR) --source_label_dir $(SOURCE_LABEL_DIR) --dataset_dir $(DATASET_DIR)

# Augmentação de dados
augment:
	@echo "Realizando augmentação de dados..."
	python -m microdetect augment --image_dir $(SOURCE_IMG_DIR) --label_dir $(SOURCE_LABEL_DIR) --factor $(AUGMENT_FACTOR)

# Treinar modelo YOLO
train:
	@echo "Treinando modelo YOLO..."
	python -m microdetect train --dataset_dir $(DATASET_DIR) --model_size $(MODEL_SIZE) \
		--epochs $(EPOCHS) --batch_size $(BATCH_SIZE) --image_size $(IMAGE_SIZE) \
		--output_dir $(OUTPUT_DIR)

# Treinar modelo YOLO com busca de hiperparâmetros
train-hyperparams:
	@echo "Treinando modelo YOLO com busca de hiperparâmetros..."
	python -m microdetect train --dataset_dir $(DATASET_DIR) --model_size $(MODEL_SIZE) \
		--find_hyperparams --output_dir $(OUTPUT_DIR)

# Avaliar modelo e gerar relatório
evaluate:
	@echo "Avaliando modelo e gerando relatório..."
	python -m microdetect evaluate --model_path $(OUTPUT_DIR)/yolov8_$(MODEL_SIZE)_custom/weights/best.pt \
		--dataset_dir $(DATASET_DIR) --output_dir $(REPORTS_DIR) --confusion_matrix

# Pipeline completa: desde a preparação até a avaliação
pipeline: prepare-data augment train evaluate
	@echo "Pipeline completa executada com sucesso!"

# Limpar dados gerados
clean:
	@echo "Limpando dados augmentados..."
	rm -rf $(DATASET_DIR)/train/images/*_aug*
	rm -rf $(DATASET_DIR)/train/labels/*_aug*

# Limpar tudo (exceto código fonte)
clean-all: clean
	@echo "Limpando todos os dados gerados..."
	rm -rf $(DATASET_DIR)/* $(OUTPUT_DIR)/* $(REPORTS_DIR)/*

# Atualizar dependências
update:
	@echo "Atualizando dependências..."
	./scripts/setup.sh --update

# Comando de ajuda
help:
	@echo "MicroDetect - Detecção de Microorganismos"
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  make setup          - Criar ambiente conda (Linux/Mac)"
	@echo "  make setup-win      - Criar ambiente conda (Windows)"
	@echo "  make install        - Instalar dependências (após ativar ambiente)"
	@echo "  make install-win    - Instalar dependências (Windows)"
	@echo "  make create-dirs    - Criar diretórios necessários"
	@echo "  make convert-tiff   - Converter imagens TIFF para PNG"
	@echo "  make annotate       - Iniciar ferramenta de anotação"
	@echo "  make visualize      - Visualizar anotações"
	@echo "  make prepare-data   - Preparar dataset (dividir em train/val/test)"
	@echo "  make augment        - Realizar augmentação de dados"
	@echo "  make train          - Treinar modelo YOLO"
	@echo "  make train-hyperparams - Treinar com busca de hiperparâmetros"
	@echo "  make evaluate       - Avaliar modelo e gerar relatório"
	@echo "  make pipeline       - Executar pipeline completa"
	@echo "  make clean          - Limpar dados augmentados"
	@echo "  make clean-all      - Limpar todos os dados gerados"
	@echo "  make update         - Atualizar dependências"
	@echo ""
	@echo "Configuração (sobrescreva com make VAR=valor):"
	@echo "  SOURCE_IMG_DIR = $(SOURCE_IMG_DIR)"
	@echo "  SOURCE_LABEL_DIR = $(SOURCE_LABEL_DIR)"
	@echo "  MODEL_SIZE = $(MODEL_SIZE) (opções: n, s, m, l, x)"
	@echo "  EPOCHS = $(EPOCHS)"
	@echo "  BATCH_SIZE = $(BATCH_SIZE)"
	@echo "  AUGMENT_FACTOR = $(AUGMENT_FACTOR)"

.PHONY: all setup install setup-win install-win create-dirs convert-tiff annotate visualize prepare-data augment train train-hyperparams evaluate pipeline clean clean-all update help