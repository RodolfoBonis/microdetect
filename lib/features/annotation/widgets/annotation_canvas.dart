import 'dart:async';
import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/annotation/controllers/annotation_controller.dart';
import 'package:microdetect/features/annotation/models/annotation.dart';

import 'package:vector_math/vector_math_64.dart' as vector_math;

/// Widget para visualizar e desenhar anotações sobre uma imagem
class AnnotationCanvas extends StatefulWidget {
  /// URL da imagem a ser anotada
  final String imageUrl;

  /// Dimensões desejadas para o canvas
  final Size size;

  /// Quando true, permite criar novas anotações
  final bool editable;

  const AnnotationCanvas({
    Key? key,
    required this.imageUrl,
    required this.size,
    this.editable = true,
  }) : super(key: key);

  @override
  State<AnnotationCanvas> createState() => _AnnotationCanvasState();
}

class _AnnotationCanvasState extends State<AnnotationCanvas>
    with TickerProviderStateMixin {
  /// Controlador de anotação
  late AnnotationController controller;

  /// Imagem carregada
  ui.Image? _image;

  /// Indicador de carregamento
  bool _isLoading = true;

  /// Erro durante o carregamento
  String? _error;

  /// Flag para controlar se estamos em modo de panorâmica ou anotação
  bool _isPanningMode = false;

  /// Key para o foco do teclado
  final FocusNode _canvasFocusNode = FocusNode();

  /// Controlador de animação para feedback visual
  late AnimationController _pulseController;

  /// Último ponto de clique para detectar duplo-clique
  Offset? _lastTapPosition;
  DateTime? _lastTapTime;

  /// Flag para indicar se estamos em movimento de drag (para prevenir conflitos)
  bool _isDragging = false;

  /// Armazenar o estado inicial da operação para usar em onPointerMove
  AnnotationEditorState? _initialDragState;

  /// Armazenar o índice do canto que está sendo redimensionado
  int _resizingCornerIndex = -1;

  /// Indica se uma operação de redimensionamento está em andamento
  bool _isResizingActive = false;

  @override
  void initState() {
    super.initState();
    controller = Get.find<AnnotationController>();

    // Inicializar o controlador de animação
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    )..repeat(reverse: true);

    // Carregar imagem
    _loadImage();

    // Focar o nó para capturar eventos de teclado
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _canvasFocusNode.requestFocus();
      controller.setViewportSize(widget.size);
    });
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _canvasFocusNode.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(AnnotationCanvas oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (widget.size != oldWidget.size) {
      controller.setViewportSize(widget.size);
    }

    if (widget.imageUrl != oldWidget.imageUrl) {
      // Nova imagem carregada
      _loadImage();
    }
  }

  /// Carrega a imagem a partir da URL
  Future<void> _loadImage() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final NetworkImage provider = NetworkImage(widget.imageUrl);
      final ImageStream stream = provider.resolve(const ImageConfiguration());

      final Completer<ui.Image> completer = Completer<ui.Image>();
      final ImageStreamListener listener = ImageStreamListener(
        (ImageInfo info, bool _) {
          completer.complete(info.image);
        },
        onError: (dynamic exception, StackTrace? stackTrace) {
          completer.completeError(exception);
        },
      );

      stream.addListener(listener);

      final ui.Image image = await completer.future;

      if (mounted) {
        setState(() {
          _image = image;
          _isLoading = false;
        });

        // Atualizar o controlador com a imagem carregada
        controller.setLoadedImage(image);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _error = 'Erro ao carregar imagem: $e';
        });
      }
    }
  }

  /// Processa eventos de teclado
  void _handleKeyEvent(KeyEvent event) {
    if (!widget.editable) return;

    if (event is KeyDownEvent) {
      if (event.logicalKey == LogicalKeyboardKey.escape) {
        // Cancelar seleção atual
        controller.cancelSelection();
      } else if (event.logicalKey == LogicalKeyboardKey.delete ||
          event.logicalKey == LogicalKeyboardKey.backspace) {
        // Deletar anotação selecionada
        if (controller.selectedAnnotation.value != null) {
          controller.deleteSelectedAnnotation();
        }
      } else if ((event.logicalKey == LogicalKeyboardKey.keyZ) &&
          (HardwareKeyboard.instance.isControlPressed ||
              HardwareKeyboard.instance.isMetaPressed)) {
        // Ctrl/Cmd+Z para desfazer (implementação futura)
      } else if ((event.logicalKey == LogicalKeyboardKey.keyS) &&
          (HardwareKeyboard.instance.isControlPressed ||
              HardwareKeyboard.instance.isMetaPressed)) {
        // Ctrl/Cmd+S para salvar
        controller.saveAllAnnotations();
      }
    }
  }

  /// Verifica se é duplo-clique
  bool _isDoubleClick(Offset position) {
    final now = DateTime.now();
    final bool isDoubleClick = _lastTapPosition != null &&
        (position - _lastTapPosition!).distance < 20 &&
        _lastTapTime != null &&
        now.difference(_lastTapTime!).inMilliseconds < 300;

    // Atualizar últimos valores
    _lastTapPosition = position;
    _lastTapTime = now;

    return isDoubleClick;
  }

  /// Exibe diálogo de edição de anotação
  void _showAnnotationEditDialog(Annotation annotation) {
    Get.dialog(
      AlertDialog(
        title: const Text('Editar Anotação'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DropdownButtonFormField<String>(
              decoration: const InputDecoration(
                labelText: 'Classe',
              ),
              value: annotation.className,
              items: controller.classes.map((className) {
                return DropdownMenuItem<String>(
                  value: className,
                  child: Text(className),
                );
              }).toList(),
              onChanged: (value) {
                if (value != null) {
                  controller.selectClass(value);
                }
              },
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.delete, color: Colors.white),
                    label: const Text('Excluir'),
                    style: OutlinedButton.styleFrom(
                      backgroundColor: AppColors.error,
                      foregroundColor: Colors.white,
                    ),
                    onPressed: () {
                      Get.back();
                      controller.deleteSelectedAnnotation();
                    },
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              Get.back();
              // Implementar atualização da classe
            },
            child: const Text('Salvar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final bool isDarkMode = Get.isDarkMode;

    if (_isLoading) {
      return Container(
        width: widget.size.width,
        height: widget.size.height,
        color: isDarkMode ? Colors.black : Colors.grey[200],
        child: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (_error != null) {
      return Container(
        width: widget.size.width,
        height: widget.size.height,
        color: isDarkMode ? Colors.black : Colors.grey[200],
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, color: AppColors.error, size: 48),
              const SizedBox(height: 16),
              Text(
                _error!,
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _loadImage,
                child: const Text('Tentar novamente'),
              ),
            ],
          ),
        ),
      );
    }

    if (_image == null) {
      return Container(
        width: widget.size.width,
        height: widget.size.height,
        color: isDarkMode ? Colors.black : Colors.grey[200],
      );
    }

    // Nova abordagem: widget de layout com tamanho fixo para manter as proporções da imagem
    return Column(
      children: [
        Container(
          width: widget.size.width,
          height: widget.size.height,
          color: isDarkMode ? Colors.black : Colors.grey[200],
          child: Center(
            child: LayoutBuilder(
              builder: (context, constraints) {
                // Calcular o tamanho da imagem mantendo proporção
                final double imageWidth = _image!.width.toDouble();
                final double imageHeight = _image!.height.toDouble();

                // Escolher o fator de escala para caber no container
                final double scaleX = constraints.maxWidth / imageWidth;
                final double scaleY = constraints.maxHeight / imageHeight;
                final double scale = math.min(scaleX, scaleY);

                // Obter dimensões finais da imagem e do canvas
                final double displayWidth = imageWidth * scale;
                final double displayHeight = imageHeight * scale;

                // Atualizar o controller com as dimensões da visualização
                controller.setViewportSize(Size(displayWidth, displayHeight));

                return SizedBox(
                  width: displayWidth,
                  height: displayHeight,
                  child: Stack(
                    children: [
                      // Camada 1: Imagem base
                      Image.network(
                        widget.imageUrl,
                        fit: BoxFit.contain,
                        width: displayWidth,
                        height: displayHeight,
                      ),

                      // Camada 2: Canvas interativo para anotações
                      KeyboardListener(
                        focusNode: _canvasFocusNode,
                        onKeyEvent: _handleKeyEvent,
                        child: GestureDetector(
                          onTapDown: (details) => _handleTapDown(
                            details.localPosition,
                            displayWidth,
                            displayHeight,
                          ),
                          onPanStart: (details) => _handlePanStart(
                            details.localPosition,
                            displayWidth,
                            displayHeight,
                          ),
                          onPanUpdate: (details) => _handlePanUpdate(
                            details.localPosition,
                            displayWidth,
                            displayHeight,
                          ),
                          onPanEnd: (_) => _handlePanEnd(),
                          child: Obx(() => CustomPaint(
                                size: Size(displayWidth, displayHeight),
                                painter: AnnotationsPainter(
                                  annotations: controller.annotations.toList(),
                                  selectedAnnotation:
                                      controller.selectedAnnotation.value,
                                  classColors: controller.classColors,
                                  pulseAnimation: _pulseController,
                                  resizeCornerIndex: _isResizingActive
                                      ? _resizingCornerIndex
                                      : controller.resizeCornerIndex.value,
                                  imageWidth: imageWidth,
                                  imageHeight: imageHeight,
                                  canvasWidth: displayWidth,
                                  canvasHeight: displayHeight,
                                ),
                                foregroundPainter: controller
                                                .editorState.value ==
                                            AnnotationEditorState.drawing &&
                                        controller.startPoint.value != null &&
                                        controller.currentPoint.value != null
                                    ? DrawingAnnotationPainter(
                                        startPoint:
                                            controller.startPoint.value!,
                                        currentPoint:
                                            controller.currentPoint.value!,
                                        pulseAnimation: _pulseController,
                                        color: controller.classColors[controller
                                                .selectedClass.value] ??
                                            AppColors.primary,
                                        imageWidth: imageWidth,
                                        imageHeight: imageHeight,
                                        canvasWidth: displayWidth,
                                        canvasHeight: displayHeight,
                                        controller: controller,
                                      )
                                    : null,
                              )),
                        ),
                      ),

                      // Camada 3: Controles de UI
                      Obx(() => _buildToolbar()),
                    ],
                  ),
                );
              },
            ),
          ),
        ),
        Obx(() => _buildStatusOverlay()),
      ],
    );
  }

  /// Determina o cursor apropriado com base no estado
  MouseCursor _getCursorForState() {
    if (_isResizingActive) {
      // Mostra cursor apropriado com base no canto
      switch (_resizingCornerIndex) {
        case 0:
          return SystemMouseCursors.resizeUpLeft;
        case 1:
          return SystemMouseCursors.resizeUpRight;
        case 2:
          return SystemMouseCursors.resizeDownRight;
        case 3:
          return SystemMouseCursors.resizeDownLeft;
        default:
          return SystemMouseCursors.basic;
      }
    } else if (controller.editorState.value == AnnotationEditorState.moving) {
      return SystemMouseCursors.move;
    } else if (controller.editorState.value == AnnotationEditorState.drawing) {
      return SystemMouseCursors.precise;
    } else if (_isPanningMode) {
      return SystemMouseCursors.grab;
    }
    return SystemMouseCursors.basic;
  }

  /// Trata eventos de clique/toque no canvas de anotação
  void _handleTapDown(Offset pos, double canvasWidth, double canvasHeight) {
    if (!widget.editable) return;

    // Verificar duplo-clique para edição
    if (_isDoubleClick(pos) && controller.selectedAnnotation.value != null) {
      _showAnnotationEditDialog(controller.selectedAnnotation.value!);
      return;
    }

    // Detectar se está em space
    if (HardwareKeyboard.instance
        .isLogicalKeyPressed(LogicalKeyboardKey.space)) {
      setState(() {
        _isPanningMode = true;
      });
      return;
    }

    // Salvar o estado inicial
    _initialDragState = controller.editorState.value;

    // Verificar se estamos em modo de redimensionamento
    _isResizingActive = _initialDragState == AnnotationEditorState.resizing ||
        controller.isResizeOperationActive.value;

    if (_isResizingActive) {
      // Se já estamos redimensionando, manter estado
      _resizingCornerIndex = controller.resizeCornerIndex.value;
      controller.isResizeOperationActive.value = true;
      controller.editorState.value = AnnotationEditorState.resizing;
      _isDragging = true;

      // Converter para coordenadas normalizadas para o controller
      final Offset normalizedPos =
          _canvasToNormalizedCoordinates(pos, canvasWidth, canvasHeight);
      controller.onCanvasDragUpdate(normalizedPos);
      return;
    }

    // Verificar se há anotação selecionada e estamos em um canto
    if (controller.selectedAnnotation.value != null) {
      // Converter para coordenadas normalizadas para o controller
      final Offset normalizedPos =
          _canvasToNormalizedCoordinates(pos, canvasWidth, canvasHeight);

      // Verificar se estamos em um canto para redimensionar
      final int cornerIndex = controller.getResizeCornerIndex(
          normalizedPos, controller.selectedAnnotation.value!);
      if (cornerIndex >= 0) {
        // Iniciar redimensionamento
        _isResizingActive = true;
        _resizingCornerIndex = cornerIndex;
        controller.resizeCornerIndex.value = cornerIndex;
        controller.isResizeOperationActive.value = true;
        controller.editorState.value = AnnotationEditorState.resizing;
        controller.dragStartPoint.value = normalizedPos;
        controller.dragStartAnnotation.value =
            controller.selectedAnnotation.value;
        _isDragging = true;
        return;
      }
    }

    // Iniciar operação normal (tap)
    final Offset normalizedPos =
        _canvasToNormalizedCoordinates(pos, canvasWidth, canvasHeight);
    controller.onCanvasTapDown(normalizedPos);

    // Atualizar flags
    _initialDragState = controller.editorState.value;
    _isResizingActive = _initialDragState == AnnotationEditorState.resizing;
    if (_isResizingActive) {
      _resizingCornerIndex = controller.resizeCornerIndex.value;
    }
    _isDragging = _initialDragState == AnnotationEditorState.drawing ||
        _initialDragState == AnnotationEditorState.moving ||
        _isResizingActive;

    // No caso de iniciar desenho, forçar refresh visual
    if (_initialDragState == AnnotationEditorState.drawing) {
      setState(() {});
    }
  }

  /// Trata o início do pan (arrasto)
  void _handlePanStart(Offset pos, double canvasWidth, double canvasHeight) {
    if (!widget.editable) return;

    // Salvar o estado inicial e converter para coordenadas normalizadas
    _initialDragState = controller.editorState.value;
    final Offset normalizedPos =
        _canvasToNormalizedCoordinates(pos, canvasWidth, canvasHeight);

    // Verificar se temos uma anotação selecionada
    if (controller.selectedAnnotation.value != null) {
      // Verificar se estamos em um canto para redimensionar
      final int cornerIndex = controller.getResizeCornerIndex(
          normalizedPos, controller.selectedAnnotation.value!);
      if (cornerIndex >= 0) {
        // Iniciar redimensionamento
        _isResizingActive = true;
        _resizingCornerIndex = cornerIndex;
        controller.resizeCornerIndex.value = cornerIndex;
        controller.isResizeOperationActive.value = true;
        controller.editorState.value = AnnotationEditorState.resizing;
        controller.dragStartPoint.value = normalizedPos;
        controller.dragStartAnnotation.value =
            controller.selectedAnnotation.value;
        _isDragging = true;
        return;
      }

      // Verificar se estamos dentro da anotação para mover
      if (controller.isPointInAnnotation(
          normalizedPos, controller.selectedAnnotation.value!)) {
        controller.editorState.value = AnnotationEditorState.moving;
        controller.dragStartPoint.value = normalizedPos;
        controller.dragStartAnnotation.value =
            controller.selectedAnnotation.value;
        _isDragging = true;
        return;
      }
    }

    // Se estamos em modo idle e não em cima de nenhuma anotação, iniciar desenho
    if (controller.editorState.value == AnnotationEditorState.idle) {
      controller.editorState.value = AnnotationEditorState.drawing;
      controller.startPoint.value = normalizedPos;
      controller.currentPoint.value = normalizedPos;
      _isDragging = true;
      // Forçar rebuild do widget para visualizar a atualização inicial
      setState(() {});
    }
  }

  /// Trata movimento do ponteiro no canvas
  void _handlePanUpdate(Offset pos, double canvasWidth, double canvasHeight) {
    if (!widget.editable) return;

    // Converter as coordenadas para o espaço normalizado
    final Offset normalizedPos =
        _canvasToNormalizedCoordinates(pos, canvasWidth, canvasHeight);

    // Atualizar o controlador com a nova posição
    controller.onCanvasDragUpdate(normalizedPos);

    // Forçar rebuild do widget para visualizar a atualização
    setState(() {});
  }

  /// Trata soltura do ponteiro
  void _handlePanEnd() {
    if (!widget.editable) return;

    // Finalizar operações de drag/resize
    if (_isDragging || _isResizingActive) {
      controller.onCanvasDragEnd();
      _isDragging = false;
      _isResizingActive = false;
      _initialDragState = null;
      _resizingCornerIndex = -1;
    }
  }

  /// Converte coordenadas do canvas para coordenadas normalizadas (0-1)
  Offset _canvasToNormalizedCoordinates(
      Offset canvasPoint, double canvasWidth, double canvasHeight) {
    // Garantir que as coordenadas estejam dentro dos limites do canvas
    final double x = canvasPoint.dx.clamp(0.0, canvasWidth);
    final double y = canvasPoint.dy.clamp(0.0, canvasHeight);

    // Converter para coordenadas normalizadas (0-1)
    final double normalX = x / canvasWidth;
    final double normalY = y / canvasHeight;

    return Offset(normalX, normalY);
  }

  /// Constrói a barra de ferramentas
  Widget _buildToolbar() {
    return Positioned(
      top: 20,
      right: 20,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Botão para alternar entre modo de anotação e navegação
          FloatingActionButton(
            mini: true,
            heroTag: 'togglePan',
            onPressed: _togglePanMode,
            tooltip: _isPanningMode ? 'Modo Anotação' : 'Modo Navegação',
            backgroundColor:
                _isPanningMode ? AppColors.info : AppColors.primary,
            child: Icon(
              _isPanningMode ? Icons.edit : Icons.pan_tool,
              size: 20,
              color: AppColors.white,
            ),
          ),
          const SizedBox(height: 8),

          // Botão para salvar mudanças
          if (controller.hasUnsavedChanges.value) ...[
            const SizedBox(height: 8),
            FloatingActionButton(
              mini: true,
              heroTag: 'save',
              onPressed: () => controller.saveAllAnnotations(),
              tooltip: 'Salvar anotações',
              backgroundColor: AppColors.success,
              child: controller.isSaving.value
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(
                      Icons.save,
                      size: 20,
                      color: AppColors.white,
                    ),
            ),
          ],

          // Botão para deletar anotação selecionada
          if (controller.selectedAnnotation.value != null) ...[
            const SizedBox(height: 8),
            FloatingActionButton(
              mini: true,
              heroTag: 'delete',
              onPressed: controller.deleteSelectedAnnotation,
              tooltip: 'Excluir anotação',
              backgroundColor: AppColors.error,
              child: const Icon(
                Icons.delete,
                size: 20,
                color: AppColors.white,
              ),
            ),
          ],
        ],
      ),
    );
  }

  /// Constrói o overlay de status
  Widget _buildStatusOverlay() {
    String message = '';

    // Indicar modo atual
    if (_isPanningMode) {
      message = 'Modo Navegação ativo (zoom e pan)';
    } else {
      // Mensagem baseada no estado do editor
      switch (controller.editorState.value) {
        case AnnotationEditorState.idle:
          if (controller.annotations.isEmpty) {
            message =
                'Clique para iniciar uma anotação | Classe: ${controller.selectedClass.value}';
          } else {
            message =
                'Clique em uma anotação ou inicie uma nova | Classe: ${controller.selectedClass.value}';
          }
          break;

        case AnnotationEditorState.drawing:
          message =
              'Arraste para desenhar a anotação | Classe: ${controller.selectedClass.value}';
          break;

        case AnnotationEditorState.selected:
          message =
              'Anotação selecionada: ${controller.selectedAnnotation.value?.className ?? ""}';
          break;

        case AnnotationEditorState.moving:
          message = 'Movendo anotação...';
          break;

        case AnnotationEditorState.resizing:
          message = 'Redimensionando anotação...';
          break;
      }
    }

    // Adicionar indicador de mudanças não salvas
    if (controller.hasUnsavedChanges.value) {
      message += ' | ⚠️ Alterações não salvas';
    }

    return Center(
      child: Column(
        children: [
          Divider(
            color: controller.classColors[controller.selectedClass.value],
          ),
          Text(
            message,
            style: AppTypography.headlineSmall(context),
          ),
        ],
      ),
    );
  }

  /// Alterna entre modo de navegação e modo de anotação
  void _togglePanMode() {
    setState(() {
      _isPanningMode = !_isPanningMode;
    });

    // Cancelar qualquer anotação em andamento ao mudar para modo de panorâmica
    if (_isPanningMode &&
        controller.editorState.value != AnnotationEditorState.idle) {
      controller.cancelSelection();
    }
  }
}

