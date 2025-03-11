# Guia de Desenvolvimento do MicroDetect

Este guia fornece informações para desenvolvedores que desejam contribuir com o projeto MicroDetect.

## Visão Geral da Arquitetura

O MicroDetect segue uma arquitetura modular, organizada em packages e módulos funcionais:

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

1. O entrypoint principal é o `cli.py`
2. Os comandos são despachados para handlers específicos
3. Cada módulo é responsável por uma funcionalidade específica
4. O sistema de configuração centralizado gerencia parâmetros

## Configurando o Ambiente de Desenvolvimento

### Instalando Dependências de Desenvolvimento

```bash
# Clone o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
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
- **flake8**: Linter para garantir qualidade do código
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

# Gerar relatório HTML de cobertura
pytest --cov=microdetect --cov-report=html

# Executar testes específicos
pytest tests/test_specific_module.py

# Executar testes com saída detalhada
pytest -v
```

### Verificando a Qualidade do Código

```bash
# Executar black para verificar formatação
black --check microdetect

# Executar black para formatar código
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
     git checkout -b feature/nome-da-feature
     # ou
     git checkout -b fix/nome-do-bug
     ```

2. **Commits**:
   - Use mensagens de commit significativas seguindo o [Conventional Commits](https://www.conventionalcommits.org/):
     ```
     feat: add support for processing multi-page TIFFs
     fix: correct annotation loading for non-standard paths
     docs: improve installation instructions
     test: add test cases for dataset splitting
     refactor: optimize augmentation pipeline
     ```

3. **Pull Requests**:
   - Faça as alterações e crie um Pull Request para a branch `main`
   - Descreva detalhadamente suas alterações
   - Referencie issues relacionadas usando `#issue_number`
   - Aguarde a revisão de código

### Estilo de Código

- Siga o estilo [PEP 8](https://peps.python.org/pep-0008/)
- Use Black com configuração padrão (linha máxima de 127 caracteres conforme configurado)
- Use tipagem estática com [type hints](https://docs.python.org/3/library/typing.html):
  ```python
  def process_image(image_path: str, output_dir: Optional[str] = None) -> bool:
      # implementation
  ```
- Use docstrings no estilo Google:
  ```python
  def function(arg1: int, arg2: str) -> bool:
      """
      Short description of function.
      
      Longer description explaining details.
      
      Args:
          arg1: Description of arg1
          arg2: Description of arg2
              
      Returns:
          Description of return value
              
      Raises:
          ValueError: Description of when this error is raised
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

### Documentação

- Mantenha a documentação atualizada com as alterações de código
- Documente novos parâmetros em funções e alterações de comportamento
- Adicione exemplos de uso para novas funcionalidades

## Desenvolvimento de Novas Funcionalidades

### Adicionando um Novo Comando CLI

Para adicionar um novo comando ao CLI:

1. Crie um novo módulo para a funcionalidade em um diretório apropriado
2. Implemente a lógica principal em uma classe ou funções neste módulo
3. Adicione uma função para configurar o parser no `cli.py`:
   ```python
   def setup_new_command_parser(subparsers):
       """Configurar parser para novo comando."""
       parser = subparsers.add_parser("new-command", help="Descrição do comando")
       parser.add_argument("--required-arg", required=True, help="Argumento necessário")
       parser.add_argument("--optional-arg", default="valor", help="Argumento opcional")
   ```
4. Adicione um handler para processar o comando:
   ```python
   def handle_new_command(args):
       """Manipular novo comando."""
       # Importar módulo apenas quando o comando for invocado
       from microdetect.module.new_module import NewFeature
       
       feature = NewFeature()
       result = feature.process(args.required_arg, optional_arg=args.optional_arg)
       logger.info(f"Novo comando executado com sucesso: {result}")
   ```
5. Adicione o parser e handler ao `main()`:
   ```python
   # Adicionar à lista de registros de parser
   setup_new_command_parser(subparsers)
   
   # Adicionar ao switch case de comandos
   elif parsed_args.command == "new-command":
       handle_new_command(parsed_args)
   ```

### Extensão das Funcionalidades Existentes

Para estender uma funcionalidade existente:

1. Entenda o código atual e como ele se integra no fluxo de trabalho
2. Atualize os testes existentes ou adicione novos
3. Atualize a documentação para refletir as mudanças
4. Atualize o arquivo `config.yaml` se necessário

### Sistema de Atualização

Para estender o sistema de atualização:

1. Entenda a estrutura do `updater.py` e `aws_setup.py`
2. Adicione novos métodos para funcionalidades adicionais
3. Certifique-se de manter a compatibilidade com o fluxo existente

## Build e Deploy

### Construindo o Pacote

```bash
# Atualizar a versão em microdetect/__init__.py
sed -i 's/__version__ = .*/__version__ = "x.y.z"/' microdetect/__init__.py

# Criar distribuição
python -m build

# Verificar distribuição
twine check dist/*
```

### Enviando para AWS CodeArtifact

Para contribuir com releases para o AWS CodeArtifact:

1. Configure suas credenciais AWS:
   ```bash
   aws configure
   ```

2. Obtenha um token de autorização:
   ```bash
   export CODEARTIFACT_TOKEN=$(aws codeartifact get-authorization-token \
       --domain seu-dominio \
       --query authorizationToken \
       --output text)
   ```

3. Obtenha o endpoint do repositório:
   ```bash
   export CODEARTIFACT_REPO_URL=$(aws codeartifact get-repository-endpoint \
       --domain seu-dominio \
       --repository seu-repositorio \
       --format pypi \
       --query repositoryEndpoint \
       --output text)
   ```

4. Faça upload usando twine:
   ```bash
   TWINE_USERNAME=aws \
   TWINE_PASSWORD=$CODEARTIFACT_TOKEN \
   python -m twine upload \
       --repository-url $CODEARTIFACT_REPO_URL \
       dist/*
   ```

## CI/CD

O projeto utiliza GitHub Actions para integração contínua e entrega contínua. Os fluxos de trabalho principais são:

### 1. Continuous Integration (ci.yml)

Acionado em push para `main` e pull requests:
- Executa linting e verificação de estilo
- Executa testes em múltiplas versões do Python
- Verifica a construção do pacote
- Realiza análise de segurança

### 2. Auto Release (auto-release.yml)

Acionado após CI bem-sucedido ou manualmente:
- Determina a próxima versão com base nas mudanças
- Atualiza o número de versão no código
- Cria uma tag git e release no GitHub
- Gera changelog automaticamente

### 3. Deploy (publish.yml)

Acionado em novas releases:
- Constrói o pacote Python
- Envia para o AWS CodeArtifact
- Envios notificações sobre o deploy

### Modificando os Fluxos de Trabalho

Se você precisa modificar os fluxos de trabalho:
1. Edite os arquivos YAML em `.github/workflows/`
2. Teste suas mudanças em um fork antes de enviar um PR
3. Documentar as mudanças no PR

## Problemas Comuns de Desenvolvimento

### Isolando Problemas

Use ambientes virtuais separados para testar diferentes configurações:

```bash
python -m venv venv_test
source venv_test/bin/activate
pip install -e .

# Teste a funcionalidade isoladamente
python -c "from microdetect.module import function; function()"
```

### Depurando Código

Use bibliotecas de debug como `pdb` ou `ipdb`:

```python
import ipdb

def problematic_function():
    # ...código...
    ipdb.set_trace()  # Ponto de interrupção
    # ...mais código...
```

Ou use o VSCode ou PyCharm para debugging visual.

### Profiling

Para identificar gargalos de desempenho:

```python
import cProfile
import pstats

# Executa o profile
cProfile.run('function_to_profile()', 'stats.prof')

# Analisa os resultados
p = pstats.Stats('stats.prof')
p.sort_stats('cumulative').print_stats(20)
```

## Recursos para Desenvolvedores

### Referências Úteis

- [Documentação do Ultralytics YOLOv8](https://docs.ultralytics.com/)
- [Tutorial do PyTorch](https://pytorch.org/tutorials/)
- [Documentação do AWS CodeArtifact](https://docs.aws.amazon.com/codeartifact/)
- [Guia do PEP 8](https://peps.python.org/pep-0008/)
- [Guia de Type Hints](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)

### Ferramentas Recomendadas

- **IDE**: VSCode ou PyCharm
- **Terminal**: iTerm2 (macOS) ou Windows Terminal
- **Git GUI**: GitKraken, SourceTree ou VSCode Git
- **Diff Tools**: Meld ou Beyond Compare
- **Visualização de Dados**: Matplotlib, Seaborn

## Contato e Suporte

Para dúvidas ou suporte durante o desenvolvimento:

- Criar um issue no GitHub
- Contatar a equipe: dev@rodolfodebonis.com.br