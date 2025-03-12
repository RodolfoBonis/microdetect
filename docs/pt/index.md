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
   - Conversão de imagens de microscopia para formatos adequados
   - Técnicas de pré-processamento para melhor detecção

2. **Anotação**
   - Anotação manual com a interface gráfica
   - Visualização e validação de anotações

3. **Gerenciamento de Dataset**
   - Criação de divisões treino/validação/teste
   - Augmentação de dados para melhor desempenho do modelo

4. **Treinamento**
   - Treinamento de modelos YOLOv8 com diferentes configurações
   - Retomada de treinamento a partir de checkpoints
   - Otimização de hiperparâmetros

5. **Avaliação**
   - Avaliação do desempenho do modelo com métricas
   - Geração de relatórios e visualizações

### Configuração e Personalização

- [Configuração Avançada](advanced_configuration.md) - Opções detalhadas para personalizar o MicroDetect
- [Integração AWS](aws_codeartifact_setup.md) - Configuração do AWS CodeArtifact para atualizações

### Desenvolvimento e Contribuição

- [Guia de Desenvolvimento](development_guide.md) - Informações para desenvolvedores que desejam contribuir
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