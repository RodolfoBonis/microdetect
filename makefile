# Makefile para Projeto MicroDetect

#==============================================================================
# VARIÁVEIS DE CONFIGURAÇÃO
#==============================================================================
# Ambiente
CONDA_ENV_NAME = microdetect
PYTHON_VERSION = 3.12

# Diretórios principais
DATASET_DIR = dataset
SOURCE_IMG_DIR = data/images
SOURCE_LABEL_DIR = data/labels
OUTPUT_DIR = runs/train
REPORTS_DIR = reports

# Parâmetros de treinamento (podem ser sobrescritos com make VAR=valor)
MODEL_SIZE = m
EPOCHS = 100
BATCH_SIZE = 32
IMAGE_SIZE = 640
AUGMENT_FACTOR = 20

# Parâmetros para AWS CodeArtifact
DOMAIN = seu-dominio
REPOSITORY = seu-repositorio
DOMAIN_OWNER =
REGION = us-east-1

# Parâmetros para testes
PYTEST_ARGS ?=
FILE ?= tests

#==============================================================================
# CONFIGURAÇÃO DE AMBIENTE
#==============================================================================
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

# Atualizar dependências
update-deps:
	@echo "Atualizando dependências..."
	./scripts/setup.sh --update

#==============================================================================
# COMANDOS DE PROCESSAMENTO DE DADOS
#==============================================================================
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

#==============================================================================
# COMANDOS DE TREINAMENTO E AVALIAÇÃO
#==============================================================================
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

#==============================================================================
# COMANDOS DE TESTES
#==============================================================================
# Preparar ambiente para testes (única versão, removida duplicata)
test-setup:
	@echo "Preparando ambiente para testes..."
	pip install pytest pytest-cov pytest-timeout mock
	mkdir -p tests/fixtures/images tests/fixtures/labels
	@echo "Ambiente de testes preparado!"

# Executar todos os testes sem cobertura (corrigido)
test:
	@echo "Executando todos os testes..."
	python -m pytest -v $(PYTEST_ARGS) tests

# Executar testes com relatório de cobertura HTML
test-cov:
	@echo "Executando testes com cobertura HTML..."
	python -m pytest --cov=microdetect --cov-report=html $(PYTEST_ARGS) tests
	@echo "Relatório de cobertura gerado em htmlcov/index.html"

# Executar testes com cobertura terminal
test-term:
	@echo "Executando testes com cobertura no terminal..."
	python -m pytest --cov=microdetect --cov-report=term $(PYTEST_ARGS) tests

# Executar testes com cobertura XML (para CI)
test-xml:
	@echo "Executando testes com cobertura XML..."
	python -m pytest --cov=microdetect --cov-report=xml $(PYTEST_ARGS) tests
	@echo "Relatório XML gerado em coverage.xml"

# Executar um teste específico
test-file:
	@echo "Executando teste específico: $(FILE)"
	python -m pytest -v $(FILE)

# Executar testes com verbosidade
test-verbose:
	@echo "Executando testes com saída detalhada..."
	python -m pytest -vv --no-header --no-summary -s tests

# Executar verificação de estilo e linting
test-lint:
	@echo "Verificando estilo de código..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check microdetect tests
	isort --check-only --profile black microdetect tests

# Limpar arquivos temporários de testes
test-clean:
	@echo "Limpando arquivos temporários de testes..."
	rm -rf .pytest_cache htmlcov .coverage coverage.xml

# Executar testes e gerar relatório de falhas em caso de erro
test-report:
	@echo "Executando testes com relatório detalhado de falhas..."
	python -m pytest -v --showlocals tests || (echo "⚠️ TESTES FALHARAM - Veja o relatório acima para detalhes")

# Ver pacotes instalados relacionados a testes
test-info:
	@echo "Pacotes pytest instalados:"
	@pip list | grep pytest
	@echo "\nConfigurações em pytest.ini:"
	@if [ -f pytest.ini ]; then cat pytest.ini; else echo "Arquivo pytest.ini não encontrado"; fi

# Executar todos os testes com PYTHONPATH definido
test-clean-run:
	@echo "Executando testes em ambiente limpo..."
	PYTHONPATH=. python -m pytest -v tests

# Teste mais simples possível
test-simple:
	@echo "Executando teste simples..."
	pytest tests

# Renomear temporariamente pytest.ini e executar testes
test-without-ini:
	@echo "Executando testes sem o arquivo pytest.ini..."
	@if [ -f pytest.ini ]; then mv pytest.ini pytest.ini.bak; fi
	pytest $(PYTEST_ARGS) tests
	@if [ -f pytest.ini.bak ]; then mv pytest.ini.bak pytest.ini; fi

# Executar testes sem mostrar warnings
test-no-warnings:
	@echo "Executando testes sem exibir warnings..."
	python -m pytest -p no:warnings -v tests

#==============================================================================
# COMANDOS DE MANUTENÇÃO E UTILITÁRIOS
#==============================================================================
# Iniciar servidor de documentação
docs:
	@echo "Iniciando servidor de documentação web..."
	python -m microdetect docs