/// Pintor customizado para desenhar as anotações existentes
class AnnotationsPainter extends CustomPainter {
  final List<Annotation> annotations;
  final Annotation? selectedAnnotation;
  final Map<String, Color> classColors;
  final AnimationController pulseAnimation;
  final int resizeCornerIndex;
  final double imageWidth;
  final double imageHeight;
  final double canvasWidth;
  final double canvasHeight;

  AnnotationsPainter({
    required this.annotations,
    this.selectedAnnotation,
    required this.classColors,
    required this.pulseAnimation,
    this.resizeCornerIndex = -1,
    required this.imageWidth,
    required this.imageHeight,
    required this.canvasWidth,
    required this.canvasHeight,
  }) : super(repaint: pulseAnimation);

  @override
  void paint(Canvas canvas, Size size) {
    // Desenhar todas as anotações
    for (final annotation in annotations) {
      final bool isSelected = selectedAnnotation?.id == annotation.id;
      _drawAnnotation(canvas, annotation, isSelected);
    }
  }

  /// Desenha uma anotação
  void _drawAnnotation(Canvas canvas, Annotation annotation, bool isSelected) {
    // Converter coordenadas normalizadas para coordenadas do canvas
    final double left = annotation.x * canvasWidth;
    final double top = annotation.y * canvasHeight;
    final double width = annotation.width * canvasWidth;
    final double height = annotation.height * canvasHeight;

    final Rect rect = Rect.fromLTWH(left, top, width, height);

    // Determinar a cor da anotação
    final Color color = annotation.colorValue != null
        ? Color(annotation.colorValue!)
        : (classColors[annotation.className] ?? AppColors.primary);

    // Estilo da borda - mais grossa e pulsante se selecionada
    final Paint borderPaint = Paint()
      ..color = isSelected
          ? Colors.white.withOpacity(pulseAnimation.value * 0.5 + 0.5)
          : color
      ..style = PaintingStyle.stroke
      ..strokeWidth = isSelected ? 3.0 : 2.0;

    // Desenhar a borda
    canvas.drawRect(rect, borderPaint);

    // Desenhar retângulo semi-transparente para indicar a área da anotação
    final Paint fillPaint = Paint()
      ..color = color.withOpacity(isSelected ? 0.3 : 0.2)
      ..style = PaintingStyle.fill;

    canvas.drawRect(rect, fillPaint);

    // Se selecionada, desenhar pontos para redimensionamento
    if (isSelected) {
      _drawResizeHandles(canvas, rect);
    }

    // Desenhar texto com dimensões em pixels da imagem original
    final int pixelWidth = (annotation.width * imageWidth).round();
    final int pixelHeight = (annotation.height * imageHeight).round();
    final String dimensions = '${pixelWidth}x${pixelHeight} px';

    final TextPainter textPainter = TextPainter(
      text: TextSpan(
        text: dimensions,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 10,
          fontWeight: FontWeight.bold,
          backgroundColor: Colors.black54,
        ),
      ),
      textDirection: TextDirection.ltr,
    );

