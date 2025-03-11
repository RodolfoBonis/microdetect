#!/bin/bash
# Script robusto para instalação do MicroDetect em ambiente de produção

set -e  # Parar em caso de erro

echo "=== Instalando MicroDetect para Producao ==="

# Detectar o caminho do pip Python
if command -v pip3 > /dev/null 2>&1; then
    PIP_CMD="pip3"
elif command -v pip > /dev/null 2>&1; then
    PIP_CMD="pip"
else
    echo "Erro: pip não encontrado. Por favor instale pip."
    exit 1
fi

# Detectar o caminho do Python
if command -v python3 > /dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python > /dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "Erro: Python não encontrado. Por favor instale Python 3."
    exit 1
fi

echo "Usando pip: $PIP_CMD"
echo "Usando Python: $PYTHON_CMD"

# Verificar versão do Python
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo "Erro: É necessário Python 3.9 ou superior. Versão detectada: $PYTHON_VERSION"
    exit 1
fi

echo "Python $PYTHON_VERSION detectado."

# Criar ambiente virtual se solicitado
USE_VENV=0
CREATE_EXAMPLE=0

for arg in "$@"; do
    case $arg in
        --virtual-env)
            USE_VENV=1
            ;;
        --with-example)
            CREATE_EXAMPLE=1
            ;;
    esac
done

if [ $USE_VENV -eq 1 ]; then
    echo "Criando ambiente virtual..."
    $PYTHON_CMD -m venv venv

    # Ativar ambiente virtual (compatível com diferentes shells)
    if [ -f "venv/bin/activate" ]; then
        . venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        . venv/Scripts/activate
    else
        echo "Erro: Não foi possível encontrar o script de ativação do ambiente virtual."
        exit 1
    fi

    # Atualizar variáveis após ativação
    if command -v pip > /dev/null 2>&1; then
        PIP_CMD="pip"
    fi
    if command -v python > /dev/null 2>&1; then
        PYTHON_CMD="python"
    fi

    echo "Ambiente virtual ativado."
fi

# Instalar dependências
echo "Instalando dependências..."
$PIP_CMD install --upgrade pip
$PIP_CMD install wheel

# Instalar PyTorch com suporte a hardware apropriado
echo "Detectando hardware para instalação otimizada de PyTorch..."

# Função simples para detecção de GPU NVIDIA
detect_nvidia_gpu() {
    # Verificar nvidia-smi
    if command -v nvidia-smi > /dev/null 2>&1; then
        echo "GPU NVIDIA detectada via nvidia-smi."
        return 0
    fi

    # Verificar diretório CUDA
    if [ -d "/usr/local/cuda" ]; then
        echo "Diretório CUDA encontrado."
        return 0
    fi

    # Verificar bibliotecas CUDA
    if [ -f "/usr/lib/x86_64-linux-gnu/libcuda.so" ] || [ -f "/usr/lib/libcuda.so" ]; then
        echo "Bibliotecas CUDA encontradas."
        return 0
    fi

    return 1
}

# Determinar o sistema e instalar PyTorch apropriadamente
IS_MACOS=0
IS_APPLE_SILICON=0

if [ "$(uname)" = "Darwin" ]; then
    IS_MACOS=1
    if [ "$(uname -m)" = "arm64" ]; then
        IS_APPLE_SILICON=1
    fi
fi

if [ $IS_MACOS -eq 1 ]; then
    if [ $IS_APPLE_SILICON -eq 1 ]; then
        echo "Detectado Apple Silicon. Instalando PyTorch para MPS..."
        $PIP_CMD install torch==2.6.0 torchvision==0.21.0
    else
        echo "Detectado macOS Intel. Instalando PyTorch..."
        $PIP_CMD install torch torchvision
    fi
else
    # Linux/WSL
    if detect_nvidia_gpu; then
        echo "CUDA detectado. Instalando PyTorch com suporte a CUDA..."
        $PIP_CMD install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
    else
        echo "GPU NVIDIA não detectada. Instalando PyTorch CPU..."
        $PIP_CMD install torch torchvision
    fi
fi

# Instalar optree para inferência mais rápida
echo "Instalando optree para inferência mais rápida..."
$PIP_CMD install --upgrade 'optree>=0.13.0'

# Instalar Ultralytics (YOLOv8)
echo "Instalando Ultralytics YOLOv8..."
$PIP_CMD install ultralytics

# Instalar o pacote MicroDetect
echo "Instalando MicroDetect..."
$PIP_CMD install -e .

# Verificar instalação
echo "Verificando instalação..."
if $PYTHON_CMD -c "import microdetect; print(f'MicroDetect importado com sucesso!')" &> /dev/null; then
    echo "MicroDetect instalado com sucesso!"
else
    echo "Erro: Falha na instalação do MicroDetect."
    exit 1
fi

# Verificar PyTorch e CUDA
echo "Verificando PyTorch e CUDA:"
$PYTHON_CMD -c "import torch; print(f'PyTorch versão: {torch.__version__}'); print(f'CUDA disponível: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"Nenhuma GPU\"}')"

# Inicializar um projeto de exemplo
if [ $CREATE_EXAMPLE -eq 1 ]; then
    echo "Criando projeto de exemplo..."
    mkdir -p microdetect_example
    cd microdetect_example
    microdetect init
    echo "Projeto de exemplo criado em: $(pwd)"
fi

echo ""
echo "=== Instalação concluída! ==="
echo ""
echo "Para iniciar um projeto MicroDetect:"
echo "1. Crie um diretório para seu projeto: mkdir meu_projeto"
echo "2. Entre no diretório: cd meu_projeto"
echo "3. Inicialize o projeto: microdetect init"
echo "4. Siga as instruções para começar a usar o MicroDetect"
echo ""
echo "Obrigado por usar MicroDetect!"