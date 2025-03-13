"""
Módulo para configuração do AWS CodeArtifact para atualizações do MicroDetect.
"""

import configparser
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from microdetect.utils.colors import BRIGHT, ERROR, INFO, RESET, SUCCESS, WARNING

logger = logging.getLogger(__name__)


class AWSSetupManager:
    """Gerencia a configuração do ambiente AWS para o MicroDetect."""

    @staticmethod
    def run_command(command, check=True):
        """
        Executa um comando e retorna seu resultado.

        Args:
            command: Lista com o comando e seus argumentos
            check: Se deve verificar o código de saída

        Returns:
            A saída do comando ou None em caso de erro
        """
        try:
            result = subprocess.run(command, check=check, capture_output=True, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar comando: {e}")
            logger.error(f"Saída de erro: {e.stderr}")
            if check:
                raise
            return None

    @staticmethod
    def check_aws_cli():
        """
        Verifica se o AWS CLI está instalado.

        Returns:
            True se o AWS CLI estiver instalado, False caso contrário
        """
        try:
            subprocess.run(["aws", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def install_aws_cli():
        """
        Instala o AWS CLI.

        Returns:
            True se a instalação foi bem-sucedida, False caso contrário
        """
        system = sys.platform
        print(f"{INFO}AWS CLI não encontrado. Tentando instalar...{RESET}")

        try:
            if system == "linux" or system == "linux2":
                # Linux
                print(f"{INFO}Instalando AWS CLI no Linux...{RESET}")
                AWSSetupManager.run_command(["pip", "install", "awscli"])
            elif system == "darwin":
                # macOS
                print(f"{INFO}Instalando AWS CLI no macOS...{RESET}")
                AWSSetupManager.run_command(["pip", "install", "awscli"])
            elif system == "win32":
                # Windows
                print(f"{INFO}Instalando AWS CLI no Windows...{RESET}")
                AWSSetupManager.run_command(["pip", "install", "awscli"])
            else:
                print(f"{ERROR}Sistema operacional não suportado: {system}{RESET}")
                print(f"{INFO}Por favor, instale o AWS CLI manualmente: https://aws.amazon.com/cli/{RESET}")
                return False

            # Verificar se a instalação foi bem-sucedida
            if AWSSetupManager.check_aws_cli():
                print(f"{SUCCESS}AWS CLI instalado com sucesso!{RESET}")
                return True
            else:
                print(f"{ERROR}Falha ao instalar o AWS CLI. Por favor, instale manualmente.{RESET}")
                return False
        except Exception as e:
            print(f"{ERROR}Erro ao instalar AWS CLI: {str(e)}{RESET}")
            return False

    @staticmethod
    def configure_aws(
        domain: str,
        repository: str,
        domain_owner: Optional[str] = None,
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None,
        aws_region: Optional[str] = None,
    ) -> bool:
        """
        Configura as credenciais AWS e variáveis de ambiente para o AWS CodeArtifact.

        Args:
            domain: Nome do domínio AWS CodeArtifact
            repository: Nome do repositório AWS CodeArtifact
            domain_owner: ID da conta proprietária do domínio (opcional)
            aws_access_key: AWS Access Key ID
            aws_secret_key: AWS Secret Access Key
            aws_region: Região AWS

        Returns:
            True se a configuração foi bem-sucedida, False caso contrário
        """
        try:
            aws_dir = Path.home() / ".aws"
            aws_dir.mkdir(exist_ok=True)

            # Configurar credenciais
            if aws_access_key and aws_secret_key:
                print(f"{INFO}Configurando credenciais AWS...{RESET}")
                credentials_file = aws_dir / "credentials"
                config = configparser.ConfigParser()

                if credentials_file.exists():
                    config.read(credentials_file)

                if "default" not in config:
                    config["default"] = {}

                config["default"]["aws_access_key_id"] = aws_access_key
                config["default"]["aws_secret_access_key"] = aws_secret_key

                with credentials_file.open("w") as f:
                    config.write(f)

                print(f"{SUCCESS}Credenciais AWS configuradas com sucesso!{RESET}")

            # Configurar região
            if aws_region:
                print(f"{INFO}Configurando região AWS para {BRIGHT}{aws_region}{RESET}")
                config_file = aws_dir / "config"
                config = configparser.ConfigParser()

                if config_file.exists():
                    config.read(config_file)

                if "default" not in config:
                    config["default"] = {}

                config["default"]["region"] = aws_region

                with config_file.open("w") as f:
                    config.write(f)

                print(f"{SUCCESS}Região AWS configurada com sucesso!{RESET}")

            # Criar ou atualizar arquivo .env para armazenar configurações do CodeArtifact
            microdetect_dir = Path.home() / ".microdetect"
            microdetect_dir.mkdir(exist_ok=True)

            config_file = microdetect_dir / "config.ini"
            config = configparser.ConfigParser()

            if config_file.exists():
                config.read(config_file)

            if "codeartifact" not in config:
                config["codeartifact"] = {}

            config["codeartifact"]["domain"] = domain
            config["codeartifact"]["repository"] = repository
            if domain_owner:
                config["codeartifact"]["domain_owner"] = domain_owner

            with config_file.open("w") as f:
                config.write(f)

            print(f"{SUCCESS}Configurações do AWS CodeArtifact salvas em {BRIGHT}{config_file}{RESET}")

            os.environ["AWS_CODEARTIFACT_DOMAIN"] = domain
            os.environ["AWS_CODEARTIFACT_REPOSITORY"] = repository
            if domain_owner:
                os.environ["AWS_CODEARTIFACT_OWNER"] = domain_owner

            return True
        except Exception as e:
            print(f"{ERROR}Erro ao configurar AWS: {str(e)}{RESET}")
            return False

    @staticmethod
    def test_codeartifact_login() -> Tuple[bool, str]:
        """
        Testa a conexão com o AWS CodeArtifact para verificar se as configurações estão corretas.

        Returns:
            Tupla com (sucesso, mensagem)
        """
        print(f"{INFO}Testando conexão com AWS CodeArtifact...{RESET}")

        try:
            from microdetect.updater.updater import UpdateManager

            success, token, endpoint = UpdateManager.get_aws_codeartifact_token()

            if success:
                print(f"{SUCCESS}✓ Conexão com AWS CodeArtifact bem-sucedida!{RESET}")
                print(f"{INFO}Endpoint do repositório: {BRIGHT}{endpoint}{RESET}")

                # Verificar versão mais recente disponível
                success, latest_version = UpdateManager.get_latest_version()
                if success:
                    print(f"{INFO}Versão mais recente disponível: {SUCCESS}{latest_version}{RESET}")
                    return True, f"Conexão bem-sucedida. Versão mais recente: {latest_version}"
                else:
                    print(f"{WARNING}⚠️ Não foi possível obter a versão mais recente.{RESET}")
                    return True, "Conexão bem-sucedida, mas não foi possível obter a versão mais recente."
            else:
                print(f"{ERROR}❌ Não foi possível obter token do AWS CodeArtifact.{RESET}")
                print(f"{WARNING}   Verifique suas credenciais AWS e configurações do CodeArtifact.{RESET}")
                return False, "Falha ao obter token do AWS CodeArtifact."
        except ImportError:
            print(f"{ERROR}❌ Não foi possível importar o módulo UpdateManager.{RESET}")
            print(f"{WARNING}   Verifique se o MicroDetect está instalado corretamente.{RESET}")
            return False, "Módulo UpdateManager não encontrado."
        except Exception as e:
            print(f"{ERROR}❌ Erro ao testar conexão: {str(e)}{RESET}")
            return False, f"Erro ao testar conexão: {str(e)}"
