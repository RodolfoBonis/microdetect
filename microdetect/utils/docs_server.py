"""
Módulo para servir documentação como uma página web com menu lateral e suporte a múltiplos idiomas.
"""

import http.server
import os
import socketserver
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

# Importar as constantes de cores do módulo existente
from microdetect.utils.colors import BRIGHT, COLORS_AVAILABLE, ERROR, INFO, RESET, SUCCESS, WARNING

# Declaração inicial das variáveis globais
MARKDOWN_AVAILABLE = False

try:
    import markdown
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name

    MARKDOWN_AVAILABLE = True
except ImportError:
    pass


# Constantes
PORT = 8080
HOST = "127.0.0.1"

# Idiomas suportados
LANGUAGES = {
    "en": {"name": "English", "flag": "🇺🇸", "dir": "en"},
    "pt": {"name": "Português", "flag": "🇧🇷", "dir": "pt"},
}
DEFAULT_LANGUAGE = "en"


class MarkdownLinkProcessor:
    """Processador de links para ajustar links relativos para funcionar com o docs server."""

    def __init__(self, current_language):
        """
        Inicializa o processador de links.

        Args:
            current_language: Idioma atual usado para construir os links
        """
        self.current_language = current_language

    def process_html(self, html_content):
        """
        Processa links em conteúdo HTML para funcionar com o docs server.

        Args:
            html_content: Conteúdo HTML com links a serem processados

        Returns:
            HTML com links modificados para funcionar com o docs server
        """
        import re

        # Padrão para capturar links que apontam para arquivos .md
        pattern = r'<a\s+href=["\']([^"\'#]+\.md)(#[^"\']+)?["\']([^>]*)>(.*?)</a>'

        def replace_link(match):
            # Extrai as partes do link
            link_path = match.group(1)
            anchor = match.group(2) or ''
            attributes = match.group(3)
            link_text = match.group(4)

            # Cria um link que funciona com o docs server
            new_href = f"/?file={link_path}&lang={self.current_language}{anchor}"

            return f'<a href="{new_href}"{attributes}>{link_text}</a>'

        # Substitui todos os links para arquivos .md
        processed_html = re.sub(pattern, replace_link, html_content)

        return processed_html


def find_docs_dir() -> Path:
    """
    Localiza o diretório de documentação.

    Returns:
        O caminho para o diretório docs.
    """
    # Buscar a partir do diretório atual
    current_dir = Path.cwd()
    docs_dir = current_dir / "docs"

    if docs_dir.exists():
        return docs_dir

    # Buscar a partir do diretório do pacote
    package_dir = Path(__file__).parent.parent.parent
    docs_dir = package_dir / "docs"

    if docs_dir.exists():
        return docs_dir

    # Buscar na pasta de compartilhamento de dados padrão da instalação
    try:
        import site

        for site_dir in site.getsitepackages():
            share_docs_dir = Path(site_dir) / "../share/microdetect/docs"
            if share_docs_dir.exists() and share_docs_dir.is_dir():
                return share_docs_dir.resolve()
    except (ImportError, AttributeError):
        pass

    # Verificar também em userbase para instalações por usuário
    try:
        user_base = site.USER_BASE
        share_docs_dir = Path(user_base) / "share/microdetect/docs"
        if share_docs_dir.exists() and share_docs_dir.is_dir():
            return share_docs_dir.resolve()
    except (ImportError, AttributeError):
        pass

    # Se não encontrar, criar um diretório temporário
    import tempfile

    temp_dir = Path(tempfile.mkdtemp(prefix="microdetect_docs_"))
    temp_docs = temp_dir / "docs"
    temp_docs.mkdir(exist_ok=True)

    # Criar estrutura de diretórios para idiomas
    for lang in LANGUAGES.values():
        lang_dir = temp_docs / lang["dir"]
        lang_dir.mkdir(exist_ok=True)

        with open(lang_dir / "index.md", "w") as f:
            if lang["dir"] == "en":
                f.write("# MicroDetect Documentation\n\n")
                f.write("Documentation directory not found. Please make sure the 'docs' directory exists.\n")
            else:
                f.write("# Documentação do MicroDetect\n\n")
                f.write("Diretório de documentação não encontrado. Por favor, certifique-se de que o diretório 'docs' existe.\n")

    return temp_docs


