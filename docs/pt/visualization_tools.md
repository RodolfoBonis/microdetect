# Guia de Ferramentas de Visualização

Este guia explica as capacidades de visualização e geração de relatórios do MicroDetect para análise de resultados de detecção.

## Sumário
- [Introdução](#introdução)
- [Visualização de Detecções](#visualização-de-detecções)
  - [Visualização Básica](#visualização-básica)
  - [Visualização Interativa](#visualização-interativa)
  - [Processamento em Lote](#processamento-em-lote)
- [Geração de Relatórios](#geração-de-relatórios)
  - [Relatórios PDF](#relatórios-pdf)
  - [Relatórios CSV](#relatórios-csv)
  - [Exportando para Formato YOLO](#exportando-para-formato-yolo)
- [Dashboards Interativos](#dashboards-interativos)
  - [Dashboard de Detecção](#dashboard-de-detecção)
  - [Dashboard de Comparação de Modelos](#dashboard-de-comparação-de-modelos)
- [Visualizações Estatísticas](#visualizações-estatísticas)
  - [Mapas de Densidade](#mapas-de-densidade)
  - [Distribuição de Tamanho](#distribuição-de-tamanho)
  - [Análise Espacial](#análise-espacial)
- [Personalização](#personalização)
- [Melhores Práticas](#melhores-práticas)
- [Solução de Problemas](#solução-de-problemas)

## Introdução

O MicroDetect fornece um conjunto abrangente de ferramentas de visualização e geração de relatórios para ajudá-lo a compreender, interpretar e apresentar resultados de detecção. Essas ferramentas permitem:

- Visualizar detecções em imagens
- Criar dashboards interativos para exploração de dados
- Gerar relatórios profissionais em formatos PDF e CSV
- Realizar análise estatística de padrões de detecção
- Comparar visualmente diferentes modelos

Essas visualizações ajudam a fazer a ponte entre dados brutos e insights acionáveis, facilitando a comunicação de resultados e a tomada de decisões informadas.

## Visualização de Detecções

### Visualização Básica

O comando `visualize_detections` permite visualizar resultados de detecção em imagens:

```bash
microdetect visualize_detections --model_path runs/train/exp/weights/best.pt \
                                --source caminho/para/imagens \
                                --conf_threshold 0.25
```

Isso abre uma janela interativa onde você pode:
- Ver detecções com caixas delimitadoras e rótulos
- Navegar pelas imagens usando controles de teclado
- Ajustar o limiar de confiança em tempo real
- Ver pontuações de confiança de detecção

**Controles de Teclado:**
- `n`: Próxima imagem
- `p`: Imagem anterior
- `+`: Aumentar limiar de confiança
- `-`: Diminuir limiar de confiança
- `q`: Sair da visualização

### Visualização Interativa

Para uma exploração mais detalhada de uma única imagem:

```bash
microdetect visualize_detections --model_path runs/train/exp/weights/best.pt \
                                --source caminho/para/imagem_unica.jpg \
                                --interactive
```

O modo interativo fornece recursos adicionais:
- Ampliação de regiões de interesse
- Exibição de informações estendidas sobre cada detecção
- Comparação com a verdade fundamental (se disponível)
- Salvamento de visualizações específicas em arquivos

### Processamento em Lote

Processe múltiplas imagens e salve os resultados da visualização:

```bash
microdetect batch_detect --model_path runs/train/exp/weights/best.pt \
                        --source caminho/para/imagens \
                        --output_dir caminho/para/saida \
                        --save_img \
                        --batch_size 16
```

Opções:
- `--save_img`: Salvar imagens com sobreposições de detecção
- `--save_txt`: Salvar resultados de detecção no formato YOLO
- `--save_json`: Salvar resultados de detecção no formato JSON
- `--batch_size`: Número de imagens a processar em cada lote
- `--conf_threshold`: Limiar de confiança para detecções

## Geração de Relatórios

### Relatórios PDF

Gere relatórios PDF abrangentes dos resultados de avaliação do modelo:

```bash
microdetect generate_report --results_dir runs/detect/exp \
                          --output_file relatorio.pdf \
                          --format pdf \
                          --include_images "img1.jpg,img2.jpg"
```

O relatório PDF inclui:
- Informações do modelo e métricas de desempenho
- Métricas específicas por classe (precisão, recall, F1-score)
- Visualizações de métricas-chave
- Imagens de exemplo de detecção (se especificadas)
- Estatísticas resumidas e gráficos

### Relatórios CSV

Exporte métricas e resultados em formato CSV para análise adicional:

```bash
microdetect generate_report --results_dir runs/detect/exp \
                          --output_file metricas.csv \
                          --format csv
```

A exportação CSV inclui:
- Métricas gerais (mAP50, mAP50-95, recall, precisão)
- Métricas por classe
- Dados brutos para análise personalizada em software de planilha

### Exportando para Formato YOLO

Exporte resultados de detecção no formato de anotação YOLO:

```bash
microdetect batch_detect --model_path runs/train/exp/weights/best.pt \
                        --source caminho/para/imagens \
                        --save_txt \
                        --output_dir caminho/para/saida
```

Isso cria arquivos de texto no formato YOLO para cada imagem, com uma linha por detecção:
```
id_classe centro_x centro_y largura altura
```

Este formato é compatível com treinamento YOLO e outras ferramentas que usam anotações YOLO.

## Dashboards Interativos

### Dashboard de Detecção

Inicie um dashboard web interativo para explorar resultados de detecção:

```bash
microdetect dashboard --results_dir runs/detect/exp \
                     --port 8050
```

O dashboard de detecção fornece:
- Visualização filtrável de detecções por classe e confiança
- Histogramas de pontuações de confiança
- Gráficos mostrando contagens de detecção por classe
- Painel de detalhes para explorar imagens individuais
- Gráficos de dispersão de tamanho vs. confiança

### Dashboard de Comparação de Modelos

Compare múltiplos modelos com um dashboard interativo:

```bash
microdetect dashboard --comparison_file resultados_comparacao_modelos.json \
                     --port 8051
```

O dashboard de comparação inclui:
- Comparação lado a lado de métricas
- Visualização do trade-off desempenho vs. velocidade
- Comparação de tamanho de modelo
- Seleção interativa de métricas
- Tabelas de comparação detalhadas

## Visualizações Estatísticas

O MicroDetect fornece ferramentas para análise estatística de padrões de detecção:

### Mapas de Densidade

Gere mapas de calor mostrando a densidade de detecções nas imagens:

```bash
microdetect analyze_distribution --model_path runs/train/exp/weights/best.pt \
                               --source caminho/para/imagens \
                               --output_dir mapas_densidade
```

Mapas de densidade ajudam a visualizar:
- Áreas com alta concentração de microorganismos
- Padrões de distribuição nas imagens
- Padrões de distribuição específicos por classe (quando usando `--by_class`)

### Distribuição de Tamanho

Analise e visualize a distribuição de tamanho dos objetos detectados:

```bash
microdetect analyze_size --model_path runs/train/exp/weights/best.pt \
                        --source caminho/para/imagens \
                        --output_dir analise_tamanho
```

A análise de distribuição de tamanho fornece:
- Histogramas de tamanhos de objetos
- Distribuições de tamanho específicas por classe
- Resumos estatísticos (média, mediana, intervalo)
- Identificação de outliers

### Análise Espacial

Analise relações espaciais entre objetos detectados:

```bash
microdetect analyze_spatial --model_path runs/train/exp/weights/best.pt \
                          --source caminho/para/imagens \
                          --output_dir analise_espacial
```

A análise espacial inclui:
- Distribuições de distância do vizinho mais próximo
- Análise de agrupamento
- Correlação espacial entre diferentes classes
- Visualização de padrões espaciais

## Personalização

### Personalizando Visualizações

Você pode personalizar vários aspectos das visualizações:

```bash
microdetect visualize_detections --model_path modelo.pt \
                                --source imagens/ \
                                --conf_threshold 0.25 \
                                --line_thickness 2 \
                                --font_scale 0.6 \
                                --show_labels True
```

Opções:
- `--line_thickness`: Espessura das linhas das caixas delimitadoras
- `--font_scale`: Tamanho dos rótulos de texto
- `--show_labels`: Se deve exibir rótulos de classe e pontuações de confiança

### Personalizando Relatórios

Para relatórios PDF, você pode fornecer um modelo HTML personalizado:

```bash
microdetect generate_report --results_dir runs/detect/exp \
                          --output_file relatorio.pdf \
                          --format pdf \
                          --template_path meu_modelo.html
```

O modelo usa sintaxe Jinja2 e tem acesso a:
- `model_name`: Nome do modelo
- `model_path`: Caminho para o arquivo do modelo
- `date`: Data de geração do relatório
- `general_metrics`: Dicionário de métricas gerais
- `class_metrics`: Lista de métricas por classe
- `images`: Lista de caminhos de imagens incluídas

## Melhores Práticas

1. **Use processamento em lote para grandes conjuntos de dados**: Ao processar muitas imagens, use detecção em lote com tamanho de lote apropriado

2. **Gere relatórios com exemplos**: Inclua imagens representativas em relatórios PDF para fornecer contexto

3. **Comece com visualização interativa**: Use visualização interativa para explorar resultados antes de gerar relatórios estáticos

4. **Combine tipos de visualização**: Use múltiplos tipos de visualização para obter uma compreensão completa dos seus resultados

5. **Personalize para seu público**: Adapte relatórios e visualizações com base no conhecimento técnico do seu público

6. **Salve resultados intermediários**: Salve resultados JSON ao executar detecção em lote para permitir análises futuras sem precisar executar o modelo novamente

## Solução de Problemas

### Problema: Visualizações muito congestionadas com muitas detecções
**Solução**: Aumente o limiar de confiança para mostrar apenas detecções de alta confiança

### Problema: Geração de relatório PDF falha
**Solução**: Certifique-se de que o wkhtmltopdf está instalado no seu sistema (necessário pelo pdfkit)

### Problema: Dashboard não carrega no navegador
**Solução**: Verifique se a porta especificada já está em uso; tente uma porta diferente

### Problema: Imagens em relatórios PDF aparecem distorcidas
**Solução**: Verifique as dimensões da imagem; imagens muito grandes podem precisar ser redimensionadas antes da inclusão

### Problema: Dados ausentes em dashboards
**Solução**: Certifique-se de que seus resultados de detecção tenham todos os campos necessários; verifique o formato JSON

Para mais informações sobre solução de problemas, consulte o [Guia de Solução de Problemas](troubleshooting.md).