    textPainter.layout();

    // Posicionar o texto no canto inferior direito da anotação
    final Offset textPosition = Offset(
      rect.right - textPainter.width - 4,
      rect.bottom - textPainter.height - 4,
    );

    textPainter.paint(canvas, textPosition);

    // Desenhar rótulo da classe
    _drawClassLabel(canvas, rect, annotation, color);
  }

  /// Desenha as alças de redimensionamento
  void _drawResizeHandles(Canvas canvas, Rect rect) {
    final List<Offset> corners = [
      rect.topLeft,
      rect.topRight,
      rect.bottomRight,
      rect.bottomLeft,
    ];

    for (int i = 0; i < corners.length; i++) {
      final bool isActive = i == resizeCornerIndex;

      // Desenhar círculo de fundo
      final handlePaint = Paint()
        ..color = isActive
            ? const Color(0xFFFF0000) // Vermelho forte para o canto ativo
            : Colors.white
        ..style = PaintingStyle.fill;

      // Tamanho do círculo depende se está ativo ou não
      final double handleSize = isActive
          ? 10.0 + (pulseAnimation.value * 3.0) // Maior quando ativo
          : 6.0; // Tamanho padrão para os outros cantos

      canvas.drawCircle(corners[i], handleSize, handlePaint);

      // Borda para melhor visibilidade
      canvas.drawCircle(
          corners[i],
          handleSize,
          Paint()
            ..color = isActive ? Colors.white : Colors.black
            ..style = PaintingStyle.stroke
            ..strokeWidth = isActive ? 2.0 : 1.0);
    }
  }

  /// Desenha o rótulo da classe
  void _drawClassLabel(
      Canvas canvas, Rect rect, Annotation annotation, Color color) {
    if (annotation.className == null || annotation.className!.isEmpty) return;

    // Preparar o texto da classe
    final TextPainter textPainter = TextPainter(
      text: TextSpan(
        text: annotation.className,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
      textDirection: TextDirection.ltr,
    );

    textPainter.layout();

    // Desenhar fundo para o texto
    final RRect labelRect = RRect.fromRectAndRadius(
      Rect.fromLTWH(
        rect.left,
        rect.top - textPainter.height - 4,
        textPainter.width + 8,
        textPainter.height + 4,
      ),
      const Radius.circular(2),
    );

    canvas.drawRRect(
      labelRect,
      Paint()..color = color,
    );

    // Desenhar o texto
    textPainter.paint(
      canvas,
      Offset(rect.left + 4, rect.top - textPainter.height - 2),
    );
  }

  @override
  bool shouldRepaint(AnnotationsPainter oldDelegate) {
    return oldDelegate.annotations != annotations ||
        oldDelegate.selectedAnnotation != selectedAnnotation ||
        oldDelegate.resizeCornerIndex != resizeCornerIndex ||
        oldDelegate.canvasWidth != canvasWidth ||
        oldDelegate.canvasHeight != canvasHeight;
  }
}