def get_doc_files(docs_dir: Path, language: str = DEFAULT_LANGUAGE) -> Dict[str, List[Path]]:
    """
    Obtém a lista de arquivos de documentação organizados por categoria para um idioma específico.

    Args:
        docs_dir: Diretório de documentação
        language: Código do idioma (ex: 'en', 'pt')

    Returns:
        Dicionário com categorias e arquivos
    """
    # Verificar se o diretório do idioma existe
    lang_dir = docs_dir / language
    if not lang_dir.exists() or not lang_dir.is_dir():
        # Fallback para o idioma padrão se o diretório do idioma solicitado não existir
        language = DEFAULT_LANGUAGE
        lang_dir = docs_dir / language

        # Se ainda não existir, retornar vazio
        if not lang_dir.exists() or not lang_dir.is_dir():
            return {}

    # Categorias e ordem de exibição
    if language == 'en':
        categories = {
            "Getting Started": ["installation_guide.md", "troubleshooting.md"],
            "Features": [],
            "Updates": ["update_system.md", "aws_codeartifact_setup.md", "update_and_release_model.md"],
            "Configuration": ["advanced_configuration.md"],
            "Development": ["development_guide.md"],
        }
    else:  # Portuguese
        categories = {
            "Primeiros Passos": ["installation_guide.md", "troubleshooting.md"],
            "Funcionalidades": [],
            "Atualizações": ["update_system.md", "aws_codeartifact_setup.md", "update_and_release_model.md"],
            "Configuração": ["advanced_configuration.md"],
            "Desenvolvimento": ["development_guide.md"],
        }

    # Arquivos não categorizados
    uncategorized = []

    # Mapear arquivos para suas categorias
    for file in lang_dir.glob("*.md"):
        file_name = file.name
        if file_name == "index.md":
            continue

        # Verificar em qual categoria o arquivo se encaixa
        found = False
        for category, files in categories.items():
            if file_name in files:
                found = True
                break

        if not found:
            # Tenta categorizar com base no nome
            if "install" in file_name or "setup" in file_name:
                categories["Getting Started" if language == "en" else "Primeiros Passos"].append(file_name)
            elif "config" in file_name:
                categories["Configuration" if language == "en" else "Configuração"].append(file_name)
            elif "develop" in file_name or "contrib" in file_name:
                categories["Development" if language == "en" else "Desenvolvimento"].append(file_name)
            elif "update" in file_name or "release" in file_name:
                categories["Updates" if language == "en" else "Atualizações"].append(file_name)
            else:
                categories["Features" if language == "en" else "Funcionalidades"].append(file_name)

    # Remover categorias vazias
    result = {k: [] for k in categories.keys()}

    # Preencher com os caminhos completos
    for category, file_names in categories.items():
        for file_name in file_names:
            file_path = lang_dir / file_name
            if file_path.exists():
                result[category].append(file_path)

    # Remover categorias vazias
    result = {k: v for k, v in result.items() if v}

    return result


"""
Implementação de execução em background para o servidor de documentação.
"""

import os
import signal
import subprocess
import tempfile
from pathlib import Path


# Caminho para o arquivo PID
def get_pid_file_path():
    """Retorna o caminho para o arquivo que armazena o PID do servidor."""
    temp_dir = Path(tempfile.gettempdir()) / "microdetect"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir / "docs_server.pid"


def start_server_in_background(port=None, language=None):
    """
    Inicia o servidor de documentação em background.

    Args:
        port: Porta para o servidor (opcional)
        language: Idioma padrão a ser usado

    Returns:
        Dicionário com informações do processo iniciado
    """
    server_script = __file__

    # Criar comando com argumentos
    cmd = [sys.executable, server_script, "--daemon"]
    if port:
        cmd.extend(["--port", str(port)])

    if language:
        cmd.extend(["--lang", str(language)])

    # Iniciar processo em background
    if os.name == "nt":  # Windows
        # No Windows, usamos subprocess com DETACHED_PROCESS
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
        pid = process.pid
    else:  # Unix/Linux/Mac
        # No Unix, usamos o fork do processo
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        pid = process.pid

    # Aguardar um momento para o servidor iniciar
    time.sleep(1)

    # Verificar se o processo ainda está em execução
    try:
        os.kill(pid, 0)  # Verifica se o processo existe, sem enviar sinal
        running = True
    except OSError:
        running = False

    # Salvar PID em arquivo
    if running:
        with open(get_pid_file_path(), "w") as f:
            f.write(str(pid))

        # Abrir navegador se o servidor estiver rodando
        server_url = f"http://{HOST}:{port or PORT}"
        open_browser(server_url)

        if COLORS_AVAILABLE:
            print(f"{SUCCESS}Documentation server started in background at {BRIGHT}{server_url}{RESET}")
            print(f"{INFO}To stop the server, run: microdetect docs --stop{RESET}")
        else:
            print(f"Documentation server started in background at {server_url}")
            print(f"To stop the server, run: microdetect docs --stop")

        return {"status": "success", "pid": pid, "url": server_url}
    else:
        if COLORS_AVAILABLE:
            print(f"{ERROR}Failed to start documentation server in background{RESET}")
        else:
            print(f"Failed to start documentation server in background")
        return {"status": "error", "message": "Failed to start server"}


