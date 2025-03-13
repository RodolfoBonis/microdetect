# Guia de Visualização e Anotação

Este guia explica como usar as ferramentas do MicroDetect para anotar imagens de microorganismos e visualizar anotações.

## Sumário
- [Introdução](#introdução)
- [Ferramenta de Anotação](#ferramenta-de-anotação)
  - [Iniciando a Ferramenta de Anotação](#iniciando-a-ferramenta-de-anotação)
  - [Visão Geral da Interface](#visão-geral-da-interface)
  - [Fluxo de Trabalho de Anotação](#fluxo-de-trabalho-de-anotação)
  - [Atalhos de Teclado](#atalhos-de-teclado)
  - [Salvamento Automático e Acompanhamento de Progresso](#salvamento-automático-e-acompanhamento-de-progresso)
- [Ferramenta de Visualização](#ferramenta-de-visualização)
  - [Visualizando Imagens Individuais](#visualizando-imagens-individuais)
  - [Visualização em Lote](#visualização-em-lote)
  - [Filtragem por Classe](#filtragem-por-classe)
  - [Personalizando a Saída Visual](#personalizando-a-saída-visual)
  - [Atalhos de Teclado para Visualização](#atalhos-de-teclado-para-visualização)
- [Gerenciando Dados de Anotação](#gerenciando-dados-de-anotação)
  - [Formato YOLO](#formato-yolo)
  - [Convertendo para Outros Formatos](#convertendo-para-outros-formatos)
  - [Fazendo Backup das Anotações](#fazendo-backup-das-anotações)
- [Melhores Práticas](#melhores-práticas)
  - [Consistência nas Anotações](#consistência-nas-anotações)
  - [Lidando com Casos Difíceis](#lidando-com-casos-difíceis)
  - [Controle de Qualidade](#controle-de-qualidade)
- [Solução de Problemas](#solução-de-problemas)

## Introdução

O MicroDetect fornece ferramentas especializadas para anotar microorganismos em imagens de microscopia e visualizar essas anotações. Este processo é crucial para:

1. Criar datasets de treinamento para modelos de aprendizado de máquina
2. Validar resultados de detecção
3. Analisar a distribuição de microorganismos

O fluxo de trabalho geralmente envolve duas etapas separadas:
- **Anotação**: Criação e edição de caixas delimitadoras ao redor dos microorganismos
- **Visualização**: Revisão e exame das anotações

## Ferramenta de Anotação

### Iniciando a Ferramenta de Anotação

Para iniciar a ferramenta de anotação, use o seguinte comando:

```bash
microdetect annotate --image_dir caminho/para/imagens --output_dir caminho/para/anotacoes
```

Parâmetros obrigatórios:
- `--image_dir`: Diretório contendo as imagens a serem anotadas
- `--output_dir`: Diretório onde os arquivos de anotação serão salvos

Parâmetros opcionais:
- `--classes`: Lista de nomes de classes separadas por vírgula (padrão: do config.yaml)
- `--resume`: Continuar da última imagem anotada
- `--auto_save`: Habilitar salvamento automático (padrão: true)
- `--auto_save_interval`: Tempo entre salvamentos automáticos em segundos (padrão: 300)

### Visão Geral da Interface

A interface de anotação inclui:

1. **Canvas de Imagem Principal**: Exibe a imagem atual para anotação
2. **Painel de Navegação**: Controles para mover entre as imagens
3. **Seleção de Classe**: Menu suspenso para selecionar a classe do microorganismo
4. **Painel de Ferramentas**: Ferramentas para anotação (Retângulo, Zoom, Pan)
5. **Barra de Status**: Mostra o nome da imagem atual, progresso e status

### Fluxo de Trabalho de Anotação

1. **Carregar Imagem**: A ferramenta carrega uma imagem do diretório especificado
2. **Selecionar Classe**: Escolha a classe de microorganismo apropriada no menu suspenso
3. **Desenhar Caixa Delimitadora**: Clique e arraste para criar uma caixa ao redor do microorganismo
4. **Ajustar Caixa**: Refine a posição e tamanho da caixa se necessário
5. **Adicionar Mais Objetos**: Repita os passos 2-4 para microorganismos adicionais
6. **Salvar Anotações**: As anotações são salvas automaticamente ou pressione 'S' para salvar manualmente
7. **Navegar**: Use os botões de navegação ou atalhos de teclado para mover para a próxima/anterior imagem

### Atalhos de Teclado

A ferramenta de anotação suporta os seguintes atalhos de teclado:

| Tecla | Função |
|-------|----------|
| A | Imagem anterior |
| D | Próxima imagem |
| S | Salvar anotações atuais |
| Z | Desfazer última anotação |
| C | Mudar classe (cicla entre as classes) |
| R | Resetar zoom e pan |
| E | Alternar entre ferramentas de retângulo e movimento |
| Del | Deletar anotação selecionada |
| ESC | Desselecionar todas as anotações |
| Q | Sair da ferramenta de anotação |

### Salvamento Automático e Acompanhamento de Progresso

A ferramenta de anotação salva automaticamente seu trabalho para prevenir perda de dados:

- Anotações são salvas no formato YOLO (arquivos .txt) no diretório de saída
- O progresso é acompanhado em um arquivo `.annotation_progress.json`
- Ao reiniciar a ferramenta com os mesmos diretórios, você pode continuar de onde parou
- Um backup das versões anteriores de anotação é mantido em caso de erros

## Ferramenta de Visualização

### Visualizando Imagens Individuais

Para visualizar anotações para uma única imagem interativamente:

```bash
microdetect visualize --image_dir caminho/para/imagens --label_dir caminho/para/anotacoes
```

Isso abre uma janela mostrando a imagem com as anotações sobrepostas.

### Visualização em Lote

Para gerar imagens anotadas para um diretório inteiro:

```bash
microdetect visualize --image_dir caminho/para/imagens --label_dir caminho/para/anotacoes --output_dir caminho/para/saida
```

Isso cria uma cópia de cada imagem com anotações desenhadas nela e as salva no diretório de saída.

### Filtragem por Classe

Para visualizar apenas classes específicas:

```bash
microdetect visualize --image_dir caminho/para/imagens --label_dir caminho/para/anotacoes --filter_classes 0,1
```

Isso mostra apenas anotações para classes com IDs 0 e 1.

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

### Atalhos de Teclado para Visualização

A ferramenta de visualização suporta os seguintes atalhos de teclado:

| Tecla | Função |
|-------|----------|
| A | Imagem anterior |
| D | Próxima imagem |
| P | Alternar modo navegação |
| R | Resetar zoom e pan |
| 0-9 | Alternar visibilidade da classe |
| S | Salvar imagem atual |
| Q | Sair da ferramenta de visualização |

## Gerenciando Dados de Anotação

### Formato YOLO

O MicroDetect usa o formato de anotação YOLO:
- Cada imagem tem um arquivo .txt correspondente com o mesmo nome
- Cada linha no arquivo .txt representa um objeto no formato:
  ```
  class_id center_x center_y width height
  ```
- Todos os valores são normalizados para o intervalo [0,1]
- Exemplo: `0 0.5 0.5 0.1 0.2` representa um objeto da classe 0 no centro da imagem

### Convertendo para Outros Formatos

Para converter anotações para outros formatos, use o módulo de conversão:

```python
from microdetect.utils.convert_annotations import yolo_to_pascal_voc

# Converter formato YOLO para formato Pascal VOC
yolo_to_pascal_voc("caminho/para/anotacoes", "caminho/para/imagens", "caminho/para/saida_xml")
```

Conversões suportadas:
- YOLO ↔ Pascal VOC
- YOLO ↔ COCO
- YOLO ↔ CSV

### Fazendo Backup das Anotações

É recomendável fazer backup regularmente dos seus arquivos de anotação:

```bash
# Criar um backup com timestamp
backup_dir="backup_anotacoes_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
cp -r caminho/para/anotacoes/* "$backup_dir"
```

## Melhores Práticas

### Consistência nas Anotações

Para melhores resultados:
- Defina diretrizes claras de anotação antes de começar
- Seja consistente em como você anota objetos similares
- Para microorganismos agrupados, decida se vai anotá-los individualmente ou como grupo
- Considere usar um processo de validação onde múltiplos anotadores revisam as mesmas imagens

### Lidando com Casos Difíceis

Para imagens desafiadoras:
- Use zoom para microorganismos pequenos
- Para objetos parcialmente visíveis nas bordas da imagem, inclua a parte visível
- Para microorganismos em diferentes planos focais, anote aqueles que estão claramente em foco
- Documente casos especiais para referência

### Controle de Qualidade

Verifique regularmente a qualidade das anotações:
- Use a ferramenta de visualização para revisar anotações
- Verifique se há microorganismos não anotados ou classificações incorretas
- Confirme que as caixas delimitadoras estão ajustadas corretamente aos microorganismos
- Revise a distribuição de classes para garantir um dataset balanceado

## Solução de Problemas

**Problema**: Ferramenta de anotação não inicia
**Solução**: Verifique se o Tkinter está instalado (`pip install tk`) e se você está usando um ambiente com suporte a display

**Problema**: Anotações não estão sendo salvas
**Solução**: Verifique as permissões e caminhos do diretório; use caminhos absolutos se necessário

**Problema**: Caixas de anotação não são visíveis na visualização
**Solução**: Verifique se o nome do arquivo de anotação corresponde ao nome da imagem (sem extensão)

**Problema**: Problemas de desempenho com imagens grandes
**Solução**: Redimensione imagens grandes para um tamanho gerenciável antes da anotação

**Problema**: Acompanhamento de progresso incompleto
**Solução**: Verifique e remova arquivos `.annotation_progress.json` vazios

Para mais problemas, consulte o [Guia de Solução de Problemas](troubleshooting.md).