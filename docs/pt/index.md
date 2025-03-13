# Documentação do MicroDetect

Bem-vindo ao portal de documentação do MicroDetect. Aqui você encontrará guias abrangentes e informações para aproveitar ao máximo o MicroDetect.

## O que é o MicroDetect?

**MicroDetect** é um conjunto especializado de ferramentas para detecção e classificação de microorganismos em imagens de microscopia usando o framework de detecção de objetos YOLOv8. Ele fornece um fluxo de trabalho completo, desde a preparação de imagens até a avaliação do modelo, projetado especificamente para aplicações de microscopia em microbiologia, biotecnologia e áreas relacionadas.

## Principais Funcionalidades

<div class="feature-grid">
  <div class="feature-card">
    <h3>🔍 Conversão de Imagens</h3>
    <p>Converta imagens TIFF de microscopia para formatos otimizados para deep learning, com suporte para normalização de 16 bits para 8 bits.</p>
  </div>
  
  <div class="feature-card">
    <h3>🏷️ Anotação Inteligente</h3>
    <p>Interface gráfica amigável para anotação de microorganismos com sessões que podem ser retomadas e acompanhamento de progresso.</p>
  </div>
  
  <div class="feature-card">
    <h3>👁️ Visualização</h3>
    <p>Ferramentas para revisar e validar anotações com filtragem de classes e capacidades de processamento em lote.</p>
  </div>
  
  <div class="feature-card">
    <h3>🔄 Augmentação de Dados</h3>
    <p>Aprimore seus conjuntos de dados com técnicas como ajuste de brilho, rotação, espelhamento e adição de ruído.</p>
  </div>
  
  <div class="feature-card">
    <h3>📊 Gerenciamento de Dataset</h3>
    <p>Organize seus dados em divisões de treino/validação/teste com configuração YOLO adequada.</p>
  </div>
  
  <div class="feature-card">
    <h3>🧠 Treinamento de Modelos</h3>
    <p>Treine modelos YOLOv8 com suporte a checkpoints, parada antecipada e otimização de hiperparâmetros.</p>
  </div>
  
  <div class="feature-card">
    <h3>📈 Avaliação</h3>
    <p>Métricas abrangentes de avaliação, matrizes de confusão e relatórios visuais para avaliação de modelos.</p>
  </div>
  
  <div class="feature-card">
    <h3>🔍 Análise de Erros</h3>
    <p>Análise detalhada de falsos positivos, falsos negativos e outros erros de detecção para melhorar o desempenho do modelo.</p>
  </div>
  
  <div class="feature-card">
    <h3>📊 Análise Estatística</h3>
    <p>Analise distribuição espacial, padrões de tamanho e mudanças temporais nas populações de microorganismos.</p>
  </div>
  
  <div class="feature-card">
    <h3>⚖️ Comparação de Modelos</h3>
    <p>Compare o desempenho em diferentes tamanhos e configurações de modelo para encontrar o equilíbrio ideal.</p>
  </div>
  
  <div class="feature-card">
    <h3>🔄 Validação Cruzada</h3>
    <p>Valide o desempenho do modelo em diferentes divisões de dados com validação cruzada k-fold.</p>
  </div>
  
  <div class="feature-card">
    <h3>⏱️ Benchmarking</h3>
    <p>Meça a velocidade de inferência, throughput e utilização de recursos de hardware para diferentes configurações de modelo.</p>
  </div>
  
  <div class="feature-card">
    <h3>🔄 Atualizações Automáticas</h3>
    <p>Mantenha seu toolkit atualizado com atualizações integradas via AWS CodeArtifact.</p>
  </div>
</div>

## Primeiros Passos

Se você é novo no MicroDetect, recomendamos começar com estes guias:

- [Guia de Instalação](installation_guide.md) - Instruções abrangentes de instalação para diferentes ambientes
- [Solução de Problemas](troubleshooting.md) - Resolva problemas comuns que você pode encontrar

## Estrutura da Documentação

### Seções do Fluxo de Trabalho Principal