def stop_background_server():
    """
    Para o servidor de documentação em execução em background.

    Returns:
        True se o servidor foi parado com sucesso, False caso contrário
    """
    pid_file = get_pid_file_path()

    # Verificar se o arquivo PID existe
    if not pid_file.exists():
        if COLORS_AVAILABLE:
            print(f"{WARNING}No running documentation server found{RESET}")
        else:
            print(f"No running documentation server found")
        return False

    # Ler PID do arquivo
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
    except (ValueError, IOError) as e:
        if COLORS_AVAILABLE:
            print(f"{ERROR}Error reading PID file: {str(e)}{RESET}")
        else:
            print(f"Error reading PID file: {str(e)}")
        return False

    # Tentar parar o processo
    try:
        if os.name == "nt":  # Windows
            subprocess.call(["taskkill", "/F", "/PID", str(pid)])
        else:  # Unix/Linux/Mac
            os.kill(pid, signal.SIGTERM)

        # Remover arquivo PID
        pid_file.unlink()

        if COLORS_AVAILABLE:
            print(f"{SUCCESS}Documentation server stopped successfully{RESET}")
        else:
            print(f"Documentation server stopped successfully")
        return True
    except Exception as e:
        if COLORS_AVAILABLE:
            print(f"{ERROR}Error stopping documentation server: {str(e)}{RESET}")
        else:
            print(f"Error stopping documentation server: {str(e)}")
        return False


def check_server_status():
    """
    Verifica se o servidor de documentação está em execução.

    Returns:
        Dicionário com status e informações do servidor
    """
    pid_file = get_pid_file_path()

    # Verificar se o arquivo PID existe
    if not pid_file.exists():
        return {"status": "stopped"}

    # Ler PID do arquivo
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
    except (ValueError, IOError):
        return {"status": "unknown"}

    # Verificar se o processo ainda está em execução
    try:
        os.kill(pid, 0)  # Verifica se o processo existe, sem enviar sinal
        return {"status": "running", "pid": pid, "url": f"http://{HOST}:{PORT}"}
    except OSError:
        # Processo não existe mais, remover arquivo PID
        pid_file.unlink()
        return {"status": "stopped"}


def run_as_daemon(port=None, language=None):
    """
    Executa o servidor como um daemon (processo em background).

    Args:
        port: Porta a ser usada pelo servidor
        language: Idioma padrão a ser usado
    """
    global PORT, DEFAULT_LANGUAGE
    if port:
        PORT = port
    if language and language in LANGUAGES:
        DEFAULT_LANGUAGE = language

    # Redirecionar saída para /dev/null ou NUL
    with open(os.devnull, "w") as devnull:
        # Substituir stdout e stderr
        sys.stdout = devnull
        sys.stderr = devnull

        # Iniciar servidor
        try:
            # Obter documentos por categoria
            docs_dir = find_docs_dir()
            docs_by_category = get_doc_files(docs_dir, DEFAULT_LANGUAGE)

            # Configurar handler com o diretório de documentação
            DocsRequestHandler.docs_dir = docs_dir
            DocsRequestHandler.docs_by_category = docs_by_category
            DocsRequestHandler.current_language = DEFAULT_LANGUAGE

            # Iniciar servidor
            with socketserver.TCPServer((HOST, PORT), DocsRequestHandler) as httpd:
                httpd.serve_forever()
        except Exception:
            # Ignorar exceções em modo daemon
            pass


