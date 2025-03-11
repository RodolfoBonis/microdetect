@echo off
REM Script robusto para instalação do MicroDetect em ambiente de produção para Windows

echo === Instalando MicroDetect para Producao ===

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Erro: Python nao encontrado. Por favor, instale o Python 3.9 ou superior.
    exit /b 1
)

REM Definir variáveis para Python e pip
set PYTHON_CMD=python
set PIP_CMD=pip

REM Verificar versão do Python
for /f "tokens=2" %%I in ('python --version') do set PYTHON_VERSION=%%I
echo Python %PYTHON_VERSION% detectado.

REM Processar argumentos
set USE_VENV=0
set CREATE_EXAMPLE=0

:parse_args
if "%~1"=="" goto end_parse_args
if "%~1"=="--virtual-env" set USE_VENV=1
if "%~1"=="--with-example" set CREATE_EXAMPLE=1
shift
goto parse_args
:end_parse_args

REM Criar ambiente virtual se solicitado
if %USE_VENV% equ 1 (
    echo Criando ambiente virtual...
    %PYTHON_CMD% -m venv venv
    call venv\Scripts\activate
    set PYTHON_CMD=python
    set PIP_CMD=pip
    echo Ambiente virtual ativado.
)

REM Instalar dependências
echo Instalando dependencias...
%PIP_CMD% install --upgrade pip
%PIP_CMD% install wheel

REM Instalar PyTorch com suporte a hardware apropriado
echo Detectando hardware para instalacao otimizada de PyTorch...

REM Verificar se CUDA está disponível usando uma abordagem mais robusta
set CUDA_DETECTED=0

REM Testar diretamente com Python (mais confiável)
%PYTHON_CMD% -c "import subprocess; import sys; try: subprocess.check_output(['nvidia-smi']); print('NVIDIA GPU detectada'); sys.exit(0); except: sys.exit(1)" >nul 2>&1
if %errorlevel% equ 0 (
    echo GPU NVIDIA detectada via teste direto.
    set CUDA_DETECTED=1
    goto :gpu_detection_done
)

REM Verificar diretório CUDA
if exist "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA" (
    echo Diretorio CUDA encontrado.
    set CUDA_DETECTED=1
    goto :gpu_detection_done
)

REM Verificar diretório de drivers NVIDIA
if exist "C:\Windows\System32\DriverStore\FileRepository\nv" (
    dir /b "C:\Windows\System32\DriverStore\FileRepository\nv*" >nul 2>&1
    if %errorlevel% equ 0 (
        echo Drivers NVIDIA encontrados.
        set CUDA_DETECTED=1
        goto :gpu_detection_done
    )
)

:gpu_detection_done
if %CUDA_DETECTED% equ 1 (
    echo CUDA detectado. Instalando PyTorch com suporte a CUDA...
    %PIP_CMD% install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
) else (
    echo GPU NVIDIA nao detectada. Instalando PyTorch CPU...
    %PIP_CMD% install torch torchvision
)

REM Instalar optree para inferência mais rápida
echo Instalando optree para inferencia mais rapida...
%PIP_CMD% install --upgrade optree>=0.13.0

REM Instalar Ultralytics (YOLOv8)
echo Instalando Ultralytics YOLOv8...
%PIP_CMD% install ultralytics

REM Instalar o próprio pacote em modo desenvolvimento
echo Instalando o pacote em modo desenvolvimento...
%PIP_CMD% install -e .

REM Verificar instalação
echo Verificando instalacao...
%PYTHON_CMD% -c "import microdetect; print(f'MicroDetect importado com sucesso!')"
if %errorlevel% neq 0 (
    echo Erro: Falha na instalacao do MicroDetect.
    exit /b 1
)

REM Verificar PyTorch e CUDA
echo Verificando PyTorch e CUDA:
%PYTHON_CMD% -c "import torch; print(f'PyTorch versao: {torch.__version__}'); print(f'CUDA disponivel: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"Nenhuma GPU\"}')"

REM Inicializar um projeto de exemplo
if %CREATE_EXAMPLE% equ 1 (
    echo Criando projeto de exemplo...
    mkdir microdetect_example
    cd microdetect_example
    microdetect init
    echo Projeto de exemplo criado em: %cd%
)

echo.
echo === Instalacao concluida! ===
echo.
echo Para iniciar um projeto MicroDetect:
echo 1. Crie um diretorio para seu projeto: mkdir meu_projeto
echo 2. Entre no diretorio: cd meu_projeto
echo 3. Inicialize o projeto: microdetect init
echo 4. Siga as instrucoes para comecar a usar o MicroDetect
echo.
echo Obrigado por usar MicroDetect!