# Guia de Anotação

## Visão Geral

O MicroDetect fornece uma ferramenta de anotação poderosa para rotular microorganismos em imagens de microscopia. A ferramenta foi projetada para tornar o processo de anotação eficiente e preciso, com suporte para sugestões automáticas baseadas em modelos YOLO ou técnicas de visão computacional.

## Iniciando a Ferramenta de Anotação

```bash
microdetect annotate --image_dir /caminho/para/imagens --output_dir /caminho/para/labels
```

Opções adicionais:

- `--model_path`: Caminho para um modelo YOLOv8 para gerar sugestões
- `--classes`: Lista de nomes de classes separadas por vírgula (padrão: levedura,fungos,microalgas)
- `--no_cv_fallback`: Desativa o fallback de visão computacional quando o modelo não está disponível

## Controles da Interface

### Controles do Mouse

- **Clique Esquerdo**: Selecionar uma bounding box
- **Clique Esquerdo + Arrastar**: Desenhar uma nova bounding box
- **Clique Direito na Caixa**: Excluir a bounding box selecionada
- **Roda do Mouse**: Aproximar/afastar zoom
- **Roda do Mouse + Ctrl**: Ajustar tamanho da caixa

### Controles do Teclado

- **Teclas de Seta**: Mover a bounding box selecionada
- **Shift + Teclas de Seta**: Redimensionar a bounding box selecionada
- **1, 2, 3, ...**: Mudar a classe da caixa selecionada
- **S**: Salvar anotações
- **Z**: Desfazer última ação
- **Y**: Refazer última ação
- **A**: Alternar sugestões automáticas
- **N**: Ir para próxima imagem
- **P**: Ir para imagem anterior
- **R**: Resetar visão
- **ESC**: Sair da ferramenta de anotação

## Sugestões Automáticas

A ferramenta de anotação pode sugerir automaticamente bounding boxes de duas maneiras:

1. **Modelo YOLOv8**: Quando um modelo treinado está disponível, ele será usado para fornecer sugestões altamente precisas
2. **Fallback de Visão Computacional**: Quando nenhum modelo está disponível ou as detecções do modelo são insuficientes, técnicas avançadas de visão computacional são aplicadas

### Detecção por Visão Computacional

O sistema de fallback usa algoritmos sofisticados para detectar diferentes tipos de microorganismos:

- **Leveduras**: Detectadas usando detecção de círculos e análise de blobs para formas circulares/ovais
- **Fungos**: Detectados usando filtros de Gabor e análise de esqueletos para estruturas filamentosas
- **Microalgas**: Detectadas através de análise de cor (tipicamente esverdeadas) e características de textura

Vários métodos de pré-processamento e segmentação são aplicados para lidar com várias condições de imagem:

- Pré-processamento adaptativo baseado no brilho e contraste da imagem
- Múltiplas técnicas de segmentação (limiarização adaptativa, Otsu, clustering K-means)
- Filtragem avançada para reduzir falsos positivos
- Supressão Não-Máxima para eliminar detecções duplicadas

## Fluxo de Trabalho de Anotação

1. Abra a ferramenta de anotação com seu diretório de imagens
2. Navegue pelas imagens com os botões Próximo/Anterior
3. Use sugestões automáticas ou desenhe caixas manualmente
4. Ajuste e refine as bounding boxes conforme necessário
5. Salve as anotações (feito automaticamente ao navegar entre imagens)
6. Exporte o dataset anotado para treinamento

## Dicas para Anotação Eficiente

- Use um modelo treinado para sugestões sempre que possível
- Comece com um pequeno lote de imagens anotadas manualmente, treine um modelo inicial e use-o para sugerir anotações para o resto do seu dataset
- Revise todas as sugestões automáticas antes de aceitá-las
- Para imagens desafiadoras com baixo contraste ou iluminação incomum, ajuste as sugestões manualmente
- Salve seu trabalho frequentemente
- Use atalhos de teclado para agilizar o processo de anotação

## Recursos Avançados

### Busca e Filtro

Acesse o diálogo de busca para encontrar imagens específicas por nome ou conteúdo de anotação.

### Visualização de Estatísticas

Veja estatísticas sobre seu progresso de anotação, incluindo:
- Número de imagens anotadas
- Número de objetos por classe
- Média de objetos por imagem

### Backup e Recuperação

A ferramenta de anotação cria automaticamente backups das suas sessões de anotação. Se o aplicativo travar, seu trabalho poderá ser recuperado do último backup.

## Exportando Anotações

Após completar as anotações, você pode exportá-las para treinamento:

```bash
microdetect dataset --source_img_dir /caminho/para/imagens --source_label_dir /caminho/para/labels
```

Isso prepara um dataset adequadamente estruturado para treinamento com YOLOv8.

## Exemplo

```bash
# Iniciar anotação com um modelo pré-treinado para sugestões
microdetect annotate --image_dir data/imagens --output_dir data/labels --model_path models/yolov8n.pt

# Exportar anotações para treinamento
microdetect dataset --source_img_dir data/imagens --source_label_dir data/labels
```