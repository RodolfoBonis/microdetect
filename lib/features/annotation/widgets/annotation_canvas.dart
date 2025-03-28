import 'dart:async';
import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/features/annotation/controllers/annotation_controller.dart';
import 'package:microdetect/features/annotation/models/annotation.dart';

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

class _AnnotationCanvasState extends State<AnnotationCanvas> with TickerProviderStateMixin {
  /// Controlador de anotação
  late AnnotationController controller;

  /// Controlador de transformação
  final TransformationController _transformController = TransformationController();

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

  /// Flag para saber se o zoom mudou durante esta interação
  bool _zoomChanged = false;

  /// Key para o canvas
  final GlobalKey _canvasKey = GlobalKey();

  @override
  void initState() {
    super.initState();
    controller = Get.find<AnnotationController>();
    _loadImage();

    // Inicializar o controlador de animação
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    )..repeat(reverse: true);

    // Listener para transformação
    _transformController.addListener(_handleTransformChange);

    // Focar o nó para capturar eventos de teclado
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _canvasFocusNode.requestFocus();
    });
  }

  @override
  void dispose() {
    _transformController.removeListener(_handleTransformChange);
    _pulseController.dispose();
    _canvasFocusNode.dispose();
    super.dispose();
  }

  /// Atualiza os valores de transformação no controller
  void _handleTransformChange() {
    if (_image == null) return;

    final Matrix4 matrix = _transformController.value;

    // Extrair valores diretamente da matriz
    final double scaleValue = matrix.getMaxScaleOnAxis();
    final double translateX = matrix.getTranslation().x;
    final double translateY = matrix.getTranslation().y;

    // Atualizar valores no controller
    controller.updateTransformation(matrix);

    // Marcar que o zoom mudou durante esta interação
    _zoomChanged = true;
  }

  @override
  void didUpdateWidget(AnnotationCanvas oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.imageUrl != oldWidget.imageUrl) {
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

        // Ajustar a transformação inicial para caber na tela
        _resetTransformation();
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

  /// Reset da transformação para que a imagem se ajuste à tela
  void _resetTransformation() {
    if (_image == null) return;

    // Calcular escala para ajustar a imagem ao container
    final double scaleX = widget.size.width / _image!.width;
    final double scaleY = widget.size.height / _image!.height;

    // Usar a menor escala para garantir que a imagem caiba completamente
    final double scale = math.min(scaleX, scaleY) * 0.95; // 95% para dar uma margem

    // Centralizar a imagem
    final double dx = (widget.size.width - (_image!.width * scale)) / 2;
    final double dy = (widget.size.height - (_image!.height * scale)) / 2;

    // Definir a matriz de transformação
    _transformController.value = Matrix4.identity()
      ..translate(dx, dy)
      ..scale(scale);

    // Atualizar informações de transformação no controlador
    controller.updateTransformation(_transformController.value);
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
    if (_isLoading) {
      return SizedBox(
        width: widget.size.width,
        height: widget.size.height,
        child: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (_error != null) {
      return SizedBox(
        width: widget.size.width,
        height: widget.size.height,
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
      return const SizedBox();
    }

    return KeyboardListener(
      focusNode: _canvasFocusNode,
      onKeyEvent: _handleKeyEvent,
      child: Stack(
        children: [
          // Canvas interativo com gestos
          Obx(() => _buildInteractiveCanvas()),

          // Overlay de status e navegação
          Obx(() => _buildStatusOverlay()),

          // Barra de ferramentas
          Obx(() => _buildToolbar()),

          // Botões de navegação
          Obx(() => _buildNavigationControls()),
        ],
      ),
    );
  }

  /// Constrói o canvas interativo com gestos
  Widget _buildInteractiveCanvas() {
    return Listener(
      onPointerDown: (PointerDownEvent event) {
        if (!widget.editable || _isPanningMode) return;

        final offset = event.localPosition;

        // Verificar duplo-clique
        final bool isDoubleClick = _isDoubleClick(offset);

        if (isDoubleClick && controller.selectedAnnotation.value != null) {
          // Duplo clique em uma anotação já selecionada - abrir diálogo de edição
          _showAnnotationEditDialog(controller.selectedAnnotation.value!);
          return;
        }

        // Processar o clique normal
        controller.onCanvasTapDown(offset);
        _isDragging = controller.editorState.value == AnnotationEditorState.drawing ||
            controller.editorState.value == AnnotationEditorState.moving ||
            controller.editorState.value == AnnotationEditorState.resizing;
      },
      onPointerMove: (PointerMoveEvent event) {
        if (!widget.editable || _isPanningMode || !_isDragging) return;

        // Processar atualização de arrasto
        controller.onCanvasDragUpdate(event.localPosition);
      },
      onPointerUp: (PointerUpEvent event) {
        if (!widget.editable || _isPanningMode) return;

        // Finalizar operação de arrasto se estivermos arrastando
        if (_isDragging) {
          controller.onCanvasDragEnd();
          _isDragging = false;
        }

        // Reset do flag de zoom
        _zoomChanged = false;
      },
      child: InteractiveViewer(
        key: _canvasKey,
        transformationController: _transformController,
        constrained: true,
        panEnabled: _isPanningMode || controller.editorState.value == AnnotationEditorState.idle,
        scaleEnabled: true,
        boundaryMargin: const EdgeInsets.all(20.0),
        minScale: 0.1,
        maxScale: 10.0,
        onInteractionStart: (_) {
          // Registrar o início de uma interação de zoom/pan
        },
        onInteractionEnd: (_) {
          // Se houve mudança de zoom, resetar flag
          _zoomChanged = false;
        },
        child: Stack(
          children: [
            // Background
            Container(
              width: _image!.width.toDouble(),
              height: _image!.height.toDouble(),
              color: Colors.black12,
            ),

            // CustomPaint com imagem e anotações
            CustomPaint(
              painter: AnnotationPainter(
                image: _image!,
                annotations: controller.annotations,
                selectedAnnotation: controller.selectedAnnotation.value,
                startPoint: controller.startPoint.value,
                currentPoint: controller.currentPoint.value,
                scale: controller.scale.value,
                translateX: controller.translateX.value,
                translateY: controller.translateY.value,
                editorState: controller.editorState.value,
                classColors: controller.classColors,
                resizeCornerIndex: controller.resizeCornerIndex.value,
                pulseAnimation: _pulseController,
                isPanningMode: _isPanningMode,
              ),
              size: Size(_image!.width.toDouble(), _image!.height.toDouble()),
            ),
          ],
        ),
      ),
    );
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
            backgroundColor: _isPanningMode
                ? AppColors.info
                : AppColors.primary,
            child: Icon(
              _isPanningMode ? Icons.edit : Icons.pan_tool,
              size: 20,
            ),
          ),
          const SizedBox(height: 8),

          // Botão para resetar zoom/transformação
          FloatingActionButton(
            mini: true,
            heroTag: 'resetZoom',
            onPressed: _resetTransformation,
            tooltip: 'Ajustar à tela',
            backgroundColor: Colors.grey.shade700,
            child: const Icon(
              Icons.fit_screen,
              size: 20,
            ),
          ),

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
                  : const Icon(Icons.save, size: 20),
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
              ),
            ),
          ],
        ],
      ),
    );
  }

  /// Constrói os botões para navegar entre imagens
  Widget _buildNavigationControls() {
    return Positioned(
      bottom: 80,
      left: 0,
      right: 0,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Botão para imagem anterior
          ElevatedButton.icon(
            onPressed: controller.hasPreviousImage()
                ? controller.previousImage
                : null,
            icon: const Icon(Icons.arrow_back),
            label: const Text('Anterior'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.grey,
              foregroundColor: Colors.white,
            ),
          ),
          const SizedBox(width: 16),

          // Botão para próxima imagem
          ElevatedButton.icon(
            onPressed: controller.hasNextImage()
                ? controller.nextImage
                : null,
            icon: const Icon(Icons.arrow_forward),
            label: const Text('Próxima'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.grey,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  /// Constrói o overlay de status
  Widget _buildStatusOverlay() {
    String message = '';
    Color backgroundColor = AppColors.primary.withOpacity(0.8);

    // Indicar modo atual
    if (_isPanningMode) {
      message = 'Modo Navegação ativo (zoom e pan)';
      backgroundColor = AppColors.info.withOpacity(0.8);
    } else {
      // Mensagem baseada no estado do editor
      switch (controller.editorState.value) {
        case AnnotationEditorState.idle:
          if (controller.annotations.isEmpty) {
            message = 'Clique para iniciar uma anotação | Classe: ${controller.selectedClass.value}';
          } else {
            message = 'Clique em uma anotação ou inicie uma nova | Classe: ${controller.selectedClass.value}';
          }
          break;

        case AnnotationEditorState.drawing:
          message = 'Arraste para desenhar a anotação | Classe: ${controller.selectedClass.value}';
          backgroundColor = AppColors.primary.withOpacity(0.8);
          break;

        case AnnotationEditorState.selected:
          message = 'Anotação selecionada: ${controller.selectedAnnotation.value?.className ?? ""}';
          backgroundColor = AppColors.success.withOpacity(0.8);
          break;

        case AnnotationEditorState.moving:
          message = 'Movendo anotação...';
          backgroundColor = AppColors.warning.withOpacity(0.8);
          break;

        case AnnotationEditorState.resizing:
          message = 'Redimensionando anotação...';
          backgroundColor = AppColors.warning.withOpacity(0.8);
          break;
      }
    }

    // Adicionar indicador de mudanças não salvas
    if (controller.hasUnsavedChanges.value) {
      message += ' | ⚠️ Alterações não salvas';
    }

    return Positioned(
      bottom: 20,
      left: 0,
      right: 0,
      child: Center(
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
          decoration: BoxDecoration(
            color: backgroundColor,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            message,
            style: const TextStyle(color: Colors.white),
          ),
        ),
      ),
    );
  }

  /// Alterna entre modo de navegação e modo de anotação
  void _togglePanMode() {
    setState(() {
      _isPanningMode = !_isPanningMode;
    });

    // Cancelar qualquer anotação em andamento ao mudar para modo de panorâmica
    if (_isPanningMode && controller.editorState.value != AnnotationEditorState.idle) {
      controller.cancelSelection();
    }
  }
}

/// Pintor customizado para desenhar as anotações
class AnnotationPainter extends CustomPainter {
  final ui.Image image;
  final List<Annotation> annotations;
  final Annotation? selectedAnnotation;
  final Offset? startPoint;
  final Offset? currentPoint;
  final double scale;
  final double translateX;
  final double translateY;
  final AnnotationEditorState editorState;
  final Map<String, Color> classColors;
  final int resizeCornerIndex;
  final AnimationController pulseAnimation;
  final bool isPanningMode;

  AnnotationPainter({
    required this.image,
    required this.annotations,
    this.selectedAnnotation,
    this.startPoint,
    this.currentPoint,
    required this.scale,
    required this.translateX,
    required this.translateY,
    required this.editorState,
    required this.classColors,
    this.resizeCornerIndex = -1,
    required this.pulseAnimation,
    this.isPanningMode = false,
  }) : super(repaint: pulseAnimation);

  @override
  void paint(Canvas canvas, Size size) {
    // Desenhar a imagem de fundo
    paintImage(canvas, size);

    // Desenhar todas as anotações existentes
    for (final annotation in annotations) {
      final bool isSelected = selectedAnnotation?.id == annotation.id;
      paintAnnotation(canvas, annotation, isSelected);
    }

    // Desenhar uma nova anotação sendo criada
    if (editorState == AnnotationEditorState.drawing &&
        startPoint != null && currentPoint != null) {
      paintNewAnnotation(canvas);
    }
  }

  /// Desenha a imagem de fundo
  void paintImage(Canvas canvas, Size size) {
    // Aplicar transformação diretamente usando escala e translação
    canvas.save();
    canvas.translate(translateX, translateY);
    canvas.scale(scale);

    // Desenhar a imagem
    canvas.drawImage(image, Offset.zero, Paint());

    // Restaurar o estado do canvas
    canvas.restore();
  }

  /// Desenha uma anotação existente
  void paintAnnotation(Canvas canvas, Annotation annotation, bool isSelected) {
    final imageWidth = image.width.toDouble();
    final imageHeight = image.height.toDouble();

    // Calcular as coordenadas em pixels
    final double left = (annotation.x * imageWidth * scale) + translateX;
    final double top = (annotation.y * imageHeight * scale) + translateY;
    final double width = annotation.width * imageWidth * scale;
    final double height = annotation.height * imageHeight * scale;

    final Rect rect = Rect.fromLTWH(left, top, width, height);

    // Cores da anotação
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

    // Desenhar rótulo da classe
    _drawClassLabel(canvas, rect, annotation);
  }

  /// Desenha os pontos para redimensionamento de uma anotação selecionada
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
        ..color = isActive ? Colors.red : Colors.white
        ..style = PaintingStyle.fill;

      // Tamanho do círculo depende se está ativo ou não, e da animação se ativo
      final double handleSize = isActive
          ? 10.0 + (pulseAnimation.value * 2.0)
          : 8.0;

      canvas.drawCircle(corners[i], handleSize, handlePaint);

      // Borda para melhor visibilidade
      canvas.drawCircle(
          corners[i],
          handleSize,
          Paint()
            ..color = Colors.black
            ..style = PaintingStyle.stroke
            ..strokeWidth = 1.5
      );
    }
  }

  /// Desenha o rótulo da classe em uma anotação
  void _drawClassLabel(Canvas canvas, Rect rect, Annotation annotation) {
    if (annotation.className == null || annotation.className!.isEmpty) return;

    // Cores
    final Color color = annotation.colorValue != null
        ? Color(annotation.colorValue!)
        : (classColors[annotation.className] ?? AppColors.primary);

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

    // Fundo do rótulo
    final Paint backgroundPaint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final double labelWidth = textPainter.width + 10;
    final double labelHeight = textPainter.height + 6;

    final Rect labelRect = Rect.fromLTWH(
      rect.left,
      rect.top - labelHeight,
      labelWidth,
      labelHeight,
    );

    // Desenhar retângulo com bordas arredondadas
    canvas.drawRRect(
      RRect.fromRectAndCorners(
        labelRect,
        topLeft: const Radius.circular(3),
        topRight: const Radius.circular(3),
      ),
      backgroundPaint,
    );

    // Texto
    textPainter.paint(
      canvas,
      Offset(rect.left + 5, rect.top - labelHeight + 3),
    );
  }

  /// Desenha uma nova anotação sendo criada
  void paintNewAnnotation(Canvas canvas) {
    if (startPoint == null || currentPoint == null) return;

    // Calcular o retângulo
    final double left = math.min(startPoint!.dx, currentPoint!.dx);
    final double top = math.min(startPoint!.dy, currentPoint!.dy);
    final double width = (startPoint!.dx - currentPoint!.dx).abs();
    final double height = (startPoint!.dy - currentPoint!.dy).abs();

    final Rect rect = Rect.fromLTWH(left, top, width, height);

    // Estilo da borda
    final Paint borderPaint = Paint()
      ..color = AppColors.primary
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    // Desenhar a borda com animação de pulso
    final borderPulse = Paint()
      ..color = AppColors.primary.withOpacity(pulseAnimation.value * 0.7)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0 + (pulseAnimation.value * 2.0);

    // Primeiro desenhar o halo pulsante
    canvas.drawRect(rect, borderPulse);

    // Depois a borda principal
    canvas.drawRect(rect, borderPaint);

    // Desenhar retângulo semi-transparente
    final Paint fillPaint = Paint()
      ..color = AppColors.primary.withOpacity(0.2)
      ..style = PaintingStyle.fill;

    canvas.drawRect(rect, fillPaint);

    // Indicar tamanho
    final String dimensions = '${width.toInt()}x${height.toInt()} px';
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
    textPainter.paint(canvas, Offset(rect.right - textPainter.width - 4, rect.bottom - textPainter.height - 4));
  }

  @override
  bool shouldRepaint(AnnotationPainter oldDelegate) {
    return oldDelegate.image != image ||
        oldDelegate.annotations != annotations ||
        oldDelegate.selectedAnnotation != selectedAnnotation ||
        oldDelegate.startPoint != startPoint ||
        oldDelegate.currentPoint != currentPoint ||
        oldDelegate.scale != scale ||
        oldDelegate.translateX != translateX ||
        oldDelegate.translateY != translateY ||
        oldDelegate.editorState != editorState ||
        oldDelegate.resizeCornerIndex != resizeCornerIndex ||
        oldDelegate.isPanningMode != isPanningMode;
  }
}