"""
Módulo para servir documentação como uma página web com menu lateral.
"""

import http.server
import os
import socketserver
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

# Importar as constantes de cores do módulo existente
from microdetect.utils.colors import (
    BRIGHT,
    COLORS_AVAILABLE,
    ERROR,
    INFO,
    RESET,
    SUCCESS,
    WARNING,
)

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

    # Se não encontrar, criar um diretório temporário
    import tempfile

    temp_dir = Path(tempfile.mkdtemp(prefix="microdetect_docs_"))
    temp_docs = temp_dir / "docs"
    temp_docs.mkdir(exist_ok=True)

    with open(temp_docs / "index.md", "w") as f:
        f.write("# MicroDetect Documentation\n\n")
        f.write("Documentation directory not found. Please make sure the 'docs' directory exists.\n")

    return temp_docs


def get_doc_files(docs_dir: Path) -> Dict[str, List[Path]]:
    """
    Obtém a lista de arquivos de documentação organizados por categoria.

    Args:
        docs_dir: Diretório de documentação

    Returns:
        Dicionário com categorias e arquivos
    """
    # Categorias e ordem de exibição
    categories = {
        "Getting Started": ["installation_guide.md", "troubleshooting.md"],
        "Features": [],
        "Updates": ["update_system.md", "aws_codeartifact_setup.md", "update_and_release_model.md"],
        "Configuration": ["advanced_configuration.md"],
        "Development": ["development_guide.md"],
    }

    # Arquivos não categorizados
    uncategorized = []

    # Mapear arquivos para suas categorias
    for file in docs_dir.glob("*.md"):
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
                categories["Getting Started"].append(file_name)
            elif "config" in file_name:
                categories["Configuration"].append(file_name)
            elif "develop" in file_name or "contrib" in file_name:
                categories["Development"].append(file_name)
            elif "update" in file_name or "release" in file_name:
                categories["Updates"].append(file_name)
            else:
                categories["Features"].append(file_name)

    # Remover categorias vazias
    result = {k: [] for k in categories.keys()}

    # Preencher com os caminhos completos
    for category, file_names in categories.items():
        for file_name in file_names:
            file_path = docs_dir / file_name
            if file_path.exists():
                result[category].append(file_path)

    # Remover categorias vazias
    result = {k: v for k, v in result.items() if v}

    return result