1. **Preparação de Imagens**
   - [Guia de Conversão de Imagens](image_conversion.md) - Conversão de imagens de microscopia para formatos adequados
   - [Guia de Pré-processamento](preprocessing.md) - Técnicas de pré-processamento para melhor detecção

2. **Anotação**
   - [Guia de Anotação](annotation_guide.md) - Anotação manual com a interface gráfica
   - [Guia de Visualização](visualization.md) - Visualização e validação de anotações

3. **Gerenciamento de Dataset**
   - [Guia de Gerenciamento de Dataset](dataset_management.md) - Criação de divisões treino/validação/teste
   - [Guia de Augmentação de Dados](data_augmentation.md) - Augmentação de dados para melhor desempenho do modelo

4. **Treinamento**
   - [Guia de Treinamento](training_guide.md) - Treinamento de modelos YOLOv8 com diferentes configurações
   - [Gerenciamento de Checkpoints](checkpoint_management.md) - Retomada de treinamento a partir de checkpoints
   - [Otimização de Hiperparâmetros](hyperparameter_optimization.md) - Otimizando parâmetros do modelo

5. **Avaliação**
   - [Guia de Avaliação Básica](basic_evaluation.md) - Avaliação do desempenho do modelo com métricas
   - [Avaliação e Análise de Modelos](model_evaluation_analysis.md) - Avaliação abrangente de modelos

### Análise Avançada e Ferramentas

1. **Avaliação e Análise de Modelos**
   - [Guia de Avaliação de Modelos](model_evaluation_analysis.md) - Métricas e visualização abrangentes de avaliação de modelos
   - [Guia de Validação Cruzada](cross_validation_benchmarking.md) - Validação cruzada k-fold e análise de estabilidade do modelo
   - [Guia de Benchmarking](cross_validation_benchmarking.md) - Benchmarking de velocidade e utilização de recursos
   - [Guia de Comparação de Modelos](model_comparison.md) - Comparando diferentes modelos e configurações

