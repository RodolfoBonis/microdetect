@echo off
REM Script para configuração do ambiente MicroDetect no Windows

setlocal EnableDelayedExpansion

set CONDA_ENV_NAME=yeast_detection
set PYTHON_VERSION=3.12

REM Verificar argumentos
if "%1"=="" goto :show_help
if "%1"=="--create" goto :create_env
if "%1"=="--install" goto :install_deps
if "%1"=="--update" goto :update_deps
if "%1"=="--help" goto :show_help

echo Opção desconhecida: %1
goto :show_help

:show_help
echo Uso: %0 [opções]
echo.
echo Opções:
echo   --create         Criar novo ambiente conda
echo   --install        Instalar dependências no ambiente atual
echo   --update         Atualizar dependências no ambiente atual
echo   --help           Mostrar esta ajuda
echo.
goto :eof

:create_env
echo Criando ambiente conda %CONDA_ENV_NAME% com Python %PYTHON_VERSION%...
call conda create -y -n %CONDA_ENV_NAME% python=%PYTHON_VERSION%
echo Ambiente criado. Ative-o com: conda activate %CONDA_ENV_NAME%
goto :eof

:install_deps
echo Instalando dependências...

REM Verificar se estamos em um ambiente conda
if "%CONDA_PREFIX%"=="" (
    echo ERRO: Nenhum ambiente conda ativo. Ative um ambiente conda primeiro.
    exit /b 1
)

REM Instalar dependências comuns
echo Instalando dependências comuns...
call pip install numpy opencv-python PyYAML matplotlib pillow tqdm

REM Verificar disponibilidade de CUDA
where /q nvcc
if %ERRORLEVEL% equ 0 (
    echo CUDA detectado. Instalando PyTorch com suporte a CUDA...

    REM Instalar diretamente do canal conda para garantir compatibilidade
    call conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia -y
) else (
    echo Nenhuma GPU CUDA detectada. Instalando PyTorch CPU...
    call pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
)

REM Instalar optree para inferência mais rápida
echo Instalando optree para inferência mais rápida...
call pip install --upgrade optree>=0.13.0

REM Instalar Ultralytics (YOLOv8)
echo Instalando Ultralytics YOLOv8...
call pip install ultralytics

REM Instalar outras dependências do projeto
if exist requirements.txt (
    echo Instalando dependências do requirements.txt...
    call pip install -r requirements.txt
)

REM Instalar o próprio pacote em modo desenvolvimento
echo Instalando o pacote em modo desenvolvimento...
call pip install -e .

REM Verificar instalação
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

echo Instalação concluída!
goto :eof

:update_deps
echo Atualizando dependências...
call pip install -U numpy opencv-python PyYAML matplotlib pillow tqdm ultralytics
call pip install --upgrade optree>=0.13.0

if exist requirements.txt (
    call pip install -U -r requirements.txt
)

echo Atualização concluída!
goto :eof