"""
Implementação de execução em background para o servidor de documentação.
Estas funções devem ser adicionadas ao arquivo docs_server.py
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


def start_server_in_background(port=None):
    """
    Inicia o servidor de documentação em background.

    Args:
        port: Porta para o servidor (opcional)

    Returns:
        Dicionário com informações do processo iniciado
    """
    server_script = __file__

    # Criar comando com argumentos
    cmd = [sys.executable, server_script, "--daemon"]
    if port:
        cmd.extend(["--port", str(port)])

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


def run_as_daemon(port=None):
    """
    Executa o servidor como um daemon (processo em background).

    Args:
        port: Porta a ser usada pelo servidor
    """
    global PORT
    if port:
        PORT = port

    # Redirecionar saída para /dev/null ou NUL
    with open(os.devnull, "w") as devnull:
        # Substituir stdout e stderr
        sys.stdout = devnull
        sys.stderr = devnull

        # Iniciar servidor
        try:
            # Obter documentos por categoria
            docs_dir = find_docs_dir()
            docs_by_category = get_doc_files(docs_dir)

            # Configurar handler com o diretório de documentação
            DocsRequestHandler.docs_dir = docs_dir
            DocsRequestHandler.docs_by_category = docs_by_category

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


def markdown_to_html(content: str) -> str:
    """
    Converte Markdown para HTML com realce de sintaxe.

    Args:
        content: Conteúdo Markdown

    Returns:
        HTML formatado
    """
    if not MARKDOWN_AVAILABLE:
        return f"<pre>{content}</pre>"

    # Configurar extensões
    extensions = [
        "markdown.extensions.tables",
        "markdown.extensions.fenced_code",
        "markdown.extensions.codehilite",
        "markdown.extensions.toc",
        "markdown.extensions.nl2br",
    ]

    # Converter com extensões
    return markdown.markdown(content, extensions=extensions)


def create_html_page(content_html: str, docs_by_category: Dict[str, List[Path]], active_file: Optional[Path] = None) -> str:
    """
    Cria uma página HTML completa com menu lateral.

    Args:
        content_html: Conteúdo HTML principal
        docs_by_category: Documentos agrupados por categoria
        active_file: Arquivo atualmente ativo

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
            copyButton.style.position = 'absolute';
            copyButton.style.right = '10px';
            copyButton.style.top = '5px';
            copyButton.style.padding = '3px 8px';
            copyButton.style.backgroundColor = 'rgba(0,0,0,0.1)';
            copyButton.style.border = 'none';
            copyButton.style.borderRadius = '3px';
            copyButton.style.cursor = 'pointer';
            copyButton.style.fontSize = '12px';
            
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
    });
    """

    # Construir menu lateral
    sidebar_html = []
    sidebar_html.append('<div id="sidebar">')
    sidebar_html.append('  <div class="sidebar-header">')
    sidebar_html.append('    <h1 class="sidebar-title"><a href="/?file=index.md">MicroDetect Docs</a></h1>')
    sidebar_html.append("  </div>")

    # Adicionar categorias e links
    for category, doc_files in docs_by_category.items():
        sidebar_html.append(f'  <div class="sidebar-category">')
        sidebar_html.append(f'    <h2 class="category-title">{category}</h2>')
        sidebar_html.append(f'    <ul class="sidebar-links">')

        for doc_file in doc_files:
            title = get_markdown_title(doc_file)
            file_name = doc_file.name
            active_class = "active" if active_file and doc_file.samefile(active_file) else ""

            sidebar_html.append(f'      <li><a class="sidebar-link {active_class}" href="/?file={file_name}">{title}</a></li>')

        sidebar_html.append(f"    </ul>")
        sidebar_html.append(f"  </div>")

    sidebar_html.append("</div>")

    # Construir HTML completo
    html = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="UTF-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "  <title>MicroDetect Documentation</title>",
        f"  <style>{css}</style>",
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

    def do_GET(self):
        """Processar requisições GET."""
        # Analisar URL
        url_parts = urlparse(self.path)
        query_params = parse_qs(url_parts.query)

        # Determinar qual arquivo exibir
        file_name = query_params.get("file", [None])[0]
        file_path = None

        # Se não há arquivo especificado, procurar por index.md ou usar o primeiro arquivo
        if not file_name:
            index_path = self.docs_dir / "index.md"
            if index_path.exists():
                file_path = index_path
            else:
                # Usar o primeiro arquivo da primeira categoria
                for _, files in self.docs_by_category.items():
                    if files:
                        file_path = files[0]
                        break
        else:
            file_path = self.docs_dir / file_name

        # Se não encontrou arquivo, gerar página de erro
        if not file_path or not file_path.exists():
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            error_html = f"<h1>Documentation Not Found</h1><p>The requested file was not found.</p>"
            page_html = create_html_page(error_html, self.docs_by_category)
            self.wfile.write(page_html.encode())
            return

        # Ler conteúdo do arquivo
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()

            # Converter para HTML
            content_html = markdown_to_html(markdown_content)

            # Criar página completa
            page_html = create_html_page(content_html, self.docs_by_category, file_path)

            # Enviar resposta
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(page_html.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            error_html = f"<h1>Error</h1><p>An error occurred while processing the documentation: {str(e)}</p>"
            page_html = create_html_page(error_html, self.docs_by_category)
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


def start_docs_server():
    """
    Inicia o servidor de documentação.

    Returns:
        True se o servidor iniciou com sucesso, False caso contrário
    """
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

    # Obter documentos por categoria
    docs_by_category = get_doc_files(docs_dir)

    # Configurar handler com o diretório de documentação
    DocsRequestHandler.docs_dir = docs_dir
    DocsRequestHandler.docs_by_category = docs_by_category

    # Iniciar servidor
    try:
        with socketserver.TCPServer((HOST, PORT), DocsRequestHandler) as httpd:
            server_url = f"http://{HOST}:{PORT}"

            if COLORS_AVAILABLE:
                print(f"{SUCCESS}Documentation server started at {BRIGHT}{server_url}{RESET}")
                print(f"{INFO}Press Ctrl+C to stop the server{RESET}")
            else:
                print(f"Documentation server started at {server_url}")
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

    args = parser.parse_args()

    if args.daemon:
        run_as_daemon(args.port)
    else:
        # Iniciar servidor normalmente
        start_docs_server()