2. **Análise de Erros**
   - [Guia de Análise de Erros](error_analysis.md) - Identificação e análise de erros de detecção
   - [Análise de Falsos Positivos](error_analysis.md#falsos-positivos) - Compreendendo e reduzindo falsos positivos
   - [Análise de Falsos Negativos](error_analysis.md#falsos-negativos) - Identificando detecções perdidas
   - [Análise de Erros de Classificação](error_analysis.md#erros-de-classificação) - Analisando classificações incorretas

3. **Visualização e Relatórios**
   - [Ferramentas de Visualização](visualization_tools.md) - Ferramentas para visualizar resultados e gerar relatórios
   - [Dashboards Interativos](visualization_tools.md#dashboards-interativos) - Criação de dashboards interativos para exploração de dados
   - [Geração de Relatórios](visualization_tools.md#geração-de-relatórios) - Criando relatórios PDF e CSV
   - [Visualização de Detecções](visualization_tools.md#visualização-de-detecções) - Visualizando resultados de detecção

4. **Análise Estatística**
   - [Guia de Análise Estatística](statistical_analysis.md) - Analisando distribuições, padrões e relacionamentos
   - [Análise de Densidade](statistical_analysis.md#análise-de-densidade) - Analisando concentração de microorganismos
   - [Análise de Distribuição de Tamanho](statistical_analysis.md#análise-de-distribuição-de-tamanho) - Analisando tamanhos de microorganismos
   - [Análise Espacial](statistical_analysis.md#análise-espacial) - Analisando relacionamentos espaciais
   - [Análise Temporal](statistical_analysis.md#análise-temporal) - Rastreando mudanças ao longo do tempo

5. **Processamento em Lote**
   - [Guia de Processamento em Lote](statistical_analysis.md#processamento-em-lote) - Processando grandes conjuntos de dados com eficiência
   - [Processamento Paralelo](statistical_analysis.md#processando-múltiplas-imagens) - Usando múltiplos workers para processamento mais rápido
   - [Funções de Análise Personalizadas](statistical_analysis.md#funções-de-análise-personalizadas) - Criando pipelines de análise personalizados

### Configuração e Personalização

- [Configuração Avançada](advanced_configuration.md) - Opções detalhadas para personalizar o MicroDetect
- [Referência de Arquivo de Configuração](configuration_reference.md) - Referência completa para opções do config.yaml
- [Integração AWS](aws_codeartifact_setup.md) - Configuração do AWS CodeArtifact para atualizações
- [Variáveis de Ambiente](environment_variables.md) - Configurando o MicroDetect com variáveis de ambiente

### Desenvolvimento e Contribuição

- [Guia de Desenvolvimento](development_guide.md) - Informações para desenvolvedores que desejam contribuir
- [Estrutura do Projeto](development_guide.md#visão-geral-da-arquitetura) - Entendendo a estrutura do código-fonte
- [Ambiente de Desenvolvimento](development_guide.md#configurando-o-ambiente-de-desenvolvimento) - Configuração para desenvolvimento
- [Guia de Testes](development_guide.md#testes) - Escrevendo e executando testes
- [Guia de Documentação](development_guide.md#documentação) - Contribuindo para a documentação
- [Modelo de Atualização e Release](update_and_release_model.md) - Compreendendo o gerenciamento de versões

## Interface de Linha de Comando

O MicroDetect fornece uma interface de linha de comando abrangente:

```bash
# Obter ajuda sobre comandos disponíveis
microdetect --help

# Obter ajuda sobre um comando específico
microdetect annotate --help
```

### Comandos Principais

```bash
# Inicializar um novo projeto
microdetect init

# Converter imagens
microdetect convert --input_dir [entrada] --output_dir [saída]

# Anotar imagens
microdetect annotate --image_dir [imagens] --output_dir [anotações]

# Visualizar anotações
microdetect visualize --image_dir [imagens] --label_dir [anotações]

# Preparar dataset
microdetect dataset --source_img_dir [imagens] --source_label_dir [anotações]

# Augmentar dados
microdetect augment --image_dir [imagens] --label_dir [anotações] --factor [número]

# Treinar modelo
microdetect train --dataset_dir [dataset] --model_size [s/m/l/x]

# Avaliar modelo
microdetect evaluate --model_path [modelo.pt] --dataset_dir [dataset]

# Analisar erros
microdetect analyze_errors --model_path [modelo.pt] --dataset_dir [dataset]

# Comparar modelos
microdetect compare_models --model_paths [modelos] --data_yaml [data.yaml]

# Processar detecções em lote
microdetect batch_detect --model_path [modelo.pt] --source [imagens]

# Visualizar detecções interativamente
microdetect visualize_detections --model_path [modelo.pt] --source [imagens]

# Gerar análise estatística
microdetect analyze_distribution --model_path [modelo.pt] --source [imagens]

# Gerar relatórios
microdetect generate_report --results_dir [resultados] --format [pdf/csv]

# Iniciar dashboard
microdetect dashboard --results_dir [resultados]

# Verificar atualizações
microdetect update --check-only

# Visualizar esta documentação
microdetect docs
```

## Requisitos do Sistema

- **Python:** 3.9 ou mais recente
- **RAM:** 4GB mínimo (8GB+ recomendado para treinamento)
- **GPU:** Opcional, mas recomendado para treinamento (suporte a CUDA ou Apple Silicon MPS)
- **Armazenamento:** 2GB mínimo para instalação e uso básico

## Suporte

Se você encontrar problemas ou tiver dúvidas não abordadas nesta documentação:

1. Consulte o [Guia de Solução de Problemas](troubleshooting.md)
2. Pesquise ou abra uma issue no [GitHub](https://github.com/RodolfoBonis/microdetect/issues)
3. Entre em contato com a equipe de desenvolvimento em dev@rodolfodebonis.com.br

---

<div class="footer-note">
  <p>MicroDetect é um projeto de código aberto desenvolvido para auxiliar pesquisadores e profissionais na área de microbiologia e microscopia.</p>
</div>