/// Pintor customizado para desenhar a anotação sendo criada
class DrawingAnnotationPainter extends CustomPainter {
  final Offset startPoint;
  final Offset currentPoint;
  final AnimationController pulseAnimation;
  final Color color;
  final double imageWidth;
  final double imageHeight;
  final double canvasWidth;
  final double canvasHeight;

  final AnnotationController controller;

  DrawingAnnotationPainter({
    required this.startPoint,
    required this.currentPoint,
    required this.pulseAnimation,
    required this.color,
    required this.imageWidth,
    required this.imageHeight,
    required this.canvasWidth,
    required this.canvasHeight,
    required this.controller,
  }) : super(repaint: pulseAnimation);

  @override
  void paint(Canvas canvas, Size size) {
    // Converter pontos de coordenadas normalizadas para coordenadas do canvas
    final double startX = startPoint.dx * canvasWidth;
    final double startY = startPoint.dy * canvasHeight;
    final double currentX = currentPoint.dx * canvasWidth;
    final double currentY = currentPoint.dy * canvasHeight;

    // Calcular o retângulo a partir dos pontos convertidos
    final Rect rect = Rect.fromPoints(
      Offset(startX, startY),
      Offset(currentX, currentY),
    );

    // Estilo da borda
    final Paint borderPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    // Desenhar a borda com efeito de pulso
    final Paint pulsePaint = Paint()
      ..color = color.withOpacity(pulseAnimation.value * 0.7)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0 + (pulseAnimation.value * 2.0);

    canvas.drawRect(rect, pulsePaint);
    canvas.drawRect(rect, borderPaint);

    // Desenhar retângulo semi-transparente
    final Paint fillPaint = Paint()
      ..color = color.withOpacity(0.2)
      ..style = PaintingStyle.fill;

    canvas.drawRect(rect, fillPaint);

    // Calcular dimensões em pixels da imagem original
    final double normalWidth = controller.abs(currentPoint.dx - startPoint.dx);
    final double normalHeight = controller.abs(currentPoint.dy - startPoint.dy);
    final int pixelWidth = (normalWidth * imageWidth).round();
    final int pixelHeight = (normalHeight * imageHeight).round();

    // Indicar dimensões
    final String dimensions = '${pixelWidth}x${pixelHeight} px';

    final TextPainter textPainter = TextPainter(
      text: TextSpan(
        text: dimensions,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 10,
          fontWeight: FontWeight.bold,
          backgroundColor: Colors.black54,
        ),
      ),
      textDirection: TextDirection.ltr,
    );

