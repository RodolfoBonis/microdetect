# Guia de Instalação

Este guia fornece instruções detalhadas passo a passo para instalar o MicroDetect em diferentes sistemas operacionais e ambientes.

## Índice
- [Requisitos do Sistema](#requisitos-do-sistema)
- [Métodos de Instalação](#métodos-de-instalação)
  - [Scripts de Instalação Rápida](#scripts-de-instalação-rápida)
  - [Instalação Manual](#instalação-manual)
- [Instalação Específica para Plataformas](#instalação-específica-para-plataformas)
  - [Linux/macOS](#linuxmacos)
  - [Windows](#windows)
  - [Apple Silicon (M1/M2/M3)](#apple-silicon-m1m2m3)
- [Instalação para Desenvolvimento](#instalação-para-desenvolvimento)
- [Instalação via AWS CodeArtifact](#instalação-via-aws-codeartifact)
- [Verificando sua Instalação](#verificando-sua-instalação)
- [Configurar Sistema de Atualização](#configurar-sistema-de-atualização)
- [Solução de Problemas](#solução-de-problemas)
- [Desinstalação](#desinstalação)

## Requisitos do Sistema

### Requisitos Mínimos
- **Python**: 3.9 ou superior
- **RAM**: 4GB (8GB recomendado para treinamento)
- **Espaço em Disco**: 2GB para instalação e uso básico
- **CUDA** (opcional): Para aceleração via GPU em hardware NVIDIA

### Dependências Principais
- PyTorch (1.7+)
- OpenCV
- Ultralytics YOLOv8
- NumPy, Matplotlib, Pillow
- AWS CLI (para atualizações automáticas)

## Métodos de Instalação

### Scripts de Instalação Rápida

Para uma experiência de instalação simplificada, fornecemos scripts de instalação prontos para uso.

#### Linux/macOS
```bash
# Clonar o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Tornar o script executável
chmod +x scripts/install_production.sh

# Instalar usando o script
./scripts/install_production.sh

# Para criar um ambiente virtual durante a instalação
./scripts/install_production.sh --virtual-env

# Para criar um projeto de exemplo após a instalação
./scripts/install_production.sh --with-example
```

#### Windows
```batch
# Clonar o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Instalar usando o script
scripts\install_production.bat

# Para criar um ambiente virtual durante a instalação
scripts\install_production.bat --virtual-env

# Para criar um projeto de exemplo após a instalação
scripts\install_production.bat --with-example
```

### Instalação Manual

Se você preferir ter mais controle sobre o processo de instalação, pode instalar o MicroDetect manualmente.

#### Usando Ambiente Virtual
```bash
# Clonar o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Criar e ativar um ambiente virtual
python -m venv venv
source venv/bin/activate  # No Linux/macOS
# Ou no Windows:
# venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar o pacote em modo de desenvolvimento
pip install -e .

# Testar a instalação
python -c "import microdetect; print(f'MicroDetect versão {microdetect.__version__} instalado com sucesso!')"
```

## Instalação Específica para Plataformas

### Linux/macOS

Para ambientes Linux e macOS, o processo de instalação é semelhante:

```bash
# Clonar o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Criar e ativar um ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Instalar o pacote em modo de desenvolvimento
pip install -e .
```

### Windows

Para ambientes Windows:

```batch
# Clonar o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Criar e ativar um ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar o pacote em modo de desenvolvimento
pip install -e .
```

### Apple Silicon (M1/M2/M3)

Para computadores Mac com chips Apple Silicon, são necessárias etapas adicionais para desempenho ideal:

```bash
# Clonar o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Criar e ativar um ambiente virtual
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
# Clonar o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Criar e ativar um ambiente virtual
python3 -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows

# Instalar dependências (incluindo ferramentas de desenvolvimento)
pip install -r requirements.txt
pip install -r requirements-dev.txt  # ferramentas adicionais para desenvolvimento

# Instalar o pacote em modo editável
pip install -e .

# Configurar hooks de pré-commit
pre-commit install
```

## Instalação via AWS CodeArtifact

Para instalar o MicroDetect diretamente do AWS CodeArtifact:

```bash
# Configurar o AWS CLI com suas credenciais
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

## Verificando sua Instalação

Após a instalação, verifique se tudo está funcionando corretamente:

```bash
# Verificar a versão
microdetect --version

# Inicializar um projeto de exemplo
mkdir meu_projeto
cd meu_projeto
microdetect init
```

## Configurar Sistema de Atualização

Após a instalação, configure o sistema de atualização automática:

```bash
# Configurar AWS CodeArtifact
microdetect setup-aws --domain seu-dominio --repository seu-repositorio --configure-aws

# Verificar se há atualizações
microdetect update --check-only
```

## Solução de Problemas

### Problemas com PyTorch

Se você encontrar problemas com o PyTorch:

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

Se você encontrar problemas com o OpenCV:

```bash
# Desinstalar e reinstalar
pip uninstall opencv-python
pip install opencv-python-headless
```

### Problemas com CUDA

Se você encontrar problemas com suporte a GPU:

```bash
# Verificar disponibilidade do CUDA
python -c "import torch; print(f'CUDA disponível: {torch.cuda.is_available()}')"

# Ver dispositivos disponíveis
python -c "import torch; print(f'Dispositivos CUDA: {torch.cuda.device_count()}')"

# Verificar versão do CUDA
python -c "import torch; print(f'Versão CUDA: {torch.version.cuda}')"
```

### Problemas com Credenciais AWS

Se você encontrar problemas com o AWS CodeArtifact:

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

Para solução de problemas mais detalhada, consulte o [Guia de Solução de Problemas](troubleshooting.md).