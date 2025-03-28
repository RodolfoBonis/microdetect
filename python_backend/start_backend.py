import os
import sys
import importlib
import subprocess
import time
import logging
import argparse
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger('start_backend')

def get_python_executable():
    """Retorna o caminho para o executável Python atual."""
    return sys.executable

def check_required_modules():
    """Verifica se todos os módulos necessários estão instalados."""
    required_modules = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'pydantic', 
        'pydantic_settings', 'python-multipart', 'numpy'
    ]
    
    missing_modules = []
    for module in required_modules:
        module_name = module.replace('-', '_')
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing_modules.append(module)
    
    return missing_modules

def setup_user_directories():
    """Configura os diretórios necessários em ~/.microdetect"""
    try:
        # Criar diretório base em ~/.microdetect
        home_dir = Path.home() / ".microdetect"
        home_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Diretório base criado: {home_dir}")
        
        # Criar estrutura de diretórios para dados
        data_subdirs = [
            "data",
            "data/datasets",
            "data/models",
            "data/images",
            "data/gallery",
            "data/temp",
            "data/static"
        ]
        
        for subdir in data_subdirs:
            dir_path = home_dir / subdir
            dir_path.mkdir(exist_ok=True, parents=True)
            logger.info(f"Diretório criado: {dir_path}")
        
        # Garantir que as permissões estejam corretas
        os.system(f"chmod -R 755 {home_dir}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao configurar diretórios do usuário: {e}")
        return False

def install_dependencies():
    """Instala as dependências do requirements.txt."""
    logger.info("Instalando dependências Python...")
    print("Instalando dependências...\n")
    
    # Verificar se o arquivo requirements.txt existe
    req_file = Path(__file__).parent / 'requirements.txt'
    if not req_file.exists():
        logger.error(f"Arquivo requirements.txt não encontrado em {req_file}")
        return False
    
    try:
        # Usar subprocess com captura de saída em tempo real
        process = subprocess.Popen(
            [sys.executable, '-m', 'pip', 'install', '-r', str(req_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        
        # Ler e registrar a saída em tempo real
        for line in iter(process.stdout.readline, ''):
            if line.strip():  # Ignorar linhas vazias
                print(line.rstrip())
            
        # Aguardar que o processo termine
        returncode = process.wait()
        
        if returncode != 0:
            logger.error(f"Falha ao instalar dependências. Código de retorno: {returncode}")
            return False
        
        logger.info("Dependências instaladas com sucesso")
        print("Dependências instaladas com sucesso")
        
        # Verificar novamente os módulos necessários
        missing = check_required_modules()
        if missing:
            logger.error(f"Alguns módulos ainda estão ausentes após a instalação: {', '.join(missing)}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Erro ao instalar dependências: {str(e)}")
        print(f"Erro ao instalar dependências: {str(e)}")
        return False

def setup_app():
    """Configura a aplicação antes de iniciar."""
    # Verificar se o diretório 'app' existe
    app_dir = Path(__file__).parent / 'app'
    if not app_dir.exists():
        logger.error(f"Diretório 'app' não encontrado em {app_dir}")
        return False
    
    # Verificar se o arquivo main.py existe
    main_file = app_dir / 'main.py'
    if not main_file.exists():
        logger.error(f"Arquivo main.py não encontrado em {main_file}")
        return False
    
    # Adicionar o diretório atual ao path do Python para importações
    python_path = str(Path(__file__).parent)
    if python_path not in sys.path:
        sys.path.insert(0, python_path)
        logger.info(f"Adicionado diretório ao PYTHONPATH: {python_path}")
    
    # Configurar diretórios no home do usuário
    if not setup_user_directories():
        logger.error("Falha ao configurar diretórios do usuário")
        return False
    
    # Inicializar banco de dados se necessário
    if not init_database():
        logger.error("Falha ao inicializar banco de dados")
        return False
    
    return True

def init_database():
    """Inicializa o banco de dados e executa migrações."""
    try:
        # Importar componentes necessários para inicializar o banco
        from app.database.database import Base, engine
        from app.models import image, dataset, annotation, training_session, model, dataset_image
        
        logger.info("Inicializando banco de dados...")
        
        # Em vez de criar todas as tabelas manualmente, vamos usar o Alembic para migrações
        try:
            # Verifica se o diretório alembic existe
            alembic_dir = Path(__file__).parent / 'alembic'
            if not alembic_dir.exists():
                logger.error("Diretório de migrações do Alembic não encontrado")
                return False
                
            # Executa as migrações usando o Alembic
            logger.info("Executando migrações do Alembic...")
            import subprocess
            result = subprocess.run(
                [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Erro ao executar migrações: {result.stderr}")
                # Se falhar, tente criar as tabelas diretamente (fallback)
                logger.info("Tentando criar tabelas diretamente como fallback...")
                Base.metadata.create_all(bind=engine)
            else:
                logger.info(f"Migrações executadas com sucesso: {result.stdout}")
                
        except Exception as migration_error:
            logger.error(f"Erro durante migrações: {migration_error}")
            logger.info("Tentando criar tabelas diretamente como fallback...")
            # Fallback: criar todas as tabelas definidas nos modelos
            Base.metadata.create_all(bind=engine)
            
        logger.info("Banco de dados inicializado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        return False

def start_server(host='127.0.0.1', port=8000):
    """Inicia o servidor FastAPI."""
    try:
        # Garantir que tudo esteja configurado corretamente
        if not setup_app():
            logger.error("Falha na configuração da aplicação")
            return False
        
        # Verificar se uvicorn está instalado
        try:
            import uvicorn
        except ImportError:
            logger.error("Uvicorn não está instalado. Falha ao iniciar servidor.")
            return False
        
        logger.info(f"Iniciando servidor na porta {port}...")
        print(f"Iniciando servidor na porta {port}...")
        
        # Iniciar o servidor
        uvicorn.run("app.main:app", 
                    host=host, 
                    port=port, 
                    reload=False, 
                    log_level="info")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {str(e)}")
        print(f"Erro ao iniciar servidor: {str(e)}")
        return False

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description='Inicia o servidor FastAPI da aplicação MicroDetect')
    parser.add_argument('--host', default='127.0.0.1', help='Host para o servidor')
    parser.add_argument('--port', type=int, default=8000, help='Porta para o servidor')
    parser.add_argument('--install-only', action='store_true', help='Apenas instalar dependências sem iniciar o servidor')
    args = parser.parse_args()
    
    # Verificar variáveis de ambiente
    install_deps_first = os.environ.get('INSTALL_DEPS_FIRST', '').lower() in ('true', '1', 'yes')
    
    # Verificar módulos necessários
    missing_modules = check_required_modules()
    
    # Se há módulos faltando ou foi solicitada a instalação
    if missing_modules or install_deps_first or args.install_only:
        if missing_modules:
            logger.warning(f"Módulos necessários ausentes: {', '.join(missing_modules)}")
        
        # Instalar dependências
        success = install_dependencies()
        if not success:
            logger.error("Falha ao instalar dependências. Abortando inicialização.")
            sys.exit(1)
        
        # Se for apenas para instalar, sair após a instalação
        if args.install_only:
            logger.info("Instalação concluída. Saindo conforme solicitado.")
            sys.exit(0)
    else:
        logger.info("Todas as dependências já estão instaladas")
    
    # Iniciar o servidor
    start_server(host=args.host, port=args.port)

if __name__ == "__main__":
    main() 