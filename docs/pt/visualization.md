# Guia de Visualização

Este guia explica como usar as ferramentas de visualização do MicroDetect para revisar anotações e visualizar resultados de detecção.

## Sumário
- [Introdução](#introdução)
- [Visualizando Anotações](#visualizando-anotações)
  - [Visualização Básica](#visualização-básica)
  - [Visualização em Lote](#visualização-em-lote)
  - [Filtragem por Classe](#filtragem-por-classe)
  - [Personalizando a Saída Visual](#personalizando-a-saída-visual)
- [Visualizando Resultados de Detecção](#visualizando-resultados-de-detecção)
  - [Visualização Básica de Detecção](#visualização-básica-de-detecção)
  - [Visualização Interativa](#visualização-interativa)
  - [Dashboard de Detecção](#dashboard-de-detecção)
- [Visualizações Comparativas](#visualizações-comparativas)
  - [Verdade Fundamental vs. Previsões](#verdade-fundamental-vs-previsões)
  - [Comparação de Múltiplos Modelos](#comparação-de-múltiplos-modelos)
- [Exportando Visualizações](#exportando-visualizações)
  - [Salvando Imagens](#salvando-imagens)
  - [Criando Relatórios](#criando-relatórios)
- [Melhores Práticas](#melhores-práticas)
- [Solução de Problemas](#solução-de-problemas)

## Introdução

A visualização é um componente crucial do fluxo de trabalho de detecção de microorganismos. O MicroDetect fornece ferramentas abrangentes de visualização que ajudam você a:

- Revisar e validar anotações
- Visualizar resultados de detecção de modelos treinados
- Comparar previsões do modelo com a verdade fundamental
- Criar relatórios visuais para apresentações e publicações
- Explorar interativamente dados de detecção

Essas ferramentas de visualização suportam tanto revisão de imagem única quanto processamento em lote para conjuntos de dados maiores.

## Visualizando Anotações

### Visualização Básica

Para visualizar anotações para uma única imagem interativamente:

```bash
microdetect visualize --image_dir caminho/para/imagens --label_dir caminho/para/anotacoes
```

Isso abre uma janela mostrando a imagem com anotações sobrepostas. Você pode:
- Navegar pelas imagens usando atalhos de teclado (A/D para anterior/próxima)
- Ampliar/reduzir para inspeção detalhada
- Ver rótulos de classe e caixas delimitadoras
- Filtrar anotações por classe

### Visualização em Lote

Para gerar imagens anotadas para um diretório inteiro:

```bash
microdetect visualize --image_dir caminho/para/imagens --label_dir caminho/para/anotacoes --output_dir caminho/para/saida
```

Isso cria uma cópia de cada imagem com anotações desenhadas nela e as salva no diretório de saída. Isso é útil para:
- Criar uma visão geral do dataset
- Documentar o progresso da anotação
- Gerar material de treinamento
- Garantia de qualidade das anotações

### Filtragem por Classe

Para visualizar apenas classes específicas:

```bash
microdetect visualize --image_dir caminho/para/imagens --label_dir caminho/para/anotacoes --filter_classes 0,1
```

Isso mostra apenas anotações para classes com IDs 0 e 1. Isso é útil quando:
- Focando em tipos específicos de microorganismos
- Verificando anotações para uma classe específica
- Criando documentação específica por classe

### Personalizando a Saída Visual

Você pode personalizar a visualização no `config.yaml`:

```yaml
annotation:
  box_thickness: 2                # Espessura da caixa para visualização
  text_size: 0.5                  # Tamanho do texto para rótulos de classe
  
color_map:
  "0": [0, 255, 0]                # Cor RGB para classe 0
  "1": [0, 0, 255]                # Cor RGB para classe 1
  "2": [255, 0, 0]                # Cor RGB para classe 2
```

Alternativamente, você pode especificar parâmetros de visualização diretamente no comando:

```bash
microdetect visualize --image_dir caminho/para/imagens --label_dir caminho/para/anotacoes --box_thickness 3 --text_size 0.6
```

## Visualizando Resultados de Detecção

### Visualização Básica de Detecção

Para visualizar detecções de um modelo treinado:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens --save_img
```

Isso executa o modelo nas imagens especificadas e salva os resultados de visualização com caixas delimitadoras, rótulos de classe e pontuações de confiança. A saída inclui:
- Imagem original com detecções sobrepostas
- Rótulos de classe
- Pontuações de confiança
- Caixas delimitadoras codificadas por cor

### Visualização Interativa

Para exploração interativa dos resultados de detecção:

```bash
microdetect visualize_detections --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens --interactive
```

O modo interativo permite que você:
- Ajuste o limiar de confiança em tempo real
- Filtre detecções por classe
- Amplie regiões de interesse
- Meça tamanhos de detecção
- Compare diferentes configurações de detecção

### Dashboard de Detecção

Para um dashboard de visualização mais abrangente:

```bash
microdetect dashboard --results_dir runs/detect/exp --port 8050
```

Isso inicia um dashboard baseado na web que fornece:
- Estatísticas resumidas de detecções
- Gráficos de distribuição de classes
- Histogramas de distribuição de tamanho
- Navegador de imagens interativo
- Capacidades de filtragem
- Painel de detalhes de detecção

O dashboard é particularmente útil para analisar grandes conjuntos de resultados de detecção e identificar padrões em várias imagens.

## Visualizações Comparativas

### Verdade Fundamental vs. Previsões

Para comparar previsões do modelo com anotações de verdade fundamental:

```bash
microdetect compare_detections --model_path runs/train/exp/weights/best.pt --source caminho/para/imagens --label_dir caminho/para/anotacoes
```

Esta visualização mostra:
- Verdadeiros Positivos (detecções correspondentes) em verde
- Falsos Positivos (detecções extras) em vermelho
- Falsos Negativos (objetos perdidos) em azul
- Valores de IoU para cada detecção correspondida

Isso ajuda a identificar onde seu modelo está performando bem e onde precisa de melhorias.

### Comparação de Múltiplos Modelos

Para comparar detecções de múltiplos modelos:

```bash
microdetect compare_models --model_paths model1.pt,model2.pt,model3.pt --source caminho/para/imagens --visualization
```

Isso gera uma comparação visual mostrando:
- Detecções de cada modelo com cores diferentes
- Detecções sobrepostas
- Diferenças em pontuações de confiança
- Diferenças na precisão da caixa delimitadora

Isso é útil para selecionar o melhor modelo para sua aplicação ou entender os trade-offs entre diferentes modelos.

## Exportando Visualizações

### Salvando Imagens

Para salvar resultados de visualização:

```bash
microdetect visualize --image_dir caminho/para/imagens --label_dir caminho/para/anotacoes --output_dir caminho/para/visualizacoes --format png
```

Formatos suportados:
- PNG (sem perdas, arquivos maiores)
- JPEG (compressão com perdas, arquivos menores)
- TIFF (alta qualidade, preserva metadados)

### Criando Relatórios

Para gerar um relatório visual em formato PDF:

```bash
microdetect generate_report --results_dir runs/detect/exp --format pdf --output_file relatorio.pdf --include_images
```

Isso cria um relatório abrangente incluindo:
- Estatísticas resumidas
- Visualizações de exemplo
- Gráficos de detecção
- Distribuição de classes
- Distribuição de pontuação de confiança

## Melhores Práticas

1. **Esquema de Cores Consistente**: Use cores consistentes para classes em todas as visualizações

2. **Espessura Apropriada**: Ajuste a espessura da caixa com base na resolução da imagem (mais espessa para imagens de alta resolução)

3. **Incluir Informações de Escala**: Quando possível, inclua informações de escala nas visualizações

4. **Usar Limiar de Confiança Apropriado**: Ajuste o limiar de confiança para mostrar detecções significativas

5. **Interativo Primeiro, Depois Lote**: Use visualização interativa para determinar configurações ideais, depois execute visualização em lote

6. **Incluir Contexto**: Ao criar relatórios, inclua tanto detalhes ampliados quanto visões de contexto

7. **Equilibrar Detalhe e Visão Geral**: Forneça tanto visualizações individuais detalhadas quanto visualizações resumidas

8. **Considerar Daltonismo**: Escolha esquemas de cores que sejam distinguíveis para pessoas com daltonismo

## Solução de Problemas

**Problema**: Visualizações não mostram anotações ou detecções
**Solução**: Verifique caminhos de arquivo e convenções de nomenclatura; verifique se os arquivos de rótulo correspondem aos nomes das imagens

**Problema**: Rótulos de texto são muito pequenos ou muito grandes
**Solução**: Ajuste o parâmetro `text_size` para um valor apropriado para sua resolução de imagem

**Problema**: Cores não correspondem entre diferentes ferramentas de visualização
**Solução**: Defina cores consistentes no config.yaml e verifique se estão sendo aplicadas corretamente

**Problema**: Dashboard falha ao carregar
**Solução**: Verifique se as dependências necessárias estão instaladas (`pip install dash dash-bootstrap-components`)

**Problema**: Imagens de alta resolução causam problemas de desempenho
**Solução**: Redimensione imagens antes da visualização ou use processamento em lote com saída de resolução mais baixa

**Problema**: Geração de relatório PDF falha
**Solução**: Certifique-se de que o wkhtmltopdf está instalado para geração de PDF

**Problema**: Rótulos ou IDs de classe não correspondem às expectativas
**Solução**: Verifique a configuração de classe no config.yaml e verifique se corresponde ao seu dataset

Para mais informações sobre solução de problemas, consulte o [Guia de Solução de Problemas](troubleshooting.md).