def get_markdown_title(file_path: Path) -> str:
    """
    Extrai o título de um arquivo Markdown (primeiro cabeçalho H1).

    Args:
        file_path: Caminho para o arquivo Markdown

    Returns:
        Título do documento ou nome do arquivo se não encontrar
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Procurar pelo primeiro cabeçalho H1
        import re

        match = re.search(r"^# (.*?)$", content, re.MULTILINE)
        if match:
            return match.group(1)
    except Exception:
        pass

    # Fallback: usar nome do arquivo
    return file_path.stem.replace("_", " ").title()


def markdown_to_html(content: str, current_language: str = DEFAULT_LANGUAGE) -> str:
    """
    Converte Markdown para HTML com realce de sintaxe e corrige links.

    Args:
        content: Conteúdo Markdown
        current_language: Idioma atual (para construção de links)

    Returns:
        HTML formatado
    """
    if not MARKDOWN_AVAILABLE:
        return f"<pre>{content}</pre>"

    # Configurar extensões com opções específicas para IDs de cabeçalhos
    extensions = [
        "markdown.extensions.tables",
        "markdown.extensions.fenced_code",
        "markdown.extensions.codehilite",
        "markdown.extensions.nl2br",
    ]

    # Configuração da extensão toc para gerar IDs compatíveis para âncoras
    extension_configs = {
        'markdown.extensions.toc': {
            'slugify': lambda text, separator: text.lower()
            .replace(' ', separator)
            .replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            .replace('à', 'a').replace('è', 'e').replace('ì', 'i').replace('ò', 'o').replace('ù', 'u')
            .replace('â', 'a').replace('ê', 'e').replace('î', 'i').replace('ô', 'o').replace('û', 'u')
            .replace('ã', 'a').replace('õ', 'o').replace('ñ', 'n')
            .replace('ç', 'c').replace('ü', 'u')
            .replace('(', '').replace(')', '')
            .replace('[', '').replace(']', '')
            .replace('{', '').replace('}', '')
            .replace(',', '').replace('.', '')
            .replace(':', '').replace(';', '')
            .replace('!', '').replace('?', '')
            .replace('&', 'e').replace('+', 'mais')
            .replace('/', '-').replace('\\', '-')
            .replace('\'', '').replace('"', '')
            .replace('<', '').replace('>', '')
            .replace('|', ''),
            'separator': '-',
            'anchorlink': False,
            'permalink': False
        }
    }

    # Adicionar a extensão toc após definir suas configurações
    extensions.append("markdown.extensions.toc")

    # Converter com extensões e configurações
    html_content = markdown.markdown(
        content,
        extensions=extensions,
        extension_configs=extension_configs
    )

    # Processar os links para trabalhar com o docs server
    link_processor = MarkdownLinkProcessor(current_language)
    html_content = link_processor.process_html(html_content)

    return html_content


def get_language_selector(current_language: str) -> str:
    """
    Gera o seletor de idioma HTML.

    Args:
        current_language: Idioma atualmente selecionado

    Returns:
        HTML para o seletor de idioma
    """
    selector = ['<div class="language-selector">']

    for lang_code, lang_info in LANGUAGES.items():
        active_class = "active" if lang_code == current_language else ""
        selector.append(f'<a href="/?lang={lang_code}" class="lang-option {active_class}" title="{lang_info["name"]}">')
        selector.append(f'{lang_info["flag"]} {lang_info["name"]}</a>')

    selector.append('</div>')
    return "\n".join(selector)


def create_html_page(content_html: str, docs_by_category: Dict[str, List[Path]], active_file: Optional[Path] = None, current_language: str = DEFAULT_LANGUAGE) -> str:
    """
    Cria uma página HTML completa com menu lateral e seletor de idioma.

    Args:
        content_html: Conteúdo HTML principal
        docs_by_category: Documentos agrupados por categoria
        active_file: Arquivo atualmente ativo
        current_language: Idioma atual

    Returns:
        Página HTML completa
    """
    # CSS para a página
    css = """
    :root {
        --primary-color: #3498db;
        --secondary-color: #2980b9;
        --bg-color: #f8f9fa;
        --text-color: #333;
        --sidebar-width: 300px;
        --heading-color: #2c3e50;
        --code-bg: #f7f7f7;
        --link-color: #3498db;
        --border-color: #e1e4e8;
    }
    
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
        margin: 0;
        padding: 0;
        display: flex;
        color: var(--text-color);
        line-height: 1.6;
    }
    
    #sidebar {
        width: var(--sidebar-width);
        height: 100vh;
        position: fixed;
        overflow-y: auto;
        background-color: var(--bg-color);
        border-right: 1px solid var(--border-color);
        padding: 20px 0;
    }
    
    #content {
        margin-left: var(--sidebar-width);
        flex: 1;
        padding: 40px;
        max-width: 1000px;
    }
    
    .sidebar-header {
        padding: 0 20px 20px 20px;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 20px;
    }
    
    .sidebar-title a {
        color: var(--heading-color);
        text-decoration: none;
    }
    
    .sidebar-title a:hover {
        text-decoration: none;
    }
    
    .sidebar-category {
        margin: 15px 0;
        padding: 0 20px;
    }
    
    .category-title {
        font-size: 1.1em;
        font-weight: bold;
        color: var(--heading-color);
        margin-bottom: 10px;
    }
    
    .sidebar-links {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .sidebar-link {
        padding: 8px 10px;
        margin-bottom: 5px;
        display: block;
        color: var(--text-color);
        text-decoration: none;
        border-radius: 5px;
        transition: background-color 0.2s;
    }
    
    .sidebar-link:hover {
        background-color: rgba(0,0,0,0.05);
    }
    
    .sidebar-link.active {
        background-color: var(--primary-color);
        color: white;
    }
    
    .language-selector {
        display: flex;
        justify-content: center;
        padding: 10px 20px;
        border-bottom: 1px solid var(--border-color);
        background-color: var(--bg-color);
    }
    
    .lang-option {
        padding: 5px 10px;
        margin: 0 5px;
        border-radius: 4px;
        text-decoration: none;
        color: var(--text-color);
        font-weight: 500;
        transition: background-color 0.2s;
    }
    
    .lang-option:hover {
        background-color: rgba(0,0,0,0.05);
    }
    
    .lang-option.active {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Content styling */
    h1, h2, h3, h4, h5, h6 {
        color: var(--heading-color);
        margin-top: 1.5em;
        margin-bottom: 0.5em;
    }
    
    h1 {
        font-size: 2em;
        padding-bottom: 0.3em;
        border-bottom: 1px solid var(--border-color);
    }
    
    h2 {
        font-size: 1.5em;
        padding-bottom: 0.3em;
        border-bottom: 1px solid var(--border-color);
    }
    
    a {
        color: var(--link-color);
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    code {
        font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        background-color: var(--code-bg);
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    pre {
        background-color: var(--code-bg);
        padding: 16px;
        border-radius: 6px;
        overflow-x: auto;
        position: relative;
    }
    
    pre code {
        background-color: transparent;
        padding: 0;
    }
    
    blockquote {
        margin: 1em 0;
        padding: 0 1em;
        color: #6a737d;
        border-left: 0.25em solid #dfe2e5;
    }
    
    img {
        max-width: 100%;
    }
    
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
    }
    
    table, th, td {
        border: 1px solid var(--border-color);
    }
    
    th, td {
        padding: 8px 16px;
        text-align: left;
    }
    
    th {
        background-color: var(--bg-color);
    }
    
    tr:nth-child(even) {
        background-color: var(--bg-color);
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 20px;
        margin: 40px 0;
    }
    
    .feature-card {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 20px;
        background-color: var(--bg-color);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    .feature-card h3 {
        margin-top: 0;
        color: var(--primary-color);
    }
    
    @media (max-width: 768px) {
        body {
            flex-direction: column;
        }
        
        #sidebar {
            width: 100%;
            height: auto;
            position: relative;
        }
        
        #content {
            margin-left: 0;
            padding: 20px;
        }
        
        .feature-grid {
            grid-template-columns: 1fr;
        }
    }
    
    .footer-note {
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid var(--border-color);
        font-size: 0.9em;
        color: #6a737d;
    }
    
    .copy-button {
        position: absolute;
        right: 10px;
        top: 5px;
        padding: 3px 8px;
        background-color: rgba(0,0,0,0.1);
        border: none;
        border-radius: 3px;
        cursor: pointer;
        font-size: 12px;
    }
    """

    # JavaScript para a página
    js = """
    document.addEventListener('DOMContentLoaded', function() {
        // Highlight active link
        const activeLink = document.querySelector('.sidebar-link.active');
        if (activeLink) {
            activeLink.scrollIntoView({ block: 'center', behavior: 'smooth' });
        }

        // Add copy buttons to code blocks
        document.querySelectorAll('pre').forEach(function(pre) {
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.textContent = 'Copy';

            // Make pre relative for positioning
            pre.style.position = 'relative';

            // Add hover states
            copyButton.addEventListener('mouseover', function() {
                this.style.backgroundColor = 'rgba(0,0,0,0.2)';
            });
            copyButton.addEventListener('mouseout', function() {
                this.style.backgroundColor = 'rgba(0,0,0,0.1)';
            });

            pre.appendChild(copyButton);

            copyButton.addEventListener('click', function() {
                const code = pre.querySelector('code').textContent;
                navigator.clipboard.writeText(code);

                copyButton.textContent = 'Copied!';
                setTimeout(function() {
                    copyButton.textContent = 'Copy';
                }, 2000);
            });
        });

        // Fix anchor navigation
        function handleAnchorNavigation() {
            // Get the hash from URL
            const hash = window.location.hash;
            if (!hash) return;

            // Remove the '#' character
            const targetId = hash.substring(1);

            // Find the target element
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                // Scroll to the element with a small delay to ensure the page is fully loaded
                setTimeout(() => {
                    targetElement.scrollIntoView({ behavior: 'smooth' });
                }, 100);
            }
        }

        // Handle anchor navigation on page load
        handleAnchorNavigation();

        // Handle anchor navigation when clicking on links within the content
        document.querySelector('#content').addEventListener('click', function(e) {
            const target = e.target;

            // Check if this is a link
            if (target.tagName === 'A' || target.closest('a')) {
                const link = target.tagName === 'A' ? target : target.closest('a');
                const href = link.getAttribute('href');

                // Check if this is an anchor link to the same page
                if (href && href.startsWith('#')) {
                    e.preventDefault();

                    // Update URL hash
                    window.location.hash = href;

                    // Handle navigation
                    handleAnchorNavigation();
                }
            }
        });

        // Also handle hash change events
        window.addEventListener('hashchange', handleAnchorNavigation);
    });
    """

    # Construir seletor de idioma
    language_selector_html = get_language_selector(current_language)

    # Construir menu lateral
    sidebar_html = []
    sidebar_html.append('<div id="sidebar">')
    sidebar_html.append('  <div class="sidebar-header">')

    # Título baseado no idioma
    if current_language == "pt":
        sidebar_title = "Documentação MicroDetect"
    else:
        sidebar_title = "MicroDetect Documentation"

    sidebar_html.append(f'    <h1 class="sidebar-title"><a href="/?file=index.md&lang={current_language}">{sidebar_title}</a></h1>')
    sidebar_html.append("  </div>")

    # Adicionar seletor de idioma
    sidebar_html.append(language_selector_html)

    # Adicionar categorias e links
    for category, doc_files in docs_by_category.items():
        sidebar_html.append(f'  <div class="sidebar-category">')
        sidebar_html.append(f'    <h2 class="category-title">{category}</h2>')
        sidebar_html.append(f'    <ul class="sidebar-links">')

        for doc_file in doc_files:
            title = get_markdown_title(doc_file)
            file_name = doc_file.name
            active_class = "active" if active_file and doc_file.samefile(active_file) else ""

            sidebar_html.append(f'      <li><a class="sidebar-link {active_class}" href="/?file={file_name}&lang={current_language}">{title}</a></li>')

        sidebar_html.append(f"    </ul>")
        sidebar_html.append(f"  </div>")

    sidebar_html.append("</div>")

    # Título da página
    page_title = "MicroDetect Documentation"
    if current_language == "pt":
        page_title = "Documentação MicroDetect"

    # Construir HTML completo
    html = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="UTF-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"  <title>{page_title}</title>",
        f"  <style>{css}</style>",
        '  <link rel="icon" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzNDk4ZGIiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjYiLz48L3N2Zz4=" />',
        "</head>",
        "<body>",
        "\n".join(sidebar_html),
        '  <div id="content">',
        content_html,
        "  </div>",
        f"  <script>{js}</script>",
        "</body>",
        "</html>",
    ]

    return "\n".join(html)


class DocsRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Manipulador de requisições para o servidor de documentação."""

    docs_dir: Path = None
    docs_by_category: Dict[str, List[Path]] = None
    current_language: str = DEFAULT_LANGUAGE

    def do_GET(self):
        """Processar requisições GET."""
        # Analisar URL
        url_parts = urlparse(self.path)
        query_params = parse_qs(url_parts.query)

        # Determinar idioma
        lang = query_params.get("lang", [self.current_language])[0]
        if lang not in LANGUAGES:
            lang = DEFAULT_LANGUAGE

        # Atualizar idioma atual
        self.current_language = lang

        # Determinar qual arquivo exibir
        file_name = query_params.get("file", [None])[0]
        file_path = None

        # Obter documentos para o idioma atual
        self.docs_by_category = get_doc_files(self.docs_dir, lang)

        # Se não há arquivo especificado, procurar por index.md ou usar o primeiro arquivo
        if not file_name:
            index_path = self.docs_dir / lang / "index.md"
            if index_path.exists():
                file_path = index_path
            else:
                # Usar o primeiro arquivo da primeira categoria
                for _, files in self.docs_by_category.items():
                    if files:
                        file_path = files[0]
                        break
        else:
            file_path = self.docs_dir / lang / file_name

        # Se não encontrou arquivo, verificar se existe no idioma padrão
        if not file_path or not file_path.exists():
            if lang != DEFAULT_LANGUAGE:
                default_file_path = self.docs_dir / DEFAULT_LANGUAGE / (file_name or "index.md")
                if default_file_path.exists():
                    file_path = default_file_path

            # Se ainda não encontrou, gerar página de erro
            if not file_path or not file_path.exists():
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                if lang == "pt":
                    error_html = f"<h1>Documentação Não Encontrada</h1><p>O arquivo solicitado não foi encontrado.</p>"
                else:
                    error_html = f"<h1>Documentation Not Found</h1><p>The requested file was not found.</p>"

                page_html = create_html_page(error_html, self.docs_by_category, current_language=lang)
                self.wfile.write(page_html.encode())
                return

        # Ler conteúdo do arquivo
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()

            # Converter para HTML com o novo processador de links
            content_html = markdown_to_html(markdown_content, lang)

            # Criar página completa
            page_html = create_html_page(content_html, self.docs_by_category, file_path, lang)

            # Enviar resposta
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(page_html.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            if lang == "pt":
                error_html = f"<h1>Erro</h1><p>Ocorreu um erro ao processar a documentação: {str(e)}</p>"
            else:
                error_html = f"<h1>Error</h1><p>An error occurred while processing the documentation: {str(e)}</p>"

            page_html = create_html_page(error_html, self.docs_by_category, current_language=lang)
            self.wfile.write(page_html.encode())


def _check_dependencies():
    """Verifica se as dependências estão instaladas."""
    global MARKDOWN_AVAILABLE
    global highlight, HtmlFormatter, get_lexer_by_name

    missing_deps = []

    if not MARKDOWN_AVAILABLE:
        missing_deps.extend(["markdown", "pygments"])

    if missing_deps:
        if COLORS_AVAILABLE:
            print(f"{WARNING}Missing dependencies for documentation server:{RESET}")
            print(f"{INFO}pip install {' '.join(missing_deps)}{RESET}")
        else:
            print(f"Missing dependencies for documentation server:")
            print(f"pip install {' '.join(missing_deps)} --index-url https://pypi.org/simple")

        install = input("Would you like to install these dependencies now? (y/n): ").lower().strip()
        if install == "y" or install == "yes":
            try:
                import subprocess

                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_deps)
                print(
                    f"{SUCCESS}Dependencies installed successfully!{RESET}"
                    if COLORS_AVAILABLE
                    else "Dependencies installed successfully!"
                )

                # Reimport
                import markdown
                from pygments import highlight
                from pygments.formatters import HtmlFormatter
                from pygments.lexers import get_lexer_by_name

                MARKDOWN_AVAILABLE = True

                return True
            except Exception as e:
                if COLORS_AVAILABLE:
                    print(f"{ERROR}Failed to install dependencies: {str(e)}{RESET}")
                else:
                    print(f"Failed to install dependencies: {str(e)}")
                return False
        else:
            return False

    return True


def start_docs_server(language=None):
    """
    Inicia o servidor de documentação.

    Args:
        language: Código do idioma para iniciar (ex: 'en', 'pt')

    Returns:
        True se o servidor iniciou com sucesso, False caso contrário
    """

    print(f"Idioma Selecionado: {language}")
    # Definir idioma padrão se especificado
    global DEFAULT_LANGUAGE
    if language and language in LANGUAGES:
        DEFAULT_LANGUAGE = language

    # Verificar dependências
    if not _check_dependencies():
        if COLORS_AVAILABLE:
            print(f"{WARNING}Starting documentation server with limited functionality.{RESET}")
        else:
            print(f"Starting documentation server with limited functionality.")

    # Encontrar diretório de documentação
    docs_dir = find_docs_dir()
    if not docs_dir.exists():
        if COLORS_AVAILABLE:
            print(f"{ERROR}Documentation directory not found at {docs_dir}{RESET}")
        else:
            print(f"Documentation directory not found at {docs_dir}")
        return False

    # Verificar se existem diretórios de idioma
    any_language_exists = False
    for lang in LANGUAGES.values():
        lang_dir = docs_dir / lang["dir"]
        if lang_dir.exists() and lang_dir.is_dir():
            any_language_exists = True
            break

    if not any_language_exists:
        if COLORS_AVAILABLE:
            print(f"{WARNING}No language directories found. Creating basic structure...{RESET}")
        else:
            print(f"No language directories found. Creating basic structure...")

        # Criar diretórios de idioma básicos
        for lang in LANGUAGES.values():
            lang_dir = docs_dir / lang["dir"]
            lang_dir.mkdir(exist_ok=True)

            # Criar index.md básico para cada idioma
            index_path = lang_dir / "index.md"
            if not index_path.exists():
                with open(index_path, "w", encoding="utf-8") as f:
                    if lang["dir"] == "en":
                        f.write("# MicroDetect Documentation\n\n")
                        f.write("Welcome to MicroDetect documentation. Please add more documentation files to the docs/en directory.\n")
                    else:
                        f.write("# Documentação do MicroDetect\n\n")
                        f.write("Bem-vindo à documentação do MicroDetect. Por favor, adicione mais arquivos de documentação ao diretório docs/pt.\n")

    # Obter documentos por categoria
    docs_by_category = get_doc_files(docs_dir, DEFAULT_LANGUAGE)

    # Configurar handler com o diretório de documentação
    DocsRequestHandler.docs_dir = docs_dir
    DocsRequestHandler.docs_by_category = docs_by_category
    DocsRequestHandler.current_language = DEFAULT_LANGUAGE

    # Iniciar servidor
    try:
        with socketserver.TCPServer((HOST, PORT), DocsRequestHandler) as httpd:
            server_url = f"http://{HOST}:{PORT}"

            if COLORS_AVAILABLE:
                print(f"{SUCCESS}Documentation server started at {BRIGHT}{server_url}{RESET}")
                print(f"{INFO}Language: {LANGUAGES[DEFAULT_LANGUAGE]['name']} {LANGUAGES[DEFAULT_LANGUAGE]['flag']}{RESET}")
                print(f"{INFO}Press Ctrl+C to stop the server{RESET}")
            else:
                print(f"Documentation server started at {server_url}")
                print(f"Language: {LANGUAGES[DEFAULT_LANGUAGE]['name']} {LANGUAGES[DEFAULT_LANGUAGE]['flag']}")
                print(f"Press Ctrl+C to stop the server")

            # Iniciar navegador em uma thread separada
            threading.Thread(target=lambda: open_browser(server_url)).start()

            # Iniciar servidor
            httpd.serve_forever()

    except KeyboardInterrupt:
        if COLORS_AVAILABLE:
            print(f"{WARNING}Server stopped.{RESET}")
        else:
            print(f"Server stopped.")
        return True
    except Exception as e:
        if COLORS_AVAILABLE:
            print(f"{ERROR}Error starting documentation server: {str(e)}{RESET}")
        else:
            print(f"Error starting documentation server: {str(e)}")
        return False


def open_browser(url: str):
    """
    Abre o navegador com uma URL após um pequeno atraso.
    Inclui suporte especial para WSL.

    Args:
        url: URL para abrir
    """
    # Aguardar um momento para o servidor iniciar
    time.sleep(1.5)

    # Detectar WSL
    is_wsl = False
    try:
        with open("/proc/version", "r") as f:
            if "microsoft" in f.read().lower():
                is_wsl = True
    except:
        pass

    if is_wsl:
        # Estamos no WSL, use o explorer.exe do Windows
        try:
            import subprocess

            subprocess.run(["cmd.exe", "/c", "start", url], check=False)
            return True
        except Exception as e:
            # Se falhar, tente uma alternativa
            try:
                subprocess.run(["explorer.exe", url], check=False)
                return True
            except Exception:
                pass
    else:
        # Para outros sistemas, tente o método padrão
        try:
            if webbrowser.open(url):
                return True
        except Exception:
            pass

    # Se todas as tentativas falharem, apenas exiba a URL
    if COLORS_AVAILABLE:
        print(f"{WARNING}Não foi possível abrir o navegador automaticamente.{RESET}")
        print(f"{SUCCESS}Por favor, acesse manualmente: {BRIGHT}{url}{RESET}")
    else:
        print(f"Não foi possível abrir o navegador automaticamente.")
        print(f"Por favor, acesse manualmente: {url}")

    return False


if __name__ == "__main__":
    import argparse

    # Configurar argumentos de linha de comando
    parser = argparse.ArgumentParser(description="MicroDetect Documentation Server")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (background process)")
    parser.add_argument("--port", type=int, help="Port for the server")
    parser.add_argument("--lang", type=str, choices=list(LANGUAGES.keys()), default=DEFAULT_LANGUAGE,
                        help="Default language for documentation")

    args = parser.parse_args()

    if args.daemon:
        run_as_daemon(args.port, args.lang)
    else:
        # Iniciar servidor normalmente
        start_docs_server(args.lang)