    textPainter.layout();

    final Offset textPosition = Offset(
      rect.right - textPainter.width - 4,
      rect.bottom - textPainter.height - 4,
    );

    textPainter.paint(canvas, textPosition);
  }

  @override
  bool shouldRepaint(DrawingAnnotationPainter oldDelegate) {
    return oldDelegate.startPoint != startPoint ||
        oldDelegate.currentPoint != currentPoint ||
        oldDelegate.color != color ||
        oldDelegate.imageWidth != imageWidth ||
        oldDelegate.imageHeight != imageHeight ||
        oldDelegate.canvasWidth != canvasWidth ||
        oldDelegate.canvasHeight != canvasHeight;
  }
}

// Pintor customizado para renderizar a imagem e anotações
class _AnnotationPainter extends CustomPainter {
  final ui.Image image;
  final AnnotationController controller;
  final AnimationController pulseAnimation;

  _AnnotationPainter({
    required this.image,
    required this.controller,
    required this.pulseAnimation,
  }) : super(repaint: pulseAnimation);

  // Função auxiliar para calcular o valor absoluto
  double _abs(double value) => value < 0 ? -value : value;

  @override
  void paint(Canvas canvas, Size size) {
    // Obter matriz de transformação
    final Matrix4 transform = controller.transformMatrix.value;

    // Desenhar a imagem
    final Paint paint = Paint();
    canvas.drawImage(image, Offset.zero, paint);

    // Desenhar anotações existentes
    for (final annotation in controller.annotations) {
      final bool isSelected =
          controller.selectedAnnotation.value?.id == annotation.id;
      _drawAnnotation(canvas, annotation, isSelected);
    }

    // Desenhar anotação em progresso
    if (controller.editorState.value == AnnotationEditorState.drawing &&
        controller.startPoint.value != null &&
        controller.currentPoint.value != null) {
      _drawDraftAnnotation(
          canvas,
          controller.startPoint.value!,
          controller.currentPoint.value!,
          controller.classColors[controller.selectedClass.value] ??
              AppColors.primary);
    }
  }

