"""
Módulo para servir documentação como uma página web com menu lateral organizado e suporte a múltiplos idiomas.
"""

import http.server
import socketserver
import sys
import threading
import time
import webbrowser
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
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


class DocPage:
    """Representa uma página de documentação com metadados."""

    def __init__(self, path: Path, title: str = None, order: int = 999,
                 category: str = None, subcategory: str = None, icon: str = None):
        self.path = path
        self.title = title or self._extract_title()
        self.name = path.name
        self.order = order
        self.category = category
        self.subcategory = subcategory
        self.icon = icon or self._get_default_icon()

    def _extract_title(self) -> str:
        """Extrai o título do arquivo Markdown (primeiro cabeçalho H1)."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read()

            # Procurar pelo primeiro cabeçalho H1
            match = re.search(r"^# (.*?)$", content, re.MULTILINE)
            if match:
                return match.group(1)
        except Exception:
            pass

        # Fallback: usar nome do arquivo
        return self.path.stem.replace("_", " ").title()

    def _get_default_icon(self) -> str:
        """Retorna um ícone padrão baseado no nome do arquivo."""
        name = self.path.stem.lower()

        # Mapeamento de palavras-chave para ícones
        icon_map = {
            "install": "📥",
            "setup": "🔧",
            "config": "⚙️",
            "start": "🚀",
            "guide": "📖",
            "tutorial": "🎓",
            "develop": "👨‍💻",
            "code": "💻",
            "visual": "🖼️",
            "train": "🏋️",
            "model": "🧠",
            "data": "📊",
            "dataset": "📁",
            "error": "❌",
            "trouble": "🔍",
            "analysis": "📈",
            "benchmark": "⏱️",
            "compare": "⚖️",
            "update": "🔄",
            "report": "📝",
            "stat": "📉",
            "index": "🏠",
        }

        # Verificar se o nome contém alguma das palavras-chave
        for key, icon in icon_map.items():
            if key in name:
                return icon

        # Ícone padrão para outros casos
        return "📄"

    def get_metadata(self) -> Dict[str, Any]:
        """Extrai metadados do conteúdo Markdown."""
        metadata = {
            "order": self.order,
            "category": self.category,
            "subcategory": self.subcategory,
            "icon": self.icon
        }

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read(2000)  # Ler apenas os primeiros 2000 caracteres para metadados

            # Procurar por metadados em comentários HTML especiais
            meta_pattern = r"<!--\s*meta:\s*(.*?)\s*-->"
            matches = re.findall(meta_pattern, content, re.DOTALL)

            if matches:
                for match in matches:
                    # Procurar por pares chave:valor
                    for line in match.strip().split("\n"):
                        if ":" in line:
                            key, value = [x.strip() for x in line.split(":", 1)]
                            if key in metadata:
                                # Converter order para inteiro se aplicável
                                if key == "order" and value.isdigit():
                                    metadata[key] = int(value)
                                else:
                                    metadata[key] = value
        except Exception:
            pass

        return metadata


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
        # Padrão para capturar links que apontam para arquivos .md
        pattern = r'<a\s+href=["\']([^"\'#]+\.md)(#[^"\']+)?["\']([^>]*)>(.*?)</a>'

        def replace_link(match):
            # Extrai as partes do link
            link_path = match.group(1)
            anchor = match.group(2) or ""
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
    # Lista de possíveis locais para procurar os documentos
    search_paths = []

    # 1. Buscar a partir do diretório atual
    current_dir = Path.cwd()
    search_paths.append(current_dir / "docs")

    # 2. Buscar a partir do diretório home do usuário
    home_dir = Path.home()
    search_paths.append(home_dir / ".microdetect" / "docs")

    # 3. Buscar a partir do diretório do pacote (diretório onde o módulo está instalado)
    package_dir = Path(__file__).parent.parent.parent
    search_paths.append(package_dir / "docs")

    # 4. Buscar nas pastas de compartilhamento de dados padrão da instalação
    try:
        import site
        import sys

        # Diretórios do site-packages para instalações padrão
        for site_dir in site.getsitepackages():
            share_docs_dir = Path(site_dir).parent / "share/microdetect/docs"
            search_paths.append(share_docs_dir)

            # Verificar também em share/microdetect
            share_dir = Path(site_dir).parent / "share/microdetect"
            search_paths.append(share_dir)

        # Diretório específico para instalações Conda
        if "conda" in sys.prefix.lower() or "miniconda" in sys.prefix.lower():
            conda_share_dir = Path(sys.prefix) / "share/microdetect/docs"
            search_paths.append(conda_share_dir)

        # Verificar também em userbase para instalações por usuário
        user_base = site.USER_BASE
        share_docs_dir = Path(user_base) / "share/microdetect/docs"
        search_paths.append(share_docs_dir)

    except (ImportError, AttributeError):
        pass

    # Verificar cada caminho e retornar o primeiro existente
    for path in search_paths:
        if path.exists() and path.is_dir():
            # Verificar se pelo menos um arquivo .md existe no caminho ou seus subdiretórios
            md_files = list(path.glob("**/*.md"))
            if md_files:
                return path

    # Se nenhum diretório existente foi encontrado, criar um temporário
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
                f.write("\nSearched in the following locations:\n")
                for path in search_paths:
                    f.write(f"- {path}\n")
            else:
                f.write("# Documentação do MicroDetect\n\n")
                f.write(
                    "Diretório de documentação não encontrado. Por favor, certifique-se de que o diretório 'docs' existe.\n"
                )
                f.write("\nBuscado nas seguintes localizações:\n")
                for path in search_paths:
                    f.write(f"- {path}\n")

    return temp_docs


def organize_documentation(docs_dir: Path, language: str = DEFAULT_LANGUAGE) -> Tuple[Dict[str, Dict[str, List[DocPage]]], Dict[str, DocPage]]:
    """
    Organiza a documentação em uma estrutura hierárquica para facilitar a navegação.

    Args:
        docs_dir: Diretório de documentação
        language: Código do idioma (ex: 'en', 'pt')

    Returns:
        Tupla contendo (dicionário hierárquico de documentos, mapa de arquivos)
    """
    # Verificar se o diretório do idioma existe
    lang_dir = docs_dir / language
    if not lang_dir.exists() or not lang_dir.is_dir():
        # Fallback para o idioma padrão se o diretório do idioma solicitado não existir
        language = DEFAULT_LANGUAGE
        lang_dir = docs_dir / language

        # Se ainda não existir, retornar vazio
        if not lang_dir.exists() or not lang_dir.is_dir():
            return {}, {}

    # Definir categorias com ordem e subcategorias (baseado na estrutura do index.md)
    if language == "en":
        predefined_categories = {
            "Getting Started": {"order": 10, "icon": "🚀", "subcategories": {}},
            "Core Workflow": {"order": 20, "icon": "⚙️", "subcategories": {
                "Image Preparation": {"order": 10, "icon": "🖼️"},
                "Annotation": {"order": 20, "icon": "🏷️"},
                "Dataset Management": {"order": 30, "icon": "📊"},
                "Training": {"order": 40, "icon": "🧠"},
                "Evaluation": {"order": 50, "icon": "📈"}
            }},
            "Advanced Analysis": {"order": 30, "icon": "🔬", "subcategories": {
                "Model Evaluation": {"order": 10, "icon": "📊"},
                "Error Analysis": {"order": 20, "icon": "🔍"},
                "Visualization": {"order": 30, "icon": "📊"},
                "Statistical Analysis": {"order": 40, "icon": "📉"},
                "Batch Processing": {"order": 50, "icon": "🔄"}
            }},
            "Configuration": {"order": 40, "icon": "⚙️", "subcategories": {}},
            "Development": {"order": 50, "icon": "👨‍💻", "subcategories": {}}
        }
    else:  # Portuguese
        predefined_categories = {
            "Primeiros Passos": {"order": 10, "icon": "🚀", "subcategories": {}},
            "Fluxo de Trabalho": {"order": 20, "icon": "⚙️", "subcategories": {
                "Preparação de Imagens": {"order": 10, "icon": "🖼️"},
                "Anotação": {"order": 20, "icon": "🏷️"},
                "Gerenciamento de Dataset": {"order": 30, "icon": "📊"},
                "Treinamento": {"order": 40, "icon": "🧠"},
                "Avaliação": {"order": 50, "icon": "📈"}
            }},
            "Análise Avançada": {"order": 30, "icon": "🔬", "subcategories": {
                "Avaliação de Modelos": {"order": 10, "icon": "📊"},
                "Análise de Erros": {"order": 20, "icon": "🔍"},
                "Visualização": {"order": 30, "icon": "📊"},
                "Análise Estatística": {"order": 40, "icon": "📉"},
                "Processamento em Lote": {"order": 50, "icon": "🔄"}
            }},
            "Configuração": {"order": 40, "icon": "⚙️", "subcategories": {}},
            "Desenvolvimento": {"order": 50, "icon": "👨‍💻", "subcategories": {}}
        }

    # Mapeamento de palavras-chave para categorias e subcategorias
    keyword_mappings = {
        "en": {
            "install": ("Getting Started", None),
            "troubleshoot": ("Getting Started", None),
            "image_conversion": ("Core Workflow", "Image Preparation"),
            "preprocess": ("Core Workflow", "Image Preparation"),
            "annotation": ("Core Workflow", "Annotation"),
            "dataset": ("Core Workflow", "Dataset Management"),
            "data_augmentation": ("Core Workflow", "Dataset Management"),
            "train": ("Core Workflow", "Training"),
            "checkpoint": ("Core Workflow", "Training"),
            "hyperparameter": ("Core Workflow", "Training"),
            "evaluation": ("Core Workflow", "Evaluation"),
            "error_analysis": ("Advanced Analysis", "Error Analysis"),
            "visualization": ("Advanced Analysis", "Visualization"),
            "report": ("Advanced Analysis", "Visualization"),
            "dashboard": ("Advanced Analysis", "Visualization"),
            "statistical": ("Advanced Analysis", "Statistical Analysis"),
            "density": ("Advanced Analysis", "Statistical Analysis"),
            "distribution": ("Advanced Analysis", "Statistical Analysis"),
            "batch": ("Advanced Analysis", "Batch Processing"),
            "parallel": ("Advanced Analysis", "Batch Processing"),
            "config": ("Configuration", None),
            "aws": ("Configuration", None),
            "environment": ("Configuration", None),
            "development": ("Development", None),
            "contributing": ("Development", None),
            "architecture": ("Development", None),
        },
        "pt": {
            "install": ("Primeiros Passos", None),
            "troubleshoot": ("Primeiros Passos", None),
            "image_conversion": ("Fluxo de Trabalho", "Preparação de Imagens"),
            "preprocess": ("Fluxo de Trabalho", "Preparação de Imagens"),
            "annotation": ("Fluxo de Trabalho", "Anotação"),
            "dataset": ("Fluxo de Trabalho", "Gerenciamento de Dataset"),
            "data_augmentation": ("Fluxo de Trabalho", "Gerenciamento de Dataset"),
            "train": ("Fluxo de Trabalho", "Treinamento"),
            "checkpoint": ("Fluxo de Trabalho", "Treinamento"),
            "hyperparameter": ("Fluxo de Trabalho", "Treinamento"),
            "evaluation": ("Fluxo de Trabalho", "Avaliação"),
            "error_analysis": ("Análise Avançada", "Análise de Erros"),
            "visualization": ("Análise Avançada", "Visualização"),
            "report": ("Análise Avançada", "Visualização"),
            "dashboard": ("Análise Avançada", "Visualização"),
            "statistical": ("Análise Avançada", "Análise Estatística"),
            "density": ("Análise Avançada", "Análise Estatística"),
            "distribution": ("Análise Avançada", "Análise Estatística"),
            "batch": ("Análise Avançada", "Processamento em Lote"),
            "parallel": ("Análise Avançada", "Processamento em Lote"),
            "config": ("Configuração", None),
            "aws": ("Configuração", None),
            "environment": ("Configuração", None),
            "development": ("Desenvolvimento", None),
            "contributing": ("Desenvolvimento", None),
            "architecture": ("Desenvolvimento", None),
        }
    }

    # Preparar estrutura de resultado
    result = {category: {"order": info["order"], "icon": info["icon"], "subcategories": {}}
              for category, info in predefined_categories.items()}
    for category, info in predefined_categories.items():
        for subcategory, subinfo in info["subcategories"].items():
            result[category]["subcategories"][subcategory] = {
                "order": subinfo["order"],
                "icon": subinfo["icon"],
                "pages": []
            }
        # Também adicionamos uma lista de páginas diretamente na categoria
        result[category]["pages"] = []

    # Mapa de arquivos para referência rápida
    file_map = {}

    # Processar cada arquivo Markdown no diretório do idioma
    for file_path in sorted(lang_dir.glob("*.md")):
        if file_path.name == "index.md":
            # Adicionar a página inicial ao mapa de arquivos, mas não ao menu
            doc_page = DocPage(file_path, order=0, icon="🏠")
            file_map[file_path.name] = doc_page
            continue

        # Criar objeto de página
        doc_page = DocPage(file_path)

        # Extrair metadados
        metadata = doc_page.get_metadata()
        doc_page.order = metadata["order"]
        doc_page.icon = metadata["icon"]

        # Tentar categorizar com base no nome do arquivo
        categorized = False
        file_stem = file_path.stem.lower()

        # Verificar se o arquivo corresponde a algum mapeamento de palavra-chave
        for keyword, (category, subcategory) in keyword_mappings[language].items():
            if keyword in file_stem:
                if category in result and subcategory is None:
                    # Adicionar à categoria principal
                    doc_page.category = category
                    result[category]["pages"].append(doc_page)
                    categorized = True
                    break
                elif category in result and subcategory in result[category]["subcategories"]:
                    # Adicionar à subcategoria
                    doc_page.category = category
                    doc_page.subcategory = subcategory
                    result[category]["subcategories"][subcategory]["pages"].append(doc_page)
                    categorized = True
                    break

        # Se não foi categorizado por palavra-chave, usar metadados ou padrão
        if not categorized:
            category = metadata["category"]
            subcategory = metadata["subcategory"]

            # Verificar se a categoria e subcategoria existem
            if category in result:
                if subcategory and subcategory in result[category]["subcategories"]:
                    # Adicionar à subcategoria
                    doc_page.category = category
                    doc_page.subcategory = subcategory
                    result[category]["subcategories"][subcategory]["pages"].append(doc_page)
                else:
                    # Adicionar à categoria principal
                    doc_page.category = category
                    result[category]["pages"].append(doc_page)
            else:
                # Categoria padrão: Getting Started / Primeiros Passos
                default_category = "Getting Started" if language == "en" else "Primeiros Passos"
                doc_page.category = default_category
                result[default_category]["pages"].append(doc_page)

        # Adicionar ao mapa de arquivos
        file_map[file_path.name] = doc_page

    # Ordenar as páginas em cada categoria e subcategoria
    for category, category_info in result.items():
        category_info["pages"] = sorted(category_info["pages"], key=lambda p: (p.order, p.title))
        for subcategory, subcategory_info in category_info["subcategories"].items():
            subcategory_info["pages"] = sorted(subcategory_info["pages"], key=lambda p: (p.order, p.title))

    # Remover categorias e subcategorias vazias
    for category in list(result.keys()):
        if not result[category]["pages"] and not any(subcategory_info["pages"] for subcategory_info in result[category]["subcategories"].values()):
            del result[category]
        else:
            # Remover subcategorias vazias
            for subcategory in list(result[category]["subcategories"].keys()):
                if not result[category]["subcategories"][subcategory]["pages"]:
                    del result[category]["subcategories"][subcategory]

    # Ordenar as categorias
    result = {k: result[k] for k in sorted(result.keys(), key=lambda c: predefined_categories.get(c, {}).get("order", 999))}

    return result, file_map


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
        "markdown.extensions.toc": {
            "slugify": lambda text, separator: text.lower()
            .replace(" ", separator)
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("à", "a")
            .replace("è", "e")
            .replace("ì", "i")
            .replace("ò", "o")
            .replace("ù", "u")
            .replace("â", "a")
            .replace("ê", "e")
            .replace("î", "i")
            .replace("ô", "o")
            .replace("û", "u")
            .replace("ã", "a")
            .replace("õ", "o")
            .replace("ñ", "n")
            .replace("ç", "c")
            .replace("ü", "u")
            .replace("(", "")
            .replace(")", "")
            .replace("[", "")
            .replace("]", "")
            .replace("{", "")
            .replace("}", "")
            .replace(",", "")
            .replace(".", "")
            .replace(":", "")
            .replace(";", "")
            .replace("!", "")
            .replace("?", "")
            .replace("&", "e")
            .replace("+", "mais")
            .replace("/", "-")
            .replace("\\", "-")
            .replace("'", "")
            .replace('"', "")
            .replace("<", "")
            .replace(">", "")
            .replace("|", ""),
            "separator": "-",
            "anchorlink": False,
            "permalink": False,
        }
    }

    # Adicionar a extensão toc após definir suas configurações
    extensions.append("markdown.extensions.toc")

    # Converter com extensões e configurações
    html_content = markdown.markdown(content, extensions=extensions, extension_configs=extension_configs)

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

    selector.append("</div>")
    return "\n".join(selector)


def create_html_page(
    content_html: str,
    doc_structure: Dict[str, Dict[str, Any]],
    file_map: Dict[str, DocPage],
    active_file: Optional[Path] = None,
    current_language: str = DEFAULT_LANGUAGE,
) -> str:
    """
    Cria uma página HTML completa com menu lateral hierárquico e seletor de idioma.

    Args:
        content_html: Conteúdo HTML principal
        doc_structure: Estrutura hierárquica de documentos
        file_map: Mapa de arquivos para referência rápida
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
        --accent-color: #e74c3c;
        --bg-color: #f8f9fa;
        --bg-secondary: #ffffff;
        --text-color: #333;
        --text-secondary: #666;
        --sidebar-width: 320px;
        --heading-color: #2c3e50;
        --code-bg: #f7f7f7;
        --link-color: #3498db;
        --border-color: #e1e4e8;
        --shadow-color: rgba(0, 0, 0, 0.1);
        --card-shadow: 0 4px 6px var(--shadow-color);
        --card-shadow-hover: 0 10px 15px var(--shadow-color);
        --transition-speed: 0.3s;
    }
    
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
        margin: 0;
        padding: 0;
        display: flex;
        color: var(--text-color);
        line-height: 1.6;
        background-color: var(--bg-color);
    }
    
    #sidebar {
        width: var(--sidebar-width);
        height: 100vh;
        position: fixed;
        overflow-y: auto;
        background-color: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
        box-shadow: 2px 0 10px var(--shadow-color);
        z-index: 100;
        transition: transform var(--transition-speed);
    }
    
    #content {
        margin-left: var(--sidebar-width);
        flex: 1;
        padding: 40px;
        max-width: 1000px;
        background-color: var(--bg-secondary);
        min-height: 100vh;
        box-shadow: 0 0 20px var(--shadow-color);
    }
    
    .sidebar-header {
        padding: 20px;
        border-bottom: 1px solid var(--border-color);
        background-color: var(--bg-secondary);
        position: sticky;
        top: 0;
        z-index: 10;
    }
    
    .logo-container {
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    .logo-image {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        box-shadow: var(--card-shadow);
        transition: transform var(--transition-speed);
    }
    
    .logo-image:hover {
        transform: scale(1.05);
    }
    
    .sidebar-title {
        margin-top: 16px;
        margin-bottom: 0;
        text-align: center;
        font-size: 1.4em;
    }
    
    .sidebar-title a {
        color: var(--heading-color);
        text-decoration: none;
        transition: color 0.2s;
    }
    
    .sidebar-title a:hover {
        color: var(--primary-color);
        text-decoration: none;
    }
    
    .sidebar-category {
        margin: 10px 0;
    }
    
    .category-header {
        padding: 10px 15px;
        cursor: pointer;
        display: flex;
        align-items: center;
        background-color: var(--bg-color);
        border-radius: 4px;
        margin: 5px 10px;
        transition: background-color 0.2s;
    }
    
    .category-header:hover {
        background-color: rgba(0,0,0,0.05);
    }
    
    .category-header.active {
        background-color: var(--primary-color);
        color: white;
    }
    
    .category-icon {
        margin-right: 10px;
        font-size: 1.2em;
    }
    
    .category-title {
        font-size: 1.1em;
        font-weight: bold;
        flex-grow: 1;
    }
    
    .category-toggle {
        transition: transform 0.3s;
    }
    
    .category-toggle.expanded {
        transform: rotate(90deg);
    }
    
    .category-content {
        margin-left: 25px;
        overflow: hidden;
        max-height: 0;
        transition: max-height 0.3s ease-out;
    }
    
    .category-content.expanded {
        max-height: 5000px;
    }
    
    .subcategory {
        margin: 10px 0;
    }
    
    .subcategory-header {
        padding: 8px 15px;
        cursor: pointer;
        display: flex;
        align-items: center;
        border-radius: 4px;
        margin: 2px 0;
        transition: background-color 0.2s;
    }
    
    .subcategory-header:hover {
        background-color: rgba(0,0,0,0.05);
    }
    
    .subcategory-icon {
        margin-right: 10px;
    }
    
    .subcategory-title {
        font-size: 1em;
        font-weight: 500;
        flex-grow: 1;
    }
    
    .subcategory-toggle {
        transition: transform 0.3s;
    }
    
    .subcategory-toggle.expanded {
        transform: rotate(90deg);
    }
    
    .subcategory-content {
        margin-left: 15px;
        overflow: hidden;
        max-height: 0;
        transition: max-height 0.3s ease-out;
    }
    
    .subcategory-content.expanded {
        max-height: 2000px;
    }
    
    .sidebar-links {
        list-style: none;
        padding: 0;
        margin: 5px 0;
    }
    
    .sidebar-link {
        padding: 6px 10px 6px 25px;
        margin: 2px 0;
        display: flex;
        align-items: center;
        color: var(--text-color);
        text-decoration: none;
        border-radius: 4px;
        transition: background-color 0.2s;
        font-size: 0.95em;
    }
    
    .sidebar-link:hover {
        background-color: rgba(0,0,0,0.05);
    }
    
    .sidebar-link.active {
        background-color: var(--primary-color);
        color: white;
    }
    
    .link-icon {
        margin-right: 8px;
        font-size: 1.1em;
        opacity: 0.8;
    }
    
    .language-selector {
        display: flex;
        justify-content: center;
        text-align: center;
        padding: 10px 20px;
        border-bottom: 1px solid var(--border-color);
        background-color: var(--bg-secondary);
        position: sticky;
        top: 0;
        z-index: 10;
    }
    
    .lang-option {
        padding: 5px 10px;
        margin: 0 5px;
        border-radius: 4px;
        text-decoration: none;
        color: var(--text-color);
        font-weight: 500;
        transition: background-color 0.2s, transform 0.2s;
    }
    
    .lang-option:hover {
        background-color: rgba(0,0,0,0.05);
        transform: translateY(-2px);
    }
    
    .lang-option.active {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Mobile menu toggle */
    .menu-toggle {
        display: none;
        position: fixed;
        top: 20px;
        left: 20px;
        z-index: 200;
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 1.5em;
        cursor: pointer;
        box-shadow: var(--card-shadow);
        transition: background-color 0.2s;
    }
    
    .menu-toggle:hover {
        background-color: var(--secondary-color);
    }
    
    /* Content styling */
    #content-wrapper {
        padding: 20px;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--heading-color);
        margin-top: 1.5em;
        margin-bottom: 0.5em;
    }
    
    h1 {
        font-size: 2.2em;
        padding-bottom: 0.3em;
        border-bottom: 1px solid var(--border-color);
    }
    
    h2 {
        font-size: 1.7em;
        padding-bottom: 0.3em;
        border-bottom: 1px solid var(--border-color);
    }
    
    h3 {
        font-size: 1.4em;
    }
    
    a {
        color: var(--link-color);
        text-decoration: none;
        transition: color 0.2s;
    }
    
    a:hover {
        color: var(--secondary-color);
        text-decoration: underline;
    }
    
    code {
        font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        background-color: var(--code-bg);
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 0.9em;
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
        font-size: 0.9em;
    }
    
    blockquote {
        margin: 1em 0;
        padding: 0 1em;
        color: var(--text-secondary);
        border-left: 0.25em solid var(--border-color);
        background-color: rgba(0,0,0,0.02);
        border-radius: 0 4px 4px 0;
    }
    
    img {
        max-width: 100%;
        border-radius: 4px;
    }
    
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
        border-radius: 4px;
        overflow: hidden;
    }
    
    table, th, td {
        border: 1px solid var(--border-color);
    }
    
    th, td {
        padding: 10px 16px;
        text-align: left;
    }
    
    th {
        background-color: var(--bg-color);
        font-weight: 600;
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
        background-color: var(--bg-secondary);
        transition: transform var(--transition-speed), box-shadow var(--transition-speed);
        box-shadow: var(--card-shadow);
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--card-shadow-hover);
    }
    
    .feature-card h3 {
        margin-top: 0;
        color: var(--primary-color);
        border-bottom: none;
        display: flex;
        align-items: center;
    }
    
    .feature-card h3 .icon {
        margin-right: 10px;
        font-size: 1.4em;
    }
    
    .footer-note {
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid var(--border-color);
        font-size: 0.9em;
        color: var(--text-secondary);
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
        transition: background-color 0.2s;
    }
    
    .copy-button:hover {
        background-color: rgba(0,0,0,0.2);
    }
    
    .breadcrumbs {
        display: flex;
        flex-wrap: wrap;
        margin-bottom: 20px;
        padding: 10px 15px;
        background-color: var(--bg-color);
        border-radius: 4px;
        font-size: 0.9em;
    }
    
    .breadcrumb-item {
        display: flex;
        align-items: center;
    }
    
    .breadcrumb-item:not(:last-child):after {
        content: ">";
        margin: 0 8px;
        color: var(--text-secondary);
    }
    
    .breadcrumb-item a {
        color: var(--link-color);
        text-decoration: none;
    }
    
    .breadcrumb-item a:hover {
        text-decoration: underline;
    }
    
    .breadcrumb-item.active {
        color: var(--text-secondary);
    }
    
    .toc {
        background-color: var(--bg-color);
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 30px;
        box-shadow: var(--card-shadow);
    }
    
    .toc-title {
        font-size: 1.1em;
        font-weight: 600;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
    }
    
    .toc-icon {
        margin-right: 8px;
    }
    
    .toc-list {
        list-style: none;
        padding-left: 15px;
    }
    
    .toc-list li {
        margin: 5px 0;
    }
    
    .toc-list a {
        color: var(--text-color);
        text-decoration: none;
        transition: color 0.2s;
    }
    
    .toc-list a:hover {
        color: var(--primary-color);
        text-decoration: underline;
    }
    
    .page-hero {
        margin: -40px -40px 40px -40px;
        padding: 60px 40px;
        background-color: var(--primary-color);
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .page-hero h1 {
        color: white;
        border-bottom: none;
        margin: 0;
        font-size: 2.5em;
        position: relative;
        z-index: 2;
    }
    
    .page-hero p {
        max-width: 700px;
        margin: 15px 0 0 0;
        position: relative;
        z-index: 2;
    }
    
    .page-hero::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(0,0,0,0.3) 0%, transparent 50%);
        z-index: 1;
    }
    
    .quick-links {
        display: flex;
        flex-wrap: wrap;
        margin: 30px 0;
        gap: 15px;
    }
    
    .quick-link {
        background-color: var(--bg-color);
        border-radius: 4px;
        padding: 10px 15px;
        display: flex;
        align-items: center;
        color: var(--heading-color);
        text-decoration: none;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: var(--card-shadow);
    }
    
    .quick-link:hover {
        transform: translateY(-3px);
        box-shadow: var(--card-shadow-hover);
        text-decoration: none;
    }
    
    .quick-link-icon {
        margin-right: 10px;
        font-size: 1.2em;
    }
    
    @media (max-width: 1024px) {
        :root {
            --sidebar-width: 280px;
        }
        
        .feature-grid {
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        }
    }
    
    @media (max-width: 768px) {
        body {
            flex-direction: column;
        }
        
        #sidebar {
            width: 280px;
            transform: translateX(-100%);
        }
        
        #sidebar.active {
            transform: translateX(0);
        }
        
        #content {
            margin-left: 0;
            padding: 20px;
            width: 100%;
            box-sizing: border-box;
        }
        
        .menu-toggle {
            display: block;
        }
        
        .page-hero {
            margin: -20px -20px 30px -20px;
            padding: 40px 20px;
        }
        
        .page-hero h1 {
            font-size: 2em;
        }
        
        .feature-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Estilo para dark mode */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-color: #1a1a1a;
            --bg-secondary: #2a2a2a;
            --text-color: #e0e0e0;
            --text-secondary: #b0b0b0;
            --heading-color: #f0f0f0;
            --code-bg: #333;
            --border-color: #444;
            --shadow-color: rgba(0, 0, 0, 0.3);
        }
        
        .copy-button {
            background-color: rgba(255,255,255,0.1);
        }
        
        .copy-button:hover {
            background-color: rgba(255,255,255,0.2);
        }
        
        tr:nth-child(even), th {
            background-color: #333;
        }
        
        blockquote {
            background-color: rgba(255,255,255,0.05);
        }
    }
    """

    # JavaScript para a página
    js = """
    document.addEventListener('DOMContentLoaded', function() {
        // Expansão de categorias e subcategorias
        const categoryHeaders = document.querySelectorAll('.category-header');
        const subcategoryHeaders = document.querySelectorAll('.subcategory-header');
        
        // Função para expandir categoria
        function toggleCategory(header) {
            const content = header.nextElementSibling;
            const toggle = header.querySelector('.category-toggle');
            
            if (content.classList.contains('expanded')) {
                content.classList.remove('expanded');
                toggle.classList.remove('expanded');
            } else {
                content.classList.add('expanded');
                toggle.classList.add('expanded');
            }
        }
        
        // Adicionar evento de clique nas categorias
        categoryHeaders.forEach(header => {
            header.addEventListener('click', () => {
                toggleCategory(header);
            });
        });
        
        // Adicionar evento de clique nas subcategorias
        subcategoryHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const content = header.nextElementSibling;
                const toggle = header.querySelector('.subcategory-toggle');
                
                if (content.classList.contains('expanded')) {
                    content.classList.remove('expanded');
                    toggle.classList.remove('expanded');
                } else {
                    content.classList.add('expanded');
                    toggle.classList.add('expanded');
                }
            });
        });
        
        // Expandir automaticamente a categoria ativa
        const activeLink = document.querySelector('.sidebar-link.active');
        if (activeLink) {
            // Encontrar os pais da categoria e subcategoria
            let parent = activeLink.parentElement;
            while (parent) {
                if (parent.classList.contains('category-content') || parent.classList.contains('subcategory-content')) {
                    parent.classList.add('expanded');
                    const headerToggle = parent.previousElementSibling.querySelector('.category-toggle, .subcategory-toggle');
                    if (headerToggle) headerToggle.classList.add('expanded');
                }
                parent = parent.parentElement;
            }
            
            // Scrollar para o link ativo com um pequeno atraso
            setTimeout(() => {
                activeLink.scrollIntoView({ block: 'center', behavior: 'smooth' });
            }, 300);
        }
        
        // Adicionar botões de cópia aos blocos de código
        document.querySelectorAll('pre').forEach(function(pre) {
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.textContent = 'Copy';
            
            pre.style.position = 'relative';
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
        
        // Lidar com navegação de âncoras
        function handleAnchorNavigation() {
            const hash = window.location.hash;
            if (!hash) return;
            
            const targetId = hash.substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                setTimeout(() => {
                    targetElement.scrollIntoView({ behavior: 'smooth' });
                }, 100);
            }
        }
        
        // Lidar com navegação de âncoras na carga da página
        handleAnchorNavigation();
        
        // Lidar com cliques em links de âncora
        document.querySelector('#content').addEventListener('click', function(e) {
            const target = e.target;
            
            if (target.tagName === 'A' || target.closest('a')) {
                const link = target.tagName === 'A' ? target : target.closest('a');
                const href = link.getAttribute('href');
                
                if (href && href.startsWith('#')) {
                    e.preventDefault();
                    window.location.hash = href;
                    handleAnchorNavigation();
                }
            }
        });
        
        // Lidar com mudanças de hash
        window.addEventListener('hashchange', handleAnchorNavigation);
        
        // Toggle menu para dispositivos móveis
        const menuToggle = document.querySelector('.menu-toggle');
        if (menuToggle) {
            menuToggle.addEventListener('click', function() {
                const sidebar = document.querySelector('#sidebar');
                sidebar.classList.toggle('active');
            });
            
            // Fechar menu ao clicar em um link (mobile)
            const mobileLinks = document.querySelectorAll('#sidebar a');
            mobileLinks.forEach(link => {
                link.addEventListener('click', function() {
                    if (window.innerWidth <= 768) {
                        const sidebar = document.querySelector('#sidebar');
                        sidebar.classList.remove('active');
                    }
                });
            });
            
            // Fechar menu ao clicar fora (mobile)
            document.querySelector('#content').addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    const sidebar = document.querySelector('#sidebar');
                    sidebar.classList.remove('active');
                }
            });
        }
    });
    """

    # Determinar se é a página inicial
    is_home_page = False
    if active_file and "index.md" in active_file.name:
        is_home_page = True

    # Construir seletor de idioma
    language_selector_html = get_language_selector(current_language)

    # Construir menu lateral
    sidebar_html = []
    sidebar_html.append('<div id="sidebar">')
    sidebar_html.append('  <div class="sidebar-header">')

    # Adicionar a logo
    sidebar_html.append('    <div class="logo-container">')
    sidebar_html.append(f'      <img src="/assets/images/logo.png" alt="MicroDetect Logo" class="logo-image">')
    sidebar_html.append("    </div>")

    # Título baseado no idioma
    if current_language == "pt":
        sidebar_title = "Documentação MicroDetect"
    else:
        sidebar_title = "MicroDetect Documentation"

    sidebar_html.append(
        f'    <h1 class="sidebar-title"><a href="/?file=index.md&lang={current_language}">{sidebar_title}</a></h1>'
    )
    # Adicionar seletor de idioma
    sidebar_html.append(language_selector_html)
    sidebar_html.append("  </div>")



    # Determinar qual categoria e subcategoria estão ativas
    active_category = None
    active_subcategory = None

    if active_file and active_file.name in file_map:
        active_doc = file_map[active_file.name]
        active_category = active_doc.category
        active_subcategory = active_doc.subcategory

    # Adicionar categorias e links
    for category, category_info in doc_structure.items():
        category_active = category == active_category
        category_active_class = "active" if category_active else ""

        sidebar_html.append(f'  <div class="sidebar-category">')
        sidebar_html.append(f'    <div class="category-header {category_active_class}">')
        sidebar_html.append(f'      <span class="category-icon">{category_info["icon"]}</span>')
        sidebar_html.append(f'      <div class="category-title">{category}</div>')
        sidebar_html.append(f'      <span class="category-toggle">▶</span>')
        sidebar_html.append(f'    </div>')

        # Expandir por padrão se a categoria estiver ativa
        expanded_class = "expanded" if category_active else ""
        sidebar_html.append(f'    <div class="category-content {expanded_class}">')

        # Adicionar links diretamente na categoria
        if category_info["pages"]:
            sidebar_html.append(f'      <ul class="sidebar-links">')
            for doc_page in category_info["pages"]:
                active_class = "active" if active_file and active_file.name == doc_page.name else ""
                sidebar_html.append(
                    f'        <li><a class="sidebar-link {active_class}" href="/?file={doc_page.name}&lang={current_language}">'
                    f'<span class="link-icon">{doc_page.icon}</span>{doc_page.title}</a></li>'
                )
            sidebar_html.append(f'      </ul>')

        # Adicionar subcategorias
        for subcategory, subcategory_info in category_info["subcategories"].items():
            subcategory_active = subcategory == active_subcategory and category == active_category
            subcategory_active_class = "active" if subcategory_active else ""

            sidebar_html.append(f'      <div class="subcategory">')
            sidebar_html.append(f'        <div class="subcategory-header {subcategory_active_class}">')
            sidebar_html.append(f'          <span class="subcategory-icon">{subcategory_info["icon"]}</span>')
            sidebar_html.append(f'          <div class="subcategory-title">{subcategory}</div>')
            sidebar_html.append(f'          <span class="subcategory-toggle">▶</span>')
            sidebar_html.append(f'        </div>')

            # Expandir por padrão se a subcategoria estiver ativa
            expanded_class = "expanded" if subcategory_active else ""
            sidebar_html.append(f'        <div class="subcategory-content {expanded_class}">')

            # Adicionar links na subcategoria
            sidebar_html.append(f'          <ul class="sidebar-links">')
            for doc_page in subcategory_info["pages"]:
                active_class = "active" if active_file and active_file.name == doc_page.name else ""
                sidebar_html.append(
                    f'            <li><a class="sidebar-link {active_class}" href="/?file={doc_page.name}&lang={current_language}">'
                    f'<span class="link-icon">{doc_page.icon}</span>{doc_page.title}</a></li>'
                )
            sidebar_html.append(f'          </ul>')

            sidebar_html.append(f'        </div>')
            sidebar_html.append(f'      </div>')

        sidebar_html.append(f'    </div>')
        sidebar_html.append(f'  </div>')

    sidebar_html.append("</div>")

    # Botão de menu para mobile
    mobile_toggle = '<button class="menu-toggle">☰</button>'

    # Título da página
    page_title = "MicroDetect Documentation"
    if current_language == "pt":
        page_title = "Documentação MicroDetect"

    # Adicionar breadcrumbs se não for a página inicial
    breadcrumbs_html = ""
    if not is_home_page and active_file and active_file.name in file_map:
        active_doc = file_map[active_file.name]
        breadcrumbs = ['<div class="breadcrumbs">']

        # Home
        if current_language == "pt":
            home_text = "Início"
        else:
            home_text = "Home"

        breadcrumbs.append(f'<div class="breadcrumb-item"><a href="/?file=index.md&lang={current_language}">{home_text}</a></div>')

        # Categoria
        if active_doc.category:
            breadcrumbs.append(f'<div class="breadcrumb-item">{active_doc.category}</div>')

        # Subcategoria
        if active_doc.subcategory:
            breadcrumbs.append(f'<div class="breadcrumb-item">{active_doc.subcategory}</div>')

        # Página atual
        breadcrumbs.append(f'<div class="breadcrumb-item active">{active_doc.title}</div>')

        breadcrumbs.append('</div>')
        breadcrumbs_html = "\n".join(breadcrumbs)

    # Personalizar a página inicial
    if is_home_page:
        # Não precisamos modificar o conteúdo HTML da página inicial,
        # pois ele já vem bem formatado do arquivo index.md
        pass

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
        mobile_toggle,
        "\n".join(sidebar_html),
        '  <div id="content">',
        '    <div id="content-wrapper">',
        breadcrumbs_html,
        content_html,
        "    </div>",
        "  </div>",
        f"  <script>{js}</script>",
        "</body>",
        "</html>",
    ]

    return "\n".join(html)


class DocsRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Manipulador de requisições para o servidor de documentação."""

    docs_dir: Path = None
    doc_structure: Dict[str, Dict[str, Any]] = None
    file_map: Dict[str, DocPage] = None
    current_language: str = DEFAULT_LANGUAGE

    def do_GET(self):
        """Processar requisições GET."""
        # Analisar URL
        url_parts = urlparse(self.path)
        query_params = parse_qs(url_parts.query)

        if url_parts.path.startswith("/assets/"):
            self.serve_static_file(url_parts.path)
            return

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
        self.doc_structure, self.file_map = organize_documentation(self.docs_dir, lang)

        # Se não há arquivo especificado, procurar por index.md
        if not file_name:
            index_path = self.docs_dir / lang / "index.md"
            if index_path.exists():
                file_path = index_path
            else:
                # Verificar se há algum arquivo mapeado
                for category, category_info in self.doc_structure.items():
                    if category_info["pages"]:
                        file_path = category_info["pages"][0].path
                        break

                    # Verificar subcategorias
                    for subcategory, subcategory_info in category_info["subcategories"].items():
                        if subcategory_info["pages"]:
                            file_path = subcategory_info["pages"][0].path
                            break
        else:
            # Se o arquivo foi especificado, verificar se existe no mapa
            if file_name in self.file_map:
                file_path = self.file_map[file_name].path
            else:
                # Procurar diretamente no diretório
                file_path = self.docs_dir / lang / file_name

        # Se não encontrou arquivo, verificar se existe no idioma padrão
        if not file_path or not file_path.exists():
            if lang != DEFAULT_LANGUAGE:
                # Obter estrutura no idioma padrão
                default_structure, default_map = organize_documentation(self.docs_dir, DEFAULT_LANGUAGE)

                if file_name and file_name in default_map:
                    file_path = default_map[file_name].path
                else:
                    default_index_path = self.docs_dir / DEFAULT_LANGUAGE / "index.md"
                    if default_index_path.exists():
                        file_path = default_index_path

            # Se ainda não encontrou, gerar página de erro
            if not file_path or not file_path.exists():
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                if lang == "pt":
                    error_html = f"<h1>Documentação Não Encontrada</h1><p>O arquivo solicitado não foi encontrado.</p>"
                else:
                    error_html = f"<h1>Documentation Not Found</h1><p>The requested file was not found.</p>"

                page_html = create_html_page(error_html, self.doc_structure, self.file_map, current_language=lang)
                self.wfile.write(page_html.encode())
                return

        # Ler conteúdo do arquivo
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()

            # Converter para HTML com o novo processador de links
            content_html = markdown_to_html(markdown_content, lang)

            # Criar página completa
            page_html = create_html_page(content_html, self.doc_structure, self.file_map, file_path, lang)

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

            page_html = create_html_page(error_html, self.doc_structure, self.file_map, current_language=lang)
            self.wfile.write(page_html.encode())

    def serve_static_file(self, path):
        """Serve arquivos estáticos como imagens e outros recursos."""
        file_path = os.path.join(self.docs_dir, path[1:])

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            self.send_error(404, "File not found")
            return

        # Determinar o tipo MIME com base na extensão
        _, ext = os.path.splitext(file_path)
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".css": "text/css",
            ".js": "application/javascript",
        }

        content_type = mime_types.get(ext.lower(), "application/octet-stream")

        try:
            with open(file_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Internal error: {str(e)}")


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
                        f.write(
                            "Welcome to MicroDetect documentation. Please add more documentation files to the docs/en directory.\n"
                        )
                    else:
                        f.write("# Documentação do MicroDetect\n\n")
                        f.write(
                            "Bem-vindo à documentação do MicroDetect. Por favor, adicione mais arquivos de documentação ao diretório docs/pt.\n"
                        )

    # Obter estrutura hierárquica de documentos
    doc_structure, file_map = organize_documentation(docs_dir, DEFAULT_LANGUAGE)

    # Configurar handler com o diretório de documentação
    DocsRequestHandler.docs_dir = docs_dir
    DocsRequestHandler.doc_structure = doc_structure
    DocsRequestHandler.file_map = file_map
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


# Implementação de execução em background para o servidor de documentação.
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
            # Encontrar diretório de documentação
            docs_dir = find_docs_dir()

            # Obter estrutura hierárquica de documentos
            doc_structure, file_map = organize_documentation(docs_dir, DEFAULT_LANGUAGE)

            # Configurar handler com o diretório de documentação
            DocsRequestHandler.docs_dir = docs_dir
            DocsRequestHandler.doc_structure = doc_structure
            DocsRequestHandler.file_map = file_map
            DocsRequestHandler.current_language = DEFAULT_LANGUAGE

            # Iniciar servidor
            with socketserver.TCPServer((HOST, PORT), DocsRequestHandler) as httpd:
                httpd.serve_forever()
        except Exception:
            # Ignorar exceções em modo daemon
            pass


if __name__ == "__main__":
    import argparse

    # Configurar argumentos de linha de comando
    parser = argparse.ArgumentParser(description="MicroDetect Documentation Server")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (background process)")
    parser.add_argument("--port", type=int, help="Port for the server")
    parser.add_argument(
        "--lang", type=str, choices=list(LANGUAGES.keys()), default=DEFAULT_LANGUAGE, help="Default language for documentation"
    )

    args = parser.parse_args()

    if args.daemon:
        run_as_daemon(args.port, args.lang)
    else:
        # Iniciar servidor normalmente
        start_docs_server(args.lang)