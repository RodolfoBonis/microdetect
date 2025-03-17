# Guia de Anotação

Este guia explica como usar as ferramentas de anotação do MicroDetect para rotular microorganismos em imagens de microscopia.

## Sumário
- [Introdução](#introdução)
- [Ferramenta de Anotação](#ferramenta-de-anotação)
  - [Iniciando a Ferramenta de Anotação](#iniciando-a-ferramenta-de-anotação)
  - [Visão Geral da Interface](#visão-geral-da-interface)
  - [Fluxo de Trabalho de Anotação](#fluxo-de-trabalho-de-anotação)
  - [Atalhos de Teclado](#atalhos-de-teclado)
  - [Salvamento Automático e Acompanhamento de Progresso](#salvamento-automático-e-acompanhamento-de-progresso)
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

A anotação precisa de imagens de microscopia é uma etapa crítica no desenvolvimento de modelos eficazes de detecção de microorganismos. O MicroDetect fornece uma ferramenta de anotação especializada projetada especificamente para anotar microorganismos em imagens de microscopia, com recursos como:

1. Interface amigável com controles familiares
2. Sessões de anotação que podem ser retomadas
3. Acompanhamento de progresso
4. Salvamento automático para evitar perda de dados
5. Suporte para múltiplas classes de microorganismos
6. Atalhos de teclado para fluxo de trabalho eficiente

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

![Interface de Anotação](https://example.com/annotation_interface.png)

### Fluxo de Trabalho de Anotação

1. **Carregar Imagem**: A ferramenta carrega uma imagem do diretório especificado
2. **Selecionar Classe**: Escolha a classe de microorganismo apropriada no menu suspenso
3. **Desenhar Caixa Delimitadora**: Clique e arraste para criar uma caixa ao redor do microorganismo
4. **Ajustar Caixa**: Refine a posição e tamanho da caixa se necessário
5. **Adicionar Mais Objetos**: Repita os passos 2-4 para microorganismos adicionais
6. **Salvar Anotações**: As anotações são salvas automaticamente ou pressione 'S' para salvar manualmente
7. **Navegar**: Use os botões de navegação ou atalhos de teclado para mover para a próxima/anterior imagem

Dicas para anotação eficaz:
- Desenhe caixas delimitadoras ajustadas em torno de cada microorganismo
- Para microorganismos agrupados, anote cada um individualmente se forem distinguíveis
- Seja consistente na anotação em todas as imagens
- Use zoom para microorganismos pequenos
- Use atalhos de teclado para agilizar o processo

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

Esses atalhos tornam o processo de anotação mais rápido e eficiente, especialmente ao anotar grandes conjuntos de dados.

### Salvamento Automático e Acompanhamento de Progresso

A ferramenta de anotação salva automaticamente seu trabalho para prevenir perda de dados:

- Anotações são salvas no formato YOLO (arquivos .txt) no diretório de saída
- O progresso é acompanhado em um arquivo `.annotation_progress.json`
- Ao reiniciar a ferramenta com os mesmos diretórios, você pode continuar de onde parou
- Um backup das versões anteriores de anotação é mantido em caso de erros

Para retomar uma sessão de anotação:

```bash
microdetect annotate --image_dir caminho/para/imagens --output_dir caminho/para/anotacoes --resume
```

## Gerenciando Dados de Anotação

### Formato YOLO

O MicroDetect usa o formato de anotação YOLO:
- Cada imagem tem um arquivo .txt correspondente com o mesmo nome
- Cada linha no arquivo .txt representa um objeto no formato:
  ```
  class_id center_x center_y width height
  ```
- Todos os valores são normalizados para o intervalo [0,1]
- Exemplo: `0 0.5 0.5 0.1 0.2` representa um objeto da classe 0 no centro da imagem com largura 10% e altura 20% das dimensões da imagem

Exemplo de arquivo de anotação para uma imagem contendo três microorganismos (dois da classe 0 e um da classe 1):
```
0 0.762 0.451 0.112 0.087
0 0.245 0.321 0.098 0.076
1 0.542 0.622 0.156 0.143
```

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

Essas conversões podem ser úteis ao integrar com outras ferramentas ou frameworks que requerem diferentes formatos de anotação.

### Fazendo Backup das Anotações

É recomendável fazer backup regularmente dos seus arquivos de anotação:

```bash
# Criar um backup com timestamp
backup_dir="backup_anotacoes_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
cp -r caminho/para/anotacoes/* "$backup_dir"
```

Você também pode usar sistemas de controle de versão como Git para rastrear mudanças nos seus arquivos de anotação.

## Melhores Práticas

### Consistência nas Anotações

Para melhores resultados:
- Defina diretrizes claras de anotação antes de começar
- Seja consistente em como você anota objetos similares
- Para microorganismos agrupados, decida se vai anotá-los individualmente ou como grupo
- Considere usar um processo de validação onde múltiplos anotadores revisam as mesmas imagens

Exemplo de diretrizes de anotação:
1. Sempre desenhe caixas delimitadoras ajustadas que contenham o microorganismo completo
2. Para microorganismos parcialmente visíveis nas bordas da imagem, inclua a parte visível
3. Para microorganismos sobrepostos, anote cada um separadamente se os limites estiverem claros
4. Para microorganismos fora de foco, anote apenas aqueles que estão claramente visíveis
5. Use atribuições de classe consistentes para microorganismos de aparência semelhante

### Lidando com Casos Difíceis

Para imagens desafiadoras:
- Use zoom para microorganismos pequenos
- Para objetos parcialmente visíveis nas bordas da imagem, inclua a parte visível
- Para microorganismos em diferentes planos focais, anote aqueles que estão claramente em foco
- Documente casos especiais para referência

Para imagens muito aglomeradas:
- Considere dividir a anotação em múltiplas sessões para evitar fadiga
- Use o recurso de zoom para focar em regiões específicas
- Seja metódico ao cobrir todas as áreas da imagem (ex., trabalhe de cima para baixo)

### Controle de Qualidade

Verifique regularmente a qualidade das anotações:
- Use a ferramenta de visualização para revisar anotações
- Verifique se há microorganismos não anotados ou classificações incorretas
- Confirme que as caixas delimitadoras estão ajustadas corretamente aos microorganismos
- Revise a distribuição de classes para garantir um dataset balanceado

Estabeleça um processo de validação:
- Peça a outra pessoa para revisar uma amostra das anotações
- Compare anotações entre anotadores para estabelecer consistência
- Crie um guia de referência com exemplos de imagens corretamente anotadas

## Solução de Problemas

**Problema**: Ferramenta de anotação não inicia
**Solução**: Verifique se o Tkinter está instalado (`pip install tk`) e se você está usando um ambiente com suporte a display

**Problema**: Anotações não estão sendo salvas
**Solução**: Verifique as permissões e caminhos do diretório; use caminhos absolutos se necessário

**Problema**: Não é possível ver anotações ao revisar
**Solução**: Verifique se o nome do arquivo de anotação corresponde ao nome da imagem (sem extensão)

**Problema**: Problemas de desempenho com imagens grandes
**Solução**: Redimensione imagens grandes para um tamanho gerenciável antes da anotação

**Problema**: Acompanhamento de progresso incompleto
**Solução**: Verifique e remova arquivos `.annotation_progress.json` vazios

**Problema**: Difícil desenhar anotações precisas
**Solução**: Use o recurso de zoom para obter uma visão mais detalhada; ajuste as caixas após o desenho inicial

**Problema**: Classes faltando no menu suspenso
**Solução**: Verifique se as classes estão definidas corretamente no config.yaml ou use o parâmetro `--classes`

Para mais problemas, consulte o [Guia de Solução de Problemas](troubleshooting.md).