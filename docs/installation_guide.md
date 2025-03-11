# Guia de Instalação do MicroDetect

Este guia fornece instruções detalhadas para instalar o MicroDetect em diferentes sistemas operacionais e ambientes.

## Requisitos do Sistema

### Requisitos Mínimos

- Python 3.9 ou superior
- 4GB de RAM (8GB recomendado para treinamento)
- 2GB de espaço em disco

### Dependências Principais

- PyTorch (1.7+)
- OpenCV
- Ultralytics YOLOv8
- NumPy, Matplotlib, PIL
- AWS CLI (para atualizações automáticas)

## Instalação em Linux/macOS

### Opção 1: Usando o Script de Instalação (Recomendado)

O método mais simples é usar o script de instalação fornecido:

```bash
# Clone o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Tornar o script executável
chmod +x scripts/install_production.sh

# Instalar com o script (com ambiente conda)
./scripts/install_production.sh

# OU para criar um ambiente virtual Python
./scripts/install_production.sh --virtual-env

# Para criar também um projeto de exemplo
./scripts/install_production.sh --with-example
```

### Opção 2: Instalação Manual com Ambiente Virtual

Se preferir mais controle sobre o processo de instalação:

```bash
# Clone o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Instalar o pacote em modo de desenvolvimento
pip install -e .

# Testar a instalação
python -c "import microdetect; print(f'MicroDetect versão {microdetect.__version__} instalado com sucesso!')"
```

### Opção 3: Instalação com Conda (para GPU)

Para usar aceleração GPU (recomendado para treinamento):

```bash
# Clone o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Criar ambiente conda
conda create -n microdetect python=3.10
conda activate microdetect

# Instalar PyTorch com suporte a CUDA
conda install pytorch torchvision pytorch-cuda=11.8 -c pytorch -c nvidia

# Instalar outras dependências
pip install -r requirements.txt

# Instalar o pacote
pip install -e .
```

## Instalação no Windows

### Opção 1: Usando o Script Batch (Recomendado)

```batch
# Clone o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Instalar com o script (com ambiente conda)
scripts\install_production.bat

# OU para criar um ambiente virtual Python
scripts\install_production.bat --virtual-env

# Para criar também um projeto de exemplo
scripts\install_production.bat --with-example
```

### Opção 2: Instalação Manual com Ambiente Virtual

```batch
# Clone o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Criar e ativar ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar o pacote em modo de desenvolvimento
pip install -e .

# Testar a instalação
python -c "import microdetect; print(f'MicroDetect versão {microdetect.__version__} instalado com sucesso!')"
```

### Opção 3: Instalação com Conda (para GPU)

```batch
# Clone o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Criar ambiente conda
conda create -n microdetect python=3.10
conda activate microdetect

# Instalar PyTorch com suporte a CUDA
conda install pytorch torchvision pytorch-cuda=11.8 -c pytorch -c nvidia

# Instalar outras dependências
pip install -r requirements.txt

# Instalar o pacote
pip install -e .
```

## Instalação em Apple Silicon (M1/M2/M3)

Para computadores Mac com chips Apple Silicon:

```bash
# Clone o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar PyTorch otimizado para MPS (GPU do Mac)
pip install torch==2.6.0 torchvision==0.21.0

# Instalar outras dependências
pip install -r requirements.txt

# Instalar o pacote
pip install -e .
```

## Instalação para Desenvolvimento

Se você planeja contribuir com o projeto:

```bash
# Clone o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows

# Instalar dependências (incluindo ferramentas de desenvolvimento)
pip install -r requirements.txt
pip install -r requirements-dev.txt  # ferramentas adicionais para desenvolvimento

# Instalar o pacote em modo editável
pip install -e .

# Configurar pre-commit hooks
pre-commit install
```

## Instalação via AWS CodeArtifact (Usuários Finais)

Para instalar o MicroDetect diretamente do AWS CodeArtifact:

```bash
# Configurar AWS CLI com suas credenciais
aws configure

# Obter token de autenticação
export CODEARTIFACT_AUTH_TOKEN=$(aws codeartifact get-authorization-token \
    --domain seu-dominio \
    --query authorizationToken \
    --output text)

# Obter URL do repositório
export CODEARTIFACT_REPOSITORY_URL=$(aws codeartifact get-repository-endpoint \
    --domain seu-dominio \
    --repository seu-repositorio \
    --format pypi \
    --query repositoryEndpoint \
    --output text)

# Instalar o MicroDetect
pip install microdetect \
    --index-url "${CODEARTIFACT_REPOSITORY_URL}simple/" \
    --extra-index-url https://pypi.org/simple
```

## Verificando a Instalação

Após a instalação, verifique se tudo está funcionando corretamente:

```bash
# Verificar a versão
microdetect --version

# Inicializar um projeto de exemplo
mkdir meu_projeto
cd meu_projeto
microdetect init
```

## Configuração do Sistema de Atualização

Após a instalação, configure o sistema de atualização automática:

```bash
# Configurar AWS CodeArtifact
microdetect setup-aws --domain seu-dominio --repository seu-repositorio --configure-aws

# Verificar se há atualizações
microdetect update --check-only
```

## Solução de Problemas de Instalação

### Problemas com PyTorch

Se encontrar problemas com o PyTorch:

```bash
# Desinstalar versão atual
pip uninstall torch torchvision

# Reinstalar a versão específica para seu hardware
# Para CUDA:
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118

# Para CPU:
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu

# Para Apple Silicon:
pip install torch==2.6.0 torchvision==0.21.0
```

### Problemas com OpenCV

Se encontrar problemas com o OpenCV:

```bash
# Desinstalar e reinstalar
pip uninstall opencv-python
pip install opencv-python-headless
```

### Problemas com CUDA

Se encontrar problemas com suporte a GPU:

```bash
# Verificar disponibilidade de CUDA
python -c "import torch; print(f'CUDA disponível: {torch.cuda.is_available()}')"

# Ver dispositivos disponíveis
python -c "import torch; print(f'Dispositivos CUDA: {torch.cuda.device_count()}')"

# Verificar versão do CUDA
python -c "import torch; print(f'Versão CUDA: {torch.version.cuda}')"
```

### Problemas com Credenciais AWS

Se encontrar problemas com AWS CodeArtifact:

```bash
# Verificar configuração AWS
aws configure list

# Testar acesso ao CodeArtifact
aws codeartifact get-repository \
    --domain seu-dominio \
    --repository seu-repositorio
```

## Desinstalação

Para desinstalar o MicroDetect:

```bash
# Desinstalar o pacote
pip uninstall microdetect

# Remover ambiente virtual (opcional)
# Linux/macOS
rm -rf venv

# Windows
rmdir /s /q venv

# Ou desativar e remover ambiente conda (opcional)
conda deactivate
conda env remove -n microdetect
```