  // Desenhar anotação existente
  void _drawAnnotation(Canvas canvas, Annotation annotation, bool isSelected) {
    // Calcular coordenadas em pixels
    final double imageWidth = image.width.toDouble();
    final double imageHeight = image.height.toDouble();

    final double x = annotation.x * imageWidth;
    final double y = annotation.y * imageHeight;
    final double width = annotation.width * imageWidth;
    final double height = annotation.height * imageHeight;

    final Rect rect = Rect.fromLTWH(x, y, width, height);

    // Determinar cor
    final Color color = annotation.colorValue != null
        ? Color(annotation.colorValue!)
        : (controller.classColors[annotation.className] ?? AppColors.primary);

    // Desenhar retângulo
    canvas.drawRect(
        rect,
        Paint()
          ..color = color.withOpacity(isSelected ? 0.4 : 0.2)
          ..style = PaintingStyle.fill);

    // Desenhar borda
    canvas.drawRect(
        rect,
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeWidth = isSelected ? 3.0 : 2.0);

    // Se selecionada, desenhar pontos de redimensionamento
    if (isSelected) {
      // Cantos para redimensionamento
      final List<Offset> corners = [
        rect.topLeft,
        rect.topRight,
        rect.bottomRight,
        rect.bottomLeft,
      ];

      // Desenhar ponto em cada canto
      for (int i = 0; i < corners.length; i++) {
        final bool isActiveCorner = i == controller.resizeCornerIndex.value;

        canvas.drawCircle(
            corners[i],
            isActiveCorner ? 8.0 : 6.0,
            Paint()
              ..color = isActiveCorner ? Colors.red : Colors.white
              ..style = PaintingStyle.fill);

        canvas.drawCircle(
            corners[i],
            isActiveCorner ? 8.0 : 6.0,
            Paint()
              ..color = Colors.black
              ..style = PaintingStyle.stroke
              ..strokeWidth = 1.0);
      }
    }
  }

