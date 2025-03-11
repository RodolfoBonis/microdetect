"""
Módulo para gerenciamento de atualizações do pacote MicroDetect.
"""

import configparser
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Tuple

from microdetect.utils.colors import BRIGHT, ERROR, INFO, RESET, SUCCESS, WARNING

logger = logging.getLogger(__name__)


class UpdateManager:
    """Gerencia as atualizações do pacote MicroDetect a partir do AWS CodeArtifact."""

    @staticmethod
    def get_aws_codeartifact_token() -> Tuple[bool, str, str]:
        """
        Obtém um token de autenticação para o AWS CodeArtifact.

        Returns:
            Tupla contendo (sucesso, token, endpoint)
        """
        try:
            # Determinar domínio e repositório CodeArtifact
            domain = os.environ.get("AWS_CODEARTIFACT_DOMAIN")
            repository = os.environ.get("AWS_CODEARTIFACT_REPOSITORY")
            domain_owner = os.environ.get("AWS_CODEARTIFACT_OWNER")

            # Se não encontrado nas variáveis de ambiente, procurar em ~/.microdetect/config.ini
            if not domain or not repository:
                config_file = Path.home() / ".microdetect" / "config.ini"
                if config_file.exists():
                    config = configparser.ConfigParser()
                    config.read(config_file)
                    if "codeartifact" in config:
                        domain = domain or config["codeartifact"].get("domain")
                        repository = repository or config["codeartifact"].get("repository")
                        domain_owner = domain_owner or config["codeartifact"].get("domain_owner")

            # Se ainda não encontrado, tentar no .env local (compatibilidade)
            if not domain or not repository:
                env_file = Path(".env")
                if env_file.exists():
                    with env_file.open() as f:
                        for line in f:
                            if line.strip() and not line.startswith("#"):
                                key, value = line.strip().split("=", 1)
                                if key == "AWS_CODEARTIFACT_DOMAIN" and not domain:
                                    domain = value
                                elif key == "AWS_CODEARTIFACT_REPOSITORY" and not repository:
                                    repository = value
                                elif key == "AWS_CODEARTIFACT_OWNER" and not domain_owner:
                                    domain_owner = value

            # Verificar se temos as informações necessárias
            if not domain or not repository:
                logger.debug("Domínio ou repositório AWS CodeArtifact não configurado")
                return False, "", ""

            # Obter token AWS CodeArtifact
            aws_cmd = [
                "aws",
                "codeartifact",
                "get-authorization-token",
                "--domain",
                os.environ.get("AWS_CODEARTIFACT_DOMAIN", "seu-dominio"),
                "--query",
                "authorizationToken",
                "--output",
                "text",
            ]

            # Se houver um domain owner específico, adicione
            if domain_owner:
                aws_cmd.extend(["--domain-owner", domain_owner])

            token = subprocess.check_output(aws_cmd).decode("utf-8").strip()

            # Obter endpoint do repositório
            repo_cmd = [
                "aws",
                "codeartifact",
                "get-repository-endpoint",
                "--domain",
                domain,
                "--repository",
                repository,
                "--format",
                "pypi",
                "--query",
                "repositoryEndpoint",
                "--output",
                "text",
            ]

            # Se houver um domain owner específico, adicione
            if domain_owner:
                repo_cmd.extend(["--domain-owner", domain_owner])

            endpoint = subprocess.check_output(repo_cmd).decode("utf-8").strip()

            return True, token, endpoint
        except Exception as e:
            logger.debug(f"Erro ao obter token do AWS CodeArtifact: {str(e)}")
            return False, "", ""

    @staticmethod
    def get_latest_version() -> Tuple[bool, str]:
        """
        Verifica a versão mais recente disponível no AWS CodeArtifact.

        Returns:
            Tupla contendo (sucesso, versão_mais_recente)
        """
        success, token, endpoint = UpdateManager.get_aws_codeartifact_token()
        if not success:
            return False, ""

        try:
            # Usar pip para listar versões
            auth_endpoint = endpoint.replace("https://", f"https://aws:{token}@")

            cmd = [
                sys.executable,
                "-m",
                "pip",
                "index",
                "versions",
                "microdetect",
                "--index-url",
                f"{auth_endpoint}simple/",
                "--extra-index-url",
                "https://pypi.org/simple",
                "--no-cache-dir",
            ]

            env = os.environ.copy()
            # Também ajuste as variáveis de ambiente
            env["PIP_INDEX_URL"] = f"{auth_endpoint}simple/"
            env["PIP_EXTRA_INDEX_URL"] = "https://pypi.org/simple"

            output = subprocess.check_output(cmd, env=env).decode("utf-8")

            # Extrair a versão mais recente
            match = re.search(r'microdetect \((.*?)\)", latest', output)
            if match:
                return True, match.group(1)

            # Método alternativo de extração
            versions = re.findall(r"microdetect \((.*?)\)", output)
            if versions:
                # Ordenar as versões
                versions.sort(key=lambda s: [int(u) for u in s.split(".")])
                return True, versions[-1]  # Retorna a versão mais recente

            return False, ""
        except Exception as e:
            logger.debug(f"Erro ao verificar versão mais recente: {str(e)}")
            return False, ""

    @staticmethod
    def compare_versions(current: str, latest: str) -> bool:
        """
        Compara duas versões usando números semânticos.

        Args:
            current: Versão atual
            latest: Versão mais recente

        Returns:
            True se a versão mais recente for maior que a versão atual
        """
        if current == latest:
            return False

        # Dividir versões em partes (major, minor, patch)
        current_parts = [int(part) for part in current.split(".")]
        latest_parts = [int(part) for part in latest.split(".")]

        # Garantir que ambas as listas tenham o mesmo comprimento
        while len(current_parts) < len(latest_parts):
            current_parts.append(0)
        while len(latest_parts) < len(current_parts):
            latest_parts.append(0)

        # Comparar cada parte da versão
        for i in range(len(current_parts)):
            if latest_parts[i] > current_parts[i]:
                return True
            elif latest_parts[i] < current_parts[i]:
                return False

        return False

    @staticmethod
    def update_package(force: bool = False) -> bool:
        """
        Atualiza o pacote para a versão mais recente.

        Args:
            force: Se deve forçar a atualização sem pedir confirmação

        Returns:
            True se a atualização foi bem-sucedida
        """
        try:
            from microdetect import __version__ as current_version
        except ImportError:
            print(f"{ERROR}Não foi possível determinar a versão atual do MicroDetect{RESET}")
            return False

        # Verificar versão mais recente
        print(f"{INFO}Verificando versão mais recente...{RESET}")
        success, latest_version = UpdateManager.get_latest_version()
        if not success:
            print(f"{ERROR}Não foi possível verificar a versão mais recente{RESET}")
            return False

        # Verificar se a versão mais recente é maior que a atual
        needs_update = UpdateManager.compare_versions(current_version, latest_version)
        if not needs_update:
            print(f"{SUCCESS}MicroDetect já está na versão mais recente {BRIGHT}({current_version}){RESET}")
            return True

        # Perguntar se o usuário deseja atualizar
        if not force:
            print(
                f"{BRIGHT}{INFO}Nova versão disponível: {SUCCESS}{latest_version} {INFO}(atual: {WARNING}{current_version}{INFO}){RESET}"
            )
            response = input(f"{INFO}Deseja atualizar? {BRIGHT}[s/N]: {RESET}").strip().lower()
            if response != "s" and response != "sim":
                print(f"{WARNING}Atualização cancelada pelo usuário{RESET}")
                return False

        # Obter token e endpoint
        success, token, endpoint = UpdateManager.get_aws_codeartifact_token()
        if not success:
            print(f"{ERROR}Falha ao obter token do AWS CodeArtifact{RESET}")
            return False

        # Instalar versão mais recente
        print(f"{INFO}Atualizando MicroDetect para versão {SUCCESS}{latest_version}{INFO}...{RESET}")

        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "microdetect",
            "--index-url",
            f"{endpoint}simple/",
            "--extra-index-url",
            "https://pypi.org/simple",
            "--no-cache-dir",
        ]

        env = os.environ.copy()
        env["PIP_INDEX_URL"] = f"{endpoint}simple/"
        env["PIP_EXTRA_INDEX_URL"] = "https://pypi.org/simple"
        env["TWINE_USERNAME"] = "aws"
        env["TWINE_PASSWORD"] = token

        try:
            process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

            # Mostrar progresso em tempo real
            for line in process.stdout:
                print(line, end="")

            process.wait()

            if process.returncode == 0:
                print(f"{SUCCESS}{BRIGHT}MicroDetect atualizado com sucesso para versão {latest_version}{RESET}")
                return True
            else:
                stderr = process.stderr.read()
                print(f"{ERROR}Erro ao atualizar MicroDetect: {stderr}{RESET}")
                return False
        except Exception as e:
            print(f"{ERROR}Erro durante a atualização: {str(e)}{RESET}")
            return False

    @staticmethod
    def check_for_updates() -> Dict[str, str]:
        """
        Verifica se há atualizações disponíveis e retorna informações sobre a versão.

        Returns:
            Dicionário com informações sobre a versão atual e disponível
        """
        try:
            from microdetect import __version__ as current_version
        except ImportError:
            logger.warning("Não foi possível determinar a versão atual do MicroDetect")
            return {"error": "Não foi possível determinar a versão atual"}

        success, latest_version = UpdateManager.get_latest_version()
        if not success:
            logger.warning("Não foi possível verificar a versão mais recente")
            return {"error": "Não foi possível verificar a versão mais recente", "current": current_version}

        needs_update = UpdateManager.compare_versions(current_version, latest_version)
        return {"current": current_version, "latest": latest_version, "needs_update": needs_update}

    @staticmethod
    def check_for_updates_before_command() -> bool:
        """
        Verificar se há atualizações disponíveis e notificar o usuário.
        Esta função deve ser chamada antes da execução de qualquer comando.
        """
        # Verificar se deve pular esta verificação (variável de ambiente)
        if os.environ.get("MICRODETECT_SKIP_UPDATE_CHECK") == "1":
            return False

        # Verificar se o arquivo de cache existe e se a verificação já foi feita hoje
        cache_dir = os.path.join(tempfile.gettempdir(), "microdetect")
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, "update_check.json")

        current_time = time.time()
        check_update = True

        # Verificar cache para não verificar mais de uma vez por dia
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                last_check_time = cache_data.get("last_check_time", 0)
                if current_time - last_check_time < 86400:  # 24 horas em segundos
                    check_update = False
            except Exception:
                pass

        if check_update:
            try:
                # Atualizar o arquivo de cache
                with open(cache_file, "w") as f:
                    json.dump({"last_check_time": current_time}, f)

                update_info = UpdateManager.check_for_updates()
                if update_info.get("needs_update", False):
                    print(
                        f"\n{INFO}🔄 {BRIGHT}Nova versão do MicroDetect disponível: {SUCCESS}{update_info['latest']} "
                        f"{INFO}(atual: {WARNING}{update_info['current']}{INFO}){RESET}"
                    )
                    return UpdateManager.update_package()
            except Exception as e:
                logger.debug(f"Erro ao verificar atualizações: {str(e)}")
                return False

        return False
