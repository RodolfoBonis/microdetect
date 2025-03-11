#!/bin/bash
# Script para configuração do ambiente MicroDetect

set -e

CONDA_ENV_NAME="yeast_detection"
PYTHON_VERSION="3.12"

show_help() {
    echo "Uso: $0 [opções]"
    echo ""
    echo "Opções:"
    echo "  --create         Criar novo ambiente conda"
    echo "  --install        Instalar dependências no ambiente atual"
    echo "  --update         Atualizar dependências no ambiente atual"
    echo "  --env NAME       Nome do ambiente conda (padrão: yeast_detection)"
    echo "  --python VERSION Versão do Python (padrão: 3.12)"
    echo "  --help           Mostrar esta ajuda"
    echo ""
}

# Função para detectar plataforma
detect_platform() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Verificar se é Mac M1/M2/M3
        if [[ $(uname -m) == "arm64" ]]; then
            echo "mac_arm"
        else
            echo "mac_intel"
        fi
    elif [[ $(grep -i microsoft /proc/version 2>/dev/null) ]]; then
        echo "wsl"
    else
        echo "linux"
    fi
}

create_env() {
    echo "Criando ambiente conda $CONDA_ENV_NAME com Python $PYTHON_VERSION..."
    conda create -y -n $CONDA_ENV_NAME python=$PYTHON_VERSION
    echo "Ambiente criado. Ative-o com: conda activate $CONDA_ENV_NAME"
}

install_dependencies() {
    echo "Instalando dependências..."

    # Verificar se estamos em um ambiente conda
    if [ -z "$CONDA_PREFIX" ]; then
        echo "ERRO: Nenhum ambiente conda ativo. Ative um ambiente conda primeiro."
        exit 1
    fi

    PLATFORM=$(detect_platform)
    echo "Plataforma detectada: $PLATFORM"

    # Instalar dependências comuns
    echo "Instalando dependências comuns..."
    pip install numpy opencv-python PyYAML matplotlib pillow tqdm

    # Instalar PyTorch com versão apropriada para o ambiente
    if [[ "$PLATFORM" == "mac_arm" ]]; then
        echo "Instalando PyTorch para Mac M1/M2/M3..."
        pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu

        # Verificar disponibilidade de MPS
        python -c "import torch; print(f'PyTorch version: {torch.__version__}'); \
                  print(f'MPS available: {torch.backends.mps.is_available()}')"

    elif [[ "$PLATFORM" == "mac_intel" ]]; then
        echo "Instalando PyTorch para Mac Intel..."
        conda install pytorch torchvision -c pytorch -y

    elif [[ "$PLATFORM" == "wsl" || "$PLATFORM" == "linux" ]]; then
        echo "Instalando PyTorch com suporte a CUDA para Linux/WSL..."
        conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia -y

        # Verificar disponibilidade de CUDA
        python -c "import torch; print(f'PyTorch version: {torch.__version__}'); \
                  print(f'CUDA available: {torch.cuda.is_available()}')"
    else
        echo "Plataforma não reconhecida, instalando PyTorch para CPU..."
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    fi

    # Instalar optree atualizado para inferência mais rápida
    echo "Instalando optree para inferência mais rápida..."
    pip install --upgrade 'optree>=0.13.0'

    # Instalar Ultralytics (YOLOv8)
    echo "Instalando Ultralytics YOLOv8..."
    pip install ultralytics

    # Instalar outras dependências do projeto
    if [ -f "requirements.txt" ]; then
        echo "Instalando dependências do requirements.txt..."
        pip install -r requirements.txt
    fi

    # Instalar o próprio pacote em modo desenvolvimento
    echo "Instalando o pacote em modo desenvolvimento..."
    pip install -e .

    echo "Instalação concluída!"
}

update_dependencies() {
    echo "Atualizando dependências..."
    pip install -U numpy opencv-python PyYAML matplotlib pillow tqdm ultralytics
    pip install --upgrade 'optree>=0.13.0'

    if [ -f "requirements.txt" ]; then
        pip install -U -r requirements.txt
    fi

    echo "Atualização concluída!"
}

# Processar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --create)
            CREATE_ENV=1
            shift
            ;;
        --install)
            INSTALL_DEPS=1
            shift
            ;;
        --update)
            UPDATE_DEPS=1
            shift
            ;;
        --env)
            CONDA_ENV_NAME="$2"
            shift 2
            ;;
        --python)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Opção desconhecida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Executar ações solicitadas
if [ ! -z "$CREATE_ENV" ]; then
    create_env
fi

if [ ! -z "$INSTALL_DEPS" ]; then
    install_dependencies
fi

if [ ! -z "$UPDATE_DEPS" ]; then
    update_dependencies
fi

# Se nenhuma ação foi especificada, mostrar ajuda
if [ -z "$CREATE_ENV" ] && [ -z "$INSTALL_DEPS" ] && [ -z "$UPDATE_DEPS" ]; then
    show_help
fi