# Configurar AWS CodeArtifact para atualizações
setup-aws:
	@echo "Configurando AWS CodeArtifact para atualizações..."
	python -m microdetect setup-aws --domain $(DOMAIN) --repository $(REPOSITORY) \
		$(if $(DOMAIN_OWNER),--domain-owner $(DOMAIN_OWNER),) \
		$(if $(REGION),--region $(REGION),) \
		--configure-aws --test

# Verificar se há atualizações
check-update:
	@echo "Verificando se há atualizações..."
	python -m microdetect update --check-only

# Atualizar aplicação
update:
	@echo "Atualizando aplicação..."
	python -m microdetect update

# Limpar dados gerados
clean:
	@echo "Limpando dados augmentados..."
	rm -rf $(DATASET_DIR)/train/images/*_aug*
	rm -rf $(DATASET_DIR)/train/labels/*_aug*

# Limpar tudo (exceto código fonte)
clean-all: clean
	@echo "Limpando todos os dados gerados..."
	rm -rf $(DATASET_DIR)/* $(OUTPUT_DIR)/* $(REPORTS_DIR)/*

# Comando de ajuda
help:
	@echo "MicroDetect - Detecção de Microorganismos"
	@echo ""
	@echo "=== CONFIGURAÇÃO DE AMBIENTE ==="
	@echo "  make setup          - Criar ambiente conda (Linux/Mac)"
	@echo "  make setup-win      - Criar ambiente conda (Windows)"
	@echo "  make install        - Instalar dependências (após ativar ambiente)"
	@echo "  make install-win    - Instalar dependências (Windows)"
	@echo "  make create-dirs    - Criar diretórios necessários"
	@echo "  make update-deps    - Atualizar dependências"
	@echo ""
	@echo "=== PROCESSAMENTO DE DADOS ==="
	@echo "  make convert-tiff   - Converter imagens TIFF para PNG"
	@echo "  make annotate       - Iniciar ferramenta de anotação"
	@echo "  make visualize      - Visualizar anotações"
	@echo "  make prepare-data   - Preparar dataset (dividir em train/val/test)"
	@echo "  make augment        - Realizar augmentação de dados"
	@echo ""
	@echo "=== TREINAMENTO E AVALIAÇÃO ==="
	@echo "  make train          - Treinar modelo YOLO"
	@echo "  make train-hyperparams - Treinar com busca de hiperparâmetros"
	@echo "  make evaluate       - Avaliar modelo e gerar relatório"
	@echo "  make pipeline       - Executar pipeline completa"
	@echo ""
	@echo "=== TESTES ==="
	@echo "  make test-setup     - Preparar ambiente para testes"
	@echo "  make test           - Executar todos os testes"
	@echo "  make test-cov       - Executar testes com relatório de cobertura"
	@echo "  make test-file      - Executar teste específico (ex: make test-file FILE=tests/test_example.py)"
	@echo "  make test-verbose   - Executar testes com saída detalhada"
	@echo "  make test-lint      - Verificar estilo de código"
	@echo "  make test-clean     - Limpar arquivos temporários de testes"
	@echo "  make test-no-warnings - Executar testes sem exibir warnings"
	@echo "  make test-without-ini - Executar testes sem pytest.ini"
	@echo ""
	@echo "=== MANUTENÇÃO E UTILITÁRIOS ==="
	@echo "  make docs           - Iniciar servidor de documentação web"
	@echo "  make setup-aws      - Configurar AWS CodeArtifact para atualizações"
	@echo "  make check-update   - Verificar se há atualizações disponíveis"
	@echo "  make update         - Atualizar aplicação para a versão mais recente"
	@echo "  make clean          - Limpar dados augmentados"
	@echo "  make clean-all      - Limpar todos os dados gerados"
	@echo ""
	@echo "Configuração (sobrescreva com make VAR=valor):"
	@echo "  SOURCE_IMG_DIR = $(SOURCE_IMG_DIR)"
	@echo "  SOURCE_LABEL_DIR = $(SOURCE_LABEL_DIR)"
	@echo "  MODEL_SIZE = $(MODEL_SIZE) (opções: n, s, m, l, x)"
	@echo "  EPOCHS = $(EPOCHS)"
	@echo "  BATCH_SIZE = $(BATCH_SIZE)"
	@echo "  AUGMENT_FACTOR = $(AUGMENT_FACTOR)"
	@echo "  DOMAIN = $(DOMAIN) (para AWS CodeArtifact)"
	@echo "  REPOSITORY = $(REPOSITORY) (para AWS CodeArtifact)"
	@echo "  REGION = $(REGION) (região AWS)"
	@echo "  PYTEST_ARGS = argumentos adicionais para pytest (ex: make test PYTEST_ARGS='-xvs')"

.PHONY: all setup install setup-win install-win create-dirs convert-tiff annotate visualize prepare-data augment train train-hyperparams evaluate setup-aws check-update update pipeline clean clean-all update-deps help docs test-setup test test-cov test-file test-verbose test-lint test-clean test-report test-info test-clean-run test-simple test-without-ini test-no-warnings