  // Desenhar anotação em progresso
  void _drawDraftAnnotation(
      Canvas canvas, Offset start, Offset end, Color color) {
    // Calcular retângulo
    final Rect rect = Rect.fromPoints(start, end);

    // Desenhar retângulo semitransparente
    canvas.drawRect(
        rect,
        Paint()
          ..color = color.withOpacity(0.2)
          ..style = PaintingStyle.fill);

    // Desenhar borda pulsante
    canvas.drawRect(
        rect,
        Paint()
          ..color = color.withOpacity(0.7 + pulseAnimation.value * 0.3)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.0 + pulseAnimation.value * 1.0);

    // Calcular dimensões em pixels da imagem original
    final double normalWidth = _abs(end.dx - start.dx);
    final double normalHeight = _abs(end.dy - start.dy);
    final int pixelWidth = (normalWidth * image.width).round();
    final int pixelHeight = (normalHeight * image.height).round();
  }

  @override
  bool shouldRepaint(_AnnotationPainter oldDelegate) {
    return oldDelegate.image != image ||
        controller.annotations != controller.annotations ||
        controller.selectedAnnotation.value !=
            controller.selectedAnnotation.value ||
        controller.editorState.value != controller.editorState.value ||
        controller.startPoint.value != controller.startPoint.value ||
        controller.currentPoint.value != controller.currentPoint.value;
  }
}
