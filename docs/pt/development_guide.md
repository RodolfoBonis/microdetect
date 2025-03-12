# Guia de Desenvolvimento

Este guia fornece informações para desenvolvedores que desejam contribuir com o projeto MicroDetect.

## Sumário
- [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
- [Configurando o Ambiente de Desenvolvimento](#configurando-o-ambiente-de-desenvolvimento)
- [Diretrizes de Contribuição](#diretrizes-de-contribuição)
- [Fluxo de Trabalho de Desenvolvimento](#fluxo-de-trabalho-de-desenvolvimento)
- [Estilo e Padrões de Código](#estilo-e-padrões-de-código)
- [Testes](#testes)
- [Documentação](#documentação)
- [Processo de Build e Release](#processo-de-build-e-release)
- [Tarefas Comuns de Desenvolvimento](#tarefas-comuns-de-desenvolvimento)
- [Solucionando Problemas de Desenvolvimento](#solucionando-problemas-de-desenvolvimento)
- [Recursos para Desenvolvedores](#recursos-para-desenvolvedores)
- [Contato e Suporte](#contato-e-suporte)

## Visão Geral da Arquitetura

O MicroDetect segue uma arquitetura modular, organizada em pacotes e módulos funcionais:

```
microdetect/
├── __init__.py                 # Inicialização do pacote
├── cli.py                      # Interface de linha de comando
├── data/                       # Processamento de dados
│   ├── __init__.py
│   ├── augmentation.py         # Augmentação de imagens
│   ├── conversion.py           # Conversão de formatos
│   └── dataset.py              # Gerenciamento de datasets
├── annotation/                 # Ferramentas de anotação
│   ├── __init__.py
│   ├── annotator.py            # Interface de anotação
│   └── visualization.py        # Visualização de anotações
├── training/                   # Módulos de treinamento
│   ├── __init__.py
│   ├── train.py                # Treinador de modelos
│   └── evaluate.py             # Avaliação de modelos
└── utils/                      # Utilitários
    ├── __init__.py
    ├── config.py               # Gerenciamento de configuração
    ├── updater.py              # Sistema de atualização
    └── aws_setup.py            # Configuração AWS
```

### Fluxo de Controle

1. O ponto de entrada principal é o `cli.py`
2. Os comandos são despachados para handlers específicos
3. Cada módulo é responsável por uma funcionalidade específica
4. O sistema de configuração centralizado gerencia parâmetros

## Configurando o Ambiente de Desenvolvimento

### Instalando Dependências de Desenvolvimento

```bash
# Clonar o repositório
git clone https://github.com/SeuUsuario/microdetect.git
cd microdetect

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OU
venv\Scripts\activate     # Windows

# Instalar dependências de produção e desenvolvimento
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Ferramentas de desenvolvimento

# Instalar o pacote em modo editável
pip install -e .

# Configurar hooks de pre-commit
pre-commit install
```

### Ferramentas de Desenvolvimento

O projeto utiliza as seguintes ferramentas de desenvolvimento:

- **Black**: Formatador de código
- **isort**: Organizador de imports
- **flake8**: Linter para qualidade de código
- **pytest**: Framework de testes
- **pytest-cov**: Medição de cobertura de código
- **pre-commit**: Hooks de git para verificação automática
- **twine**: Para publicação de pacotes
- **sphinx**: Para geração de documentação

### Executando Testes

```bash
# Executar todos os testes
pytest

# Executar testes com cobertura
pytest --cov=microdetect

# Gerar relatório de cobertura HTML
pytest --cov=microdetect --cov-report=html

# Executar testes específicos
pytest tests/test_modulo_especifico.py

# Executar testes com saída detalhada
pytest -v
```

### Verificando a Qualidade do Código

```bash
# Verificar formatação com black
black --check microdetect

# Formatar código com black
black microdetect

# Verificar imports com isort
isort --check-only --profile black microdetect

# Organizar imports
isort --profile black microdetect

# Verificar com flake8
flake8 microdetect

# Executar todas as verificações de qualidade
pre-commit run --all-files
```

## Diretrizes de Contribuição

### Fluxo de Trabalho Git

1. **Forks e Branches**:
   - Faça um fork do repositório
   - Crie uma branch para sua feature ou correção:
     ```bash
     git checkout -b feature/nome-da-sua-feature
     # ou
     git checkout -b fix/nome-do-seu-bug
     ```

2. **Commits**:
   - Use mensagens de commit significativas seguindo [Conventional Commits](https://www.conventionalcommits.org/):
     ```
     feat: adicionar suporte para processamento de TIFFs multi-página
     fix: corrigir carregamento de anotações para caminhos não padrão
     docs: melhorar instruções de instalação
     test: adicionar casos de teste para divisão de dataset
     refactor: otimizar pipeline de augmentação
     ```

3. **Pull Requests**:
   - Faça suas alterações e crie um Pull Request para a branch `main`
   - Descreva suas alterações em detalhes
   - Referencie issues relacionadas usando `#numero_da_issue`
   - Aguarde a revisão de código

### Estilo de Código

- Siga o guia de estilo [PEP 8](https://peps.python.org/pep-0008/)
- Use Black com configuração padrão (comprimento máximo de linha de 127 caracteres conforme configurado)
- Use tipagem estática com [type hints](https://docs.python.org/3/library/typing.html):
  ```python
  def processar_imagem(caminho_imagem: str, diretorio_saida: Optional[str] = None) -> bool:
      # implementação
  ```
- Use docstrings no estilo Google:
  ```python
  def funcao(arg1: int, arg2: str) -> bool:
      """
      Breve descrição da função.
      
      Descrição mais longa explicando detalhes.
      
      Args:
          arg1: Descrição do arg1
          arg2: Descrição do arg2
              
      Returns:
          Descrição do valor de retorno
              
      Raises:
          ValueError: Descrição de quando este erro é lançado
      """
  ```

### Testes

- Escreva testes para todas as novas funcionalidades e correções
- Mantenha ou melhore a cobertura de testes existente
- Estruture os testes para espelhar a estrutura do código fonte:
  ```
  tests/
  ├── test_cli.py
  ├── data/
  │   ├── test_augmentation.py
  │   ├── test_conversion.py
  │   └── test_dataset.py
  ├── annotation/
  │   ├── test_annotator.py
  │   └── test_visualization.py
  ├── training/
  │   ├── test_train.py
  │   └── test_evaluate.py
  └── utils/
      ├── test_config.py
      ├── test_updater.py
      └── test_aws_setup.py
  ```

# Documentação

## Empacotamento e Acesso à Documentação

O projeto MicroDetect agora inclui um sistema de documentação abrangente que é devidamente empacotado com a distribuição. Esta seção explica como a documentação é estruturada, empacotada e servida.

## Estrutura da Documentação

A documentação está organizada em uma estrutura baseada em idiomas:

```
docs/
├── en/                          # Documentação em inglês
│   ├── index.md                 # Ponto de entrada principal
│   ├── installation_guide.md    # Instruções de instalação
│   ├── ...                      # Outros arquivos de tópicos
└── pt/                          # Documentação em português
    ├── index.md                 # Ponto de entrada principal (português)
    ├── installation_guide.md    # Instruções de instalação (português)
    └── ...                      # Outros arquivos de tópicos
```

## Empacotamento da Documentação

A documentação é incluída no pacote MicroDetect durante o processo de build usando dois mecanismos:

### 1. Configuração MANIFEST.in

O arquivo `MANIFEST.in` inclui as seguintes diretivas para incluir arquivos de documentação:

```
recursive-include docs *.md
recursive-include docs *.html
recursive-include docs *.css
recursive-include docs *.js
recursive-include docs *.png
recursive-include docs *.jpg
recursive-include docs *.svg
```

### 2. Configuração setup.py

O arquivo `setup.py` inclui código para coletar e organizar arquivos de documentação:

```python
# Coletar todos os arquivos de documentação
doc_files = glob.glob('docs/**/*.md', recursive=True)
doc_files += glob.glob('docs/**/*.html', recursive=True)
doc_files += glob.glob('docs/**/*.css', recursive=True)
# ...etc.

# Organizar arquivos de documentação por estrutura de diretórios
doc_dirs = {}
for doc_file in doc_files:
    rel_dir = os.path.dirname(doc_file)
    if rel_dir not in doc_dirs:
        doc_dirs[rel_dir] = []
    doc_dirs[rel_dir].append(doc_file)

# Criar entradas data_files para cada diretório
doc_data_files = []
for rel_dir, files in doc_dirs.items():
    install_dir = os.path.join('share/microdetect', rel_dir)
    doc_data_files.append((install_dir, files))

# Adicionar ao setup
setup(
    # ...outros parâmetros de setup...
    data_files=doc_data_files,
)
```

Isso garante que os arquivos de documentação sejam instalados corretamente no diretório `share/microdetect/docs/` do pacote Python.

## Servidor de Documentação

A CLI do MicroDetect inclui um servidor de documentação integrado:

```python
# Em microdetect/utils/docs_server.py
```

Este módulo fornece:

1. Um servidor web que renderiza arquivos Markdown como HTML
2. Uma barra lateral de navegação com links de documentação organizados
3. Alternância de idioma entre inglês e português
4. Funcionalidade de busca
5. A capacidade de executar em modo de segundo plano

## Comandos CLI para Documentação

Dois comandos principais foram implementados para acesso à documentação:

### 1. `microdetect docs`

Inicia o servidor de documentação:

```bash
# Uso básico
microdetect docs

# Opções de idioma
microdetect docs --lang pt  # Português
microdetect docs --lang en  # Inglês (padrão)

# Modo de segundo plano
microdetect docs --background
microdetect docs --status
microdetect docs --stop
```

### 2. `microdetect install-docs`

Instala arquivos de documentação no diretório do usuário:

```bash
microdetect install-docs [--force]
```

Isso copia os arquivos de documentação para `~/.microdetect/docs/` para acesso offline.

## Fluxo de Trabalho de Desenvolvimento para Documentação

Ao desenvolver ou atualizar a documentação:

1. Edite os arquivos Markdown apropriados no diretório `docs/`
2. Teste a documentação localmente usando `microdetect docs`
3. Certifique-se de atualizar ambas as versões de idioma conforme necessário
4. As alterações na documentação serão incluídas no próximo build do pacote

## Melhores Práticas para Documentação

1. Mantenha a documentação sincronizada entre os idiomas
2. Use links relativos entre arquivos de documentação para navegação
3. Prefixe links de documentação internos com informações de idioma
4. Use uma estrutura consistente entre as versões de idioma
5. Inclua exemplos de código e capturas de tela quando apropriado
6. Lembre-se de atualizar a documentação ao fazer alterações significativas no código

## Testando o Empacotamento da Documentação

Para testar se a documentação está corretamente empacotada:

```bash
# Construir o pacote
python setup.py sdist bdist_wheel

# Instalar o pacote em um ambiente de teste
pip install --force-reinstall dist/microdetect-*.whl

# Iniciar o servidor de documentação para verificar a instalação
microdetect docs
```

Isso verificará se os arquivos de documentação estão devidamente incluídos no build e podem ser acessados através do servidor de documentação.

## Fluxo de Trabalho de Desenvolvimento

### Adicionando um Novo Comando CLI

Para adicionar um novo comando ao CLI:

1. Crie um novo módulo para a funcionalidade em um diretório apropriado
2. Implemente a lógica principal em uma classe ou funções neste módulo
3. Adicione uma função para configurar o parser no `cli.py`:
   ```python
   def setup_novo_comando_parser(subparsers):
       """Configurar parser para novo comando."""
       parser = subparsers.add_parser("novo-comando", help="Descrição do comando")
       parser.add_argument("--arg-obrigatorio", required=True, help="Argumento obrigatório")
       parser.add_argument("--arg-opcional", default="valor", help="Argumento opcional")
   ```
4. Adicione um handler para processar o comando:
   ```python
   def handle_novo_comando(args):
       """Manipular novo comando."""
       # Importar módulo apenas quando o comando for invocado
       from microdetect.modulo.novo_modulo import NovaFuncionalidade
       
       funcionalidade = NovaFuncionalidade()
       resultado = funcionalidade.processar(args.arg_obrigatorio, arg_opcional=args.arg_opcional)
       logger.info(f"Novo comando executado com sucesso: {resultado}")
   ```
5. Adicione o parser e handler ao `main()`:
   ```python
   # Adicionar à lista de registro de parser
   setup_novo_comando_parser(subparsers)
   
   # Adicionar ao switch case de comandos
   elif parsed_args.command == "novo-comando":
       handle_novo_comando(parsed_args)
   ```

### Estendendo Funcionalidades Existentes

Para estender uma funcionalidade existente:

1. Entenda o código atual e como ele se integra no fluxo de trabalho
2. Atualize os testes existentes ou adicione novos
3. Atualize a documentação para refletir as mudanças
4. Atualize o arquivo `config.yaml` se necessário

### Sistema de Atualização

Para estender o sistema de atualização:

1. Entenda a estrutura do `updater.py` e `aws_setup.py`
2. Adicione novos métodos para funcionalidades adicionais
3. Garanta compatibilidade com o fluxo existente

## Estilo e Padrões de Código

O MicroDetect segue estes padrões de codificação:

1. **Convenções de Nomenclatura**:
   - `snake_case` para variáveis, funções, métodos e módulos
   - `PascalCase` para classes
   - `MAIUSCULAS` para constantes

2. **Organização de Imports**:
   - Imports da biblioteca padrão primeiro
   - Imports de bibliotecas de terceiros em segundo
   - Imports da aplicação local em terceiro
   - Ordenação alfabética dentro de cada grupo

3. **Documentação**:
   - Docstrings de módulo no topo de cada arquivo explicando o propósito
   - Docstrings de classe explicando o propósito da classe
   - Docstrings de método/função no estilo Google

4. **Tratamento de Erros**:
   - Use exceções específicas
   - Forneça mensagens de erro significativas
   - Registre erros com níveis apropriados

5. **Logging**:
   - Use o módulo `logging` em vez de declarações print
   - Use níveis de log apropriados (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
   - Inclua contexto relevante nas mensagens de log

## Testes

### Tipos de Testes

1. **Testes Unitários**: Testa funções e métodos individuais
2. **Testes de Integração**: Testa interação entre componentes
3. **Testes Funcionais**: Testa fluxos de trabalho de ponta a ponta

### Diretrizes de Teste

- Use fixtures do `pytest` para configurar ambientes de teste
- Faça mock de dependências externas
- Use testes parametrizados para múltiplos casos de teste similares
- Mire em 80%+ de cobertura de código
- Inclua casos de borda e condições de erro

### Escrevendo um Teste

```python
# Exemplo de um teste para conversão de imagem
def test_converter_tiff_para_png(imagem_tiff_exemplo, diretorio_saida_temp):
    """Testar conversão de uma imagem TIFF para formato PNG."""
    # Arrange
    conversor = ImageConverter()
    
    # Act
    sucesso, erros, mensagens = conversor.convert_tiff_to_png(
        input_dir=os.path.dirname(imagem_tiff_exemplo),
        output_dir=diretorio_saida_temp
    )
    
    # Assert
    assert sucesso == 1
    assert erros == 0
    assert len(mensagens) == 0
    
    # Verificar se o arquivo de saída existe e é um PNG válido
    nome_base = os.path.splitext(os.path.basename(imagem_tiff_exemplo))[0]
    caminho_saida = os.path.join(diretorio_saida_temp, f"{nome_base}.png")
    assert os.path.exists(caminho_saida)
    
    # Verificar se é um PNG válido
    with open(caminho_saida, 'rb') as f:
        assert f.read(8).startswith(b'\x89PNG\r\n\x1a\n')
```

## Documentação

### Estrutura da Documentação

A documentação está organizada nos seguintes diretórios:

```
docs/
├── en/                          # Documentação em inglês
│   ├── index.md                 # Ponto de entrada principal
│   ├── installation_guide.md    # Instruções de instalação
│   ├── advanced_configuration.md # Opções avançadas de configuração
│   ├── troubleshooting.md       # Informações de solução de problemas
│   └── ...                      # Outros arquivos de documentação
└── pt/                          # Documentação em português
    ├── index.md                 # Ponto de entrada principal (português)
    ├── installation_guide.md    # Instruções de instalação (português)
    └── ...                      # Outros arquivos de documentação
```

### Adicionando Documentação

1. Crie o arquivo de documentação em ambos os idiomas (se aplicável)
2. Use formatação Markdown
3. Inclua cabeçalhos de seção claros
4. Forneça exemplos de código quando relevante
5. Adicione o arquivo ao sumário em ambos os arquivos `index.md`

## Processo de Build e Release

### Construindo o Pacote

```bash
# Atualizar versão em microdetect/__init__.py
sed -i 's/__version__ = .*/__version__ = "x.y.z"/' microdetect/__init__.py

# Criar distribuição
python -m build

# Verificar distribuição
twine check dist/*
```

### Lançamento para AWS CodeArtifact

O projeto usa GitHub Actions para releases automatizadas para o AWS CodeArtifact. Quando uma nova release é criada no GitHub:

1. O workflow é acionado
2. O pacote é construído
3. É enviado para o AWS CodeArtifact
4. Uma notificação é enviada

Para uploads manuais para o AWS CodeArtifact:

```bash
# Configurar credenciais AWS
aws configure

# Obter token de autorização
export CODEARTIFACT_TOKEN=$(aws codeartifact get-authorization-token \
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

# Fazer upload usando twine
TWINE_USERNAME=aws \
TWINE_PASSWORD=$CODEARTIFACT_TOKEN \
python -m twine upload \
    --repository-url $CODEARTIFACT_REPOSITORY_URL \
    dist/*
```

## Tarefas Comuns de Desenvolvimento

### Trabalhando com Configuração

Para modificar o tratamento de configuração:

```python
from microdetect.utils.config import config

# Acessar configuração
valor = config.get("secao.chave", valor_padrao)

# Adicionar nova opção de configuração padrão
# Em config.py, atualizar método _get_default_config
def _get_default_config(self) -> Dict[str, Any]:
    return {
        "directories": {
            # configurações existentes
        },
        "nova_secao": {
            "nova_chave": "valor_padrao"
        }
    }
```

### Implementando Nova Funcionalidade de Processamento de Dados

```python
# Em um módulo novo ou existente:
from typing import List, Optional, Tuple
import cv2
import numpy as np
from microdetect.utils.config import config

class NovoProcessador:
    """Processa imagens com nova funcionalidade."""
    
    def __init__(self, param1: str = None, param2: int = None):
        """
        Inicializa processador com parâmetros.
        
        Args:
            param1: Descrição do primeiro parâmetro
            param2: Descrição do segundo parâmetro
        """
        self.param1 = param1 or config.get("nova_secao.param1", "padrao")
        self.param2 = param2 or config.get("nova_secao.param2", 42)
    
    def processar(self, caminho_entrada: str, caminho_saida: Optional[str] = None) -> Tuple[bool, str]:
        """
        Processa uma imagem com nova funcionalidade.
        
        Args:
            caminho_entrada: Caminho para a imagem de entrada
            caminho_saida: Caminho para salvar a imagem de saída (opcional)
            
        Returns:
            Tupla de (flag de sucesso, caminho de saída ou mensagem de erro)
        """
        try:
            # Implementação
            return True, caminho_saida
        except Exception as e:
            return False, str(e)
```

### Adicionando uma Nova Funcionalidade de Treinamento

```python
# Em training/train.py, adicione um novo método:
def treinar_com_nova_funcionalidade(self, data_yaml: str, novo_param: float = 0.5) -> Dict[str, Any]:
    """
    Treina um modelo com nova funcionalidade.
    
    Args:
        data_yaml: Caminho para o dataset YAML
        novo_param: Novo parâmetro para funcionalidade especial
    
    Returns:
        Resultados do treinamento
    """
    # Implementação
    model = YOLO(f"yolov8{self.model_size}.pt")
    results = model.train(
        data=data_yaml,
        epochs=self.epochs,
        batch=self.batch_size,
        imgsz=self.image_size,
        # Adicionar novos parâmetros
        novo_param_funcionalidade=novo_param
    )
    
    return results
```

## Solucionando Problemas de Desenvolvimento

### Isolando Problemas

Use ambientes virtuais separados para testar diferentes configurações:

```bash
python -m venv venv_teste
source venv_teste/bin/activate
pip install -e .

# Testar funcionalidade isoladamente
python -c "from microdetect.modulo import funcao; funcao()"
```

### Depurando Código

Use bibliotecas de depuração como `pdb` ou `ipdb`:

```python
import ipdb

def funcao_problematica():
    # ...código...
    ipdb.set_trace()  # Ponto de interrupção
    # ...mais código...
```

Ou use VSCode ou PyCharm para depuração visual.

### Perfilamento

Para identificar gargalos de desempenho:

```python
import cProfile
import pstats

# Executar o perfil
cProfile.run('funcao_para_perfilar()', 'stats.prof')

# Analisar resultados
p = pstats.Stats('stats.prof')
p.sort_stats('cumulative').print_stats(20)
```

## Recursos para Desenvolvedores

### Referências Úteis

- [Documentação do Ultralytics YOLOv8](https://docs.ultralytics.com/)
- [Tutorial do PyTorch](https://pytorch.org/tutorials/)
- [Documentação do AWS CodeArtifact](https://docs.aws.amazon.com/codeartifact/)
- [Guia PEP 8](https://peps.python.org/pep-0008/)
- [Guia de Type Hints](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)

### Ferramentas Recomendadas

- **IDE**: VSCode ou PyCharm
- **Terminal**: iTerm2 (macOS) ou Windows Terminal
- **Git GUI**: GitKraken, SourceTree ou VSCode Git
- **Ferramentas de Diff**: Meld ou Beyond Compare
- **Visualização de Dados**: Matplotlib, Seaborn

## Contato e Suporte

Para dúvidas ou suporte durante o desenvolvimento:

- Crie uma issue no GitHub
- Entre em contato com a equipe: dev@rodolfodebonis.com.br