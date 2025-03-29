import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/features/annotation/models/annotation.dart';
import 'package:microdetect/features/annotation/services/annotation_service.dart';
import 'package:microdetect/features/camera/models/gallery_image.dart';
import 'package:microdetect/features/camera/services/camera_service.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';
import 'package:microdetect/features/datasets/services/dataset_service.dart';
import 'dart:ui' as ui;

import 'package:vector_math/vector_math_64.dart' as vector_math;


/// Estados possíveis do editor de anotações
enum AnnotationEditorState {
  idle,        // Estado neutro, sem anotação ativa
  drawing,     // Desenhando uma nova anotação
  selected,    // Uma anotação está selecionada
  moving,      // Movendo uma anotação selecionada
  resizing,    // Redimensionando uma anotação selecionada
}

/// Controlador das telas de anotação - usando uma abordagem de máquina de estados
class AnnotationController extends GetxController {
  final AnnotationService _annotationService = Get.find<AnnotationService>();
  final DatasetService _datasetService = Get.find<DatasetService>();

  // Estado atual do editor
  final Rx<AnnotationEditorState> editorState = AnnotationEditorState.idle.obs;

  // Dados principais
  final RxList<Dataset> datasets = <Dataset>[].obs;
  final Rx<Dataset?> selectedDataset = Rx<Dataset?>(null);
  final RxList<AnnotatedImage> images = <AnnotatedImage>[].obs;
  final Rx<AnnotatedImage?> selectedImage = Rx<AnnotatedImage?>(null);
  final RxList<Annotation> annotations = <Annotation>[].obs;
  final Rx<Annotation?> selectedAnnotation = Rx<Annotation?>(null);
  final RxList<String> classes = <String>[].obs;
  final RxString selectedClass = ''.obs;

  // Anotações pendentes (não salvas)
  final RxList<Annotation> pendingAnnotations = <Annotation>[].obs;
  final RxBool hasUnsavedChanges = false.obs;

  // Dados de interação com o canvas
  final Rx<Offset?> startPoint = Rx<Offset?>(null);
  final Rx<Offset?> currentPoint = Rx<Offset?>(null);
  final Rx<ui.Image?> loadedImage = Rx<ui.Image?>(null);

  // Transformação da imagem
  final Rx<Matrix4> transformMatrix = Matrix4.identity().obs;
  final RxDouble scale = 1.0.obs;
  final RxDouble translateX = 0.0.obs;
  final RxDouble translateY = 0.0.obs;

  // Ponto de partida para operações de arrasto/redimensionamento
  final Rx<Offset?> dragStartPoint = Rx<Offset?>(null);
  final Rx<Annotation?> dragStartAnnotation = Rx<Annotation?>(null);

  // Status de UI
  final RxBool isLoading = false.obs;
  final RxBool isSaving = false.obs;
  final RxString errorMessage = ''.obs;

  // Mapeamento de classes para cores
  final Map<String, Color> classColors = <String, Color>{};

  // Índice do canto que está sendo redimensionado
  // 0: top-left, 1: top-right, 2: bottom-right, 3: bottom-left
  final RxInt resizeCornerIndex = (-1).obs;

  // Tamanho do widget de visualização
  final Rx<Size> viewportSize = Size(0, 0).obs;

  @override
  void onInit() {
    super.onInit();
    loadDatasets();

    // Observar mudanças no dataset
    ever(selectedDataset, (_) {
      if (selectedDataset.value != null) {
        loadDatasetImages(selectedDataset.value!.id);
        loadDatasetClasses(selectedDataset.value!.id);

        // Resetar estados
        editorState.value = AnnotationEditorState.idle;
        selectedAnnotation.value = null;
      }
    });

    // Observar mudanças na imagem selecionada
    ever(selectedImage, (_) {
      if (selectedImage.value != null) {
        // Verificar alterações não salvas
        if (hasUnsavedChanges.value) {
          _confirmSaveChanges();
        }

        // Carregar anotações da imagem
        if (selectedImage.value!.annotations.isNotEmpty) {
          annotations.value = selectedImage.value!.annotations;
        } else {
          annotations.clear();
        }

        // Resetar estado de anotação
        editorState.value = AnnotationEditorState.idle;
        selectedAnnotation.value = null;
        pendingAnnotations.clear();
        hasUnsavedChanges.value = false;

        // Resetar transformação
        transformMatrix.value = Matrix4.identity();
        scale.value = 1.0;
        translateX.value = 0.0;
        translateY.value = 0.0;
      } else {
        annotations.clear();
        pendingAnnotations.clear();
      }
    });

    // Observar anotações pendentes
    ever(pendingAnnotations, (_) {
      hasUnsavedChanges.value = pendingAnnotations.isNotEmpty;
    });

    // Observar o estado do editor para atualizar UI
    ever(editorState, (_) {
      // Resetar pontos se estamos saindo de um estado de desenho
      if (editorState.value != AnnotationEditorState.drawing) {
        startPoint.value = null;
        currentPoint.value = null;
      }

      // Resetar pontos de drag se não estamos movendo/redimensionando
      if (editorState.value != AnnotationEditorState.moving &&
          editorState.value != AnnotationEditorState.resizing) {
        dragStartPoint.value = null;
        dragStartAnnotation.value = null;
        resizeCornerIndex.value = -1;
      }
    });

    // Observar seleção de anotação para evitar seleções múltiplas
    ever(selectedAnnotation, (annotation) {
      if (annotation != null) {
        editorState.value = AnnotationEditorState.selected;
      }
    });
  }

  //
  // Métodos para gerenciamento de dados
  //

  /// Carrega a lista de datasets
  Future<void> loadDatasets() async {
    isLoading.value = true;
    try {
      final List<Dataset> result = await _datasetService.getDatasets();
      datasets.value = result;

      // Auto-selecionar dataset se houver ID nos argumentos
      if (Get.arguments != null && Get.arguments['dataset_id'] != null) {
        final int datasetId = Get.arguments['dataset_id'];
        final Dataset? dataset = datasets.firstWhereOrNull((d) => d.id == datasetId);
        if (dataset != null) {
          selectedDataset.value = dataset;
        }
      }
    } catch (e) {
      LoggerUtil.error('Erro ao carregar datasets: $e');
      errorMessage.value = 'Erro ao carregar datasets: $e';
    } finally {
      isLoading.value = false;
    }
  }

  /// Carrega imagens de um dataset
  Future<void> loadDatasetImages(int datasetId) async {
    isLoading.value = true;
    try {
      images.clear();
      selectedImage.value = null;

      final List<AnnotatedImage> result =
      await _annotationService.getDatasetImages(datasetId);
      images.value = result;
    } catch (e) {
      LoggerUtil.error('Erro ao carregar imagens: $e');
      errorMessage.value = 'Erro ao carregar imagens: $e';
    } finally {
      isLoading.value = false;
    }
  }

  /// Carrega classes de um dataset
  Future<void> loadDatasetClasses(int datasetId) async {
    try {
      final List<String> result = await _annotationService.getDatasetClasses(datasetId);
      classes.value = result;

      _generateClassColors();

      // Selecionar a primeira classe como padrão
      if (classes.isNotEmpty && selectedClass.isEmpty) {
        selectedClass.value = classes.first;
      }
    } catch (e) {
      LoggerUtil.error('Erro ao carregar classes: $e');
    }
  }

  /// Gera cores para as classes
  void _generateClassColors() {
    classColors.clear();

    // Definir paleta de cores
    final List<Color> palette = [
      AppColors.primary,           // Coral
      AppColors.success,           // Verde
      AppColors.info,              // Azul
      AppColors.warning,           // Amarelo
      const Color(0xFF9C27B0),     // Roxo
      const Color(0xFF3F51B5),     // Índigo
      const Color(0xFF795548),     // Marrom
      const Color(0xFF607D8B),     // Azul acinzentado
    ];

    // Atribuir cores para cada classe
    for (int i = 0; i < classes.length; i++) {
      final className = classes[i];
      final color = palette[i % palette.length];
      classColors[className] = color;
    }
  }

  /// Seleciona um dataset
  void selectDataset(Dataset dataset) {
    selectedDataset.value = dataset;
  }

  /// Seleciona uma imagem
  void selectImage(AnnotatedImage image) {
    selectedImage.value = image;
  }

  /// Seleciona uma classe para anotação
  void selectClass(String className) {
    selectedClass.value = className;
  }

  //
  // Métodos para manipulação do canvas
  //

  /// Define o tamanho do viewport de visualização
  void setViewportSize(Size size) {
    viewportSize.value = size;
  }

  /// Atualiza os dados de transformação da imagem
  void updateTransformation(Matrix4 transform) {
    transformMatrix.value = transform.clone();

    // Extrair escala e translação da matriz de transformação
    scale.value = transform.getMaxScaleOnAxis();
    final vector_math.Vector3 translation = transform.getTranslation();
    translateX.value = translation.x;
    translateY.value = translation.y;
  }

  /// Define a imagem carregada
  void setLoadedImage(ui.Image image) {
    loadedImage.value = image;
  }

  /// Converte um ponto de coordenadas de tela para coordenadas normalizadas (0-1)
  Offset toNormalizedCoordinates(Offset screenPoint) {
    if (loadedImage.value == null) return const Offset(0, 0);

    final double imageWidth = loadedImage.value!.width.toDouble();
    final double imageHeight = loadedImage.value!.height.toDouble();

    // Aplicar a transformação inversa
    final Matrix4 inverseMatrix = Matrix4.inverted(transformMatrix.value);
    final vector_math.Vector4 position = vector_math.Vector4(screenPoint.dx, screenPoint.dy, 0, 1);
    final vector_math.Vector4 transformed = inverseMatrix.transform(position);

    final double normalX = transformed.x / imageWidth;
    final double normalY = transformed.y / imageHeight;

    return Offset(normalX, normalY);
  }

  /// Converte coordenadas normalizadas para coordenadas de tela
  Offset toScreenCoordinates(Offset normalizedPoint) {
    if (loadedImage.value == null) return const Offset(0, 0);

    final double imageWidth = loadedImage.value!.width.toDouble();
    final double imageHeight = loadedImage.value!.height.toDouble();

    // Converter para coordenadas da imagem
    final double x = normalizedPoint.dx * imageWidth;
    final double y = normalizedPoint.dy * imageHeight;

    // Aplicar a transformação
    final vector_math.Vector4 position = vector_math.Vector4(x, y, 0, 1);
    final vector_math.Vector4 transformed = transformMatrix.value.transform(position);

    return Offset(transformed.x, transformed.y);
  }

  /// Verifica se um ponto (em coordenadas normalizadas) está dentro de uma anotação
  bool isPointInAnnotation(Offset normalizedPoint, Annotation annotation) {
    return normalizedPoint.dx >= annotation.x &&
        normalizedPoint.dx <= annotation.x + annotation.width &&
        normalizedPoint.dy >= annotation.y &&
        normalizedPoint.dy <= annotation.y + annotation.height;
  }

  /// Encontra uma anotação no ponto indicado
  Annotation? findAnnotationAt(Offset screenPoint) {
    final normalizedPoint = toNormalizedCoordinates(screenPoint);
    LoggerUtil.debug("Ponto normalizado: $normalizedPoint");

    // Procurar a anotação de trás para frente (para que a última desenhada seja selecionada primeiro)
    for (int i = annotations.length - 1; i >= 0; i--) {
      final annotation = annotations[i];
      if (isPointInAnnotation(normalizedPoint, annotation)) {
        LoggerUtil.debug("Anotação encontrada: ${annotation.id}");
        return annotation;
      }
    }

    return null;
  }

  /// Verifica se um ponto está próximo a um dos cantos da anotação
  /// Retorna o índice do canto ou -1 se não estiver próximo
  int getResizeCornerIndex(Offset screenPoint, Annotation annotation) {
    final double hitDistance = 20.0 / scale.value; // Área de toque ajustada pela escala

    // Calcular coordenadas da imagem
    final double imageWidth = loadedImage.value!.width.toDouble();
    final double imageHeight = loadedImage.value!.height.toDouble();

    // Calcular os 4 cantos da anotação em coordenadas da imagem
    final List<Offset> imageCorners = [
      Offset(annotation.x * imageWidth, annotation.y * imageHeight), // Canto superior esquerdo
      Offset((annotation.x + annotation.width) * imageWidth, annotation.y * imageHeight), // Canto superior direito
      Offset((annotation.x + annotation.width) * imageWidth, (annotation.y + annotation.height) * imageHeight), // Canto inferior direito
      Offset(annotation.x * imageWidth, (annotation.y + annotation.height) * imageHeight), // Canto inferior esquerdo
    ];

    // Transformar ponto da tela para coordenadas da imagem
    final Matrix4 inverseMatrix = Matrix4.inverted(transformMatrix.value);
    final vector_math.Vector4 screenPos = vector_math.Vector4(screenPoint.dx, screenPoint.dy, 0, 1);
    final vector_math.Vector4 imagePos = inverseMatrix.transform(screenPos);
    final Offset imagePoint = Offset(imagePos.x, imagePos.y);

    // Verificar cada canto
    for (int i = 0; i < imageCorners.length; i++) {
      if ((imageCorners[i] - imagePoint).distance < hitDistance) {
        return i;
      }
    }

    return -1; // Não está perto de nenhum canto
  }

  //
  // Métodos de interação do usuário com o canvas
  //

  /// Trata o evento de toque no canvas
  void onCanvasTapDown(Offset position) {
    if (selectedImage.value == null || loadedImage.value == null) return;

    LoggerUtil.debug("Toque em: $position");

    switch (editorState.value) {
      case AnnotationEditorState.idle:
      // Verificar se clicou em uma anotação existente
        final tappedAnnotation = findAnnotationAt(position);
        if (tappedAnnotation != null) {
          // Selecionar a anotação
          selectedAnnotation.value = tappedAnnotation;
          editorState.value = AnnotationEditorState.selected;

          // Atualizar a classe selecionada para corresponder à anotação
          if (tappedAnnotation.className != null &&
              classes.contains(tappedAnnotation.className)) {
            selectedClass.value = tappedAnnotation.className!;
          }
        } else {
          // Iniciar desenho de nova anotação
          startPoint.value = position;
          currentPoint.value = position;
          editorState.value = AnnotationEditorState.drawing;
        }
        break;

      case AnnotationEditorState.selected:
        if (selectedAnnotation.value == null) {
          editorState.value = AnnotationEditorState.idle;
          break;
        }

        // Verificar se clicou em um ponto de redimensionamento
        final cornerIndex = getResizeCornerIndex(position, selectedAnnotation.value!);
        if (cornerIndex >= 0) {
          // Iniciar redimensionamento
          resizeCornerIndex.value = cornerIndex;
          dragStartPoint.value = position;
          dragStartAnnotation.value = selectedAnnotation.value;
          editorState.value = AnnotationEditorState.resizing;
          LoggerUtil.debug("Iniciando redimensionamento no canto $cornerIndex");
        }
        // Verificar se clicou dentro da anotação selecionada
        else if (isPointInAnnotation(toNormalizedCoordinates(position), selectedAnnotation.value!)) {
          // Iniciar arrasto
          dragStartPoint.value = position;
          dragStartAnnotation.value = selectedAnnotation.value;
          editorState.value = AnnotationEditorState.moving;
          LoggerUtil.debug("Iniciando movimento");
        }
        // Clicou fora da anotação
        else {
          // Desselecionar e iniciar desenho de nova anotação
          selectedAnnotation.value = null;
          startPoint.value = position;
          currentPoint.value = position;
          editorState.value = AnnotationEditorState.drawing;
        }
        break;

    // Para outros estados, reiniciar para o estado idle
      default:
        editorState.value = AnnotationEditorState.idle;
        break;
    }
  }

  /// Trata o evento de arrasto no canvas
  void onCanvasDragUpdate(Offset position) {
    if (selectedImage.value == null || loadedImage.value == null) return;

    switch (editorState.value) {
      case AnnotationEditorState.drawing:
      // Atualizar ponto final da anotação em desenho
        currentPoint.value = position;
        break;

      case AnnotationEditorState.moving:
        if (selectedAnnotation.value == null || dragStartPoint.value == null ||
            dragStartAnnotation.value == null) {
          editorState.value = AnnotationEditorState.idle;
          break;
        }

        // Garantir que o estado continue sendo "moving" durante toda a operação
        editorState.value = AnnotationEditorState.moving;

        // Converter os pontos para coordenadas normalizadas
        final Offset startNorm = toNormalizedCoordinates(dragStartPoint.value!);
        final Offset currentNorm = toNormalizedCoordinates(position);

        // Calcular o delta do movimento
        final double deltaX = currentNorm.dx - startNorm.dx;
        final double deltaY = currentNorm.dy - startNorm.dy;

        // Obter a anotação original
        final annotation = dragStartAnnotation.value!;

        // Calcular novas coordenadas com limites
        final double newX = (annotation.x + deltaX).clamp(0.0, 1.0 - annotation.width);
        final double newY = (annotation.y + deltaY).clamp(0.0, 1.0 - annotation.height);

        // Atualizar a anotação
        final updatedAnnotation = annotation.copyWith(
          x: newX,
          y: newY,
        );

        // Importante: manter o estado como "moving" durante toda a operação
        updateAnnotationInLists(updatedAnnotation, maintainMovingState: true);

        // Atualizar o ponto de início para o próximo delta
        dragStartPoint.value = position;
        dragStartAnnotation.value = updatedAnnotation;
        break;

      case AnnotationEditorState.resizing:
        if (selectedAnnotation.value == null ||
            dragStartPoint.value == null ||
            dragStartAnnotation.value == null) {
          editorState.value = AnnotationEditorState.idle;
          break;
        }

        // Se por algum motivo o índice do canto for inválido, mas estamos no estado resizing,
        // força um valor válido para evitar problemas
        if (resizeCornerIndex.value < 0) {
          resizeCornerIndex.value = 0; // Usar canto superior esquerdo como padrão
        }

        // Garantir que o estado continue sendo "resizing" durante toda a operação
        editorState.value = AnnotationEditorState.resizing;

        // Obter a anotação original
        final annotation = dragStartAnnotation.value!;

        // Obter o canto que está sendo arrastado
        final cornerIndex = resizeCornerIndex.value;

        // Converter para coordenadas normalizadas
        final Offset currentNorm = toNormalizedCoordinates(position);

        // Valores atuais da anotação
        double x = annotation.x;
        double y = annotation.y;
        double width = annotation.width;
        double height = annotation.height;

        switch (cornerIndex) {
          case 0: // Canto superior esquerdo
          // Novo X não pode ser maior que X + largura - tamanho mínimo
            x = currentNorm.dx.clamp(0.0, annotation.x + annotation.width - 0.01);
            // Novo Y não pode ser maior que Y + altura - tamanho mínimo
            y = currentNorm.dy.clamp(0.0, annotation.y + annotation.height - 0.01);
            // Ajustar largura e altura
            width = annotation.x + annotation.width - x;
            height = annotation.y + annotation.height - y;
            break;

          case 1: // Canto superior direito
          // Novo Y não pode ser maior que Y + altura - tamanho mínimo
            y = currentNorm.dy.clamp(0.0, annotation.y + annotation.height - 0.01);
            // Nova largura não pode fazer X + largura sair da imagem
            width = (currentNorm.dx - annotation.x).clamp(0.01, 1.0 - annotation.x);
            // Ajustar altura
            height = annotation.y + annotation.height - y;
            break;

          case 2: // Canto inferior direito
          // Nova largura não pode fazer X + largura sair da imagem
            width = (currentNorm.dx - annotation.x).clamp(0.01, 1.0 - annotation.x);
            // Nova altura não pode fazer Y + altura sair da imagem
            height = (currentNorm.dy - annotation.y).clamp(0.01, 1.0 - annotation.y);
            break;

          case 3: // Canto inferior esquerdo
          // Novo X não pode ser maior que X + largura - tamanho mínimo
            x = currentNorm.dx.clamp(0.0, annotation.x + annotation.width - 0.01);
            // Ajustar largura
            width = annotation.x + annotation.width - x;
            // Nova altura não pode fazer Y + altura sair da imagem
            height = (currentNorm.dy - annotation.y).clamp(0.01, 1.0 - annotation.y);
            break;
        }

        // Garantir tamanho mínimo
        if (width < 0.01) width = 0.01;
        if (height < 0.01) height = 0.01;

        // Criar a anotação atualizada
        final updatedAnnotation = annotation.copyWith(
          x: x,
          y: y,
          width: width,
          height: height,
        );

        // Importante: manter o estado como "resizing" durante toda a operação
        updateAnnotationInLists(updatedAnnotation, maintainResizingState: true);
        break;

      default:
        break;
    }
  }

  /// Trata o evento de fim de arrasto no canvas
  void onCanvasDragEnd() {
    if (selectedImage.value == null) return;

    switch (editorState.value) {
      case AnnotationEditorState.drawing:
        if (startPoint.value != null && currentPoint.value != null) {
          // Finalizar o desenho criando uma nova anotação
          createNewAnnotation();
        }
        editorState.value = AnnotationEditorState.idle;
        break;

      case AnnotationEditorState.moving:
      case AnnotationEditorState.resizing:
        // Após mover ou redimensionar, voltar para o estado de seleção
        // Garantir que a anotação ainda esteja selecionada
        if (selectedAnnotation.value != null) {
          editorState.value = AnnotationEditorState.selected;
        } else {
          editorState.value = AnnotationEditorState.idle;
        }
        
        // Limpar os pontos de referência do arrasto
        dragStartPoint.value = null;
        dragStartAnnotation.value = null;
        resizeCornerIndex.value = -1;
        break;

      default:
        editorState.value = AnnotationEditorState.idle;
        break;
    }
  }

  /// Cria uma nova anotação a partir dos pontos inicial e final
  void createNewAnnotation() {
    if (startPoint.value == null || currentPoint.value == null ||
        selectedImage.value == null || loadedImage.value == null) return;

    // Converter os pontos para coordenadas normalizadas
    final Offset startNorm = toNormalizedCoordinates(startPoint.value!);
    final Offset endNorm = toNormalizedCoordinates(currentPoint.value!);

    // Calcular as coordenadas do retângulo em coordenadas normalizadas
    final double x = min(startNorm.dx, endNorm.dx).clamp(0.0, 1.0);
    final double y = min(startNorm.dy, endNorm.dy).clamp(0.0, 1.0);
    final double width = (max(startNorm.dx, endNorm.dx) - x).clamp(0.01, 1.0 - x);
    final double height = (max(startNorm.dy, endNorm.dy) - y).clamp(0.01, 1.0 - y);

    // Verificar tamanho mínimo
    if (width < 0.01 || height < 0.01) return;

    // Criar a anotação
    Annotation newAnnotation = Annotation(
      imageId: selectedImage.value!.id,
      datasetId: selectedDataset.value!.id,
      classId: selectedClass.value.isNotEmpty ? classes.indexOf(selectedClass.value) + 1 : 1,
      className: selectedClass.value,
      x: x,
      y: y,
      width: width,
      height: height,
      colorValue: classColors[selectedClass.value]?.value,
    );

    // Atribuir ID temporário negativo
    final int tempId = -(annotations.length + pendingAnnotations.length + 1);
    newAnnotation = newAnnotation.copyWith(id: tempId);

    // Adicionar às listas
    annotations.add(newAnnotation);
    pendingAnnotations.add(newAnnotation);

    // Selecionar a nova anotação
    selectedAnnotation.value = newAnnotation;
    editorState.value = AnnotationEditorState.selected;

    LoggerUtil.debug("Nova anotação criada: ${newAnnotation.id} em ($x, $y) ${width}x${height}");
  }

  /// Atualiza uma anotação nas listas de anotações
  void updateAnnotationInLists(Annotation updatedAnnotation, {bool maintainMovingState = false, bool maintainResizingState = false}) {
    if (updatedAnnotation.id == null) return;

    // Atualizar na lista principal
    final int index = annotations.indexWhere((a) => a.id == updatedAnnotation.id);
    if (index >= 0) {
      annotations[index] = updatedAnnotation;

      // Atualizar a anotação selecionada se for a mesma
      if (selectedAnnotation.value?.id == updatedAnnotation.id) {
        selectedAnnotation.value = updatedAnnotation;
      }

      // Atualizar ou adicionar à lista de pendentes
      final int pendingIndex = pendingAnnotations.indexWhere((a) => a.id == updatedAnnotation.id);
      if (pendingIndex >= 0) {
        pendingAnnotations[pendingIndex] = updatedAnnotation;
      } else {
        pendingAnnotations.add(updatedAnnotation);
      }
    }

    // Importante: manter o estado como "moving" ou "resizing" durante toda a operação
    if (maintainResizingState) {
      // Forçar o estado para resizing independentemente do valor de resizeCornerIndex
      editorState.value = AnnotationEditorState.resizing;
    } else if (maintainMovingState) {
      editorState.value = AnnotationEditorState.moving;
    }
  }

  //
  // Métodos de ações do usuário
  //

  /// Cancela a seleção ou edição atual
  void cancelSelection() {
    editorState.value = AnnotationEditorState.idle;
    selectedAnnotation.value = null;
  }

  /// Remove a anotação selecionada
  void deleteSelectedAnnotation() {
    if (selectedAnnotation.value == null) return;

    final annotationId = selectedAnnotation.value!.id;
    if (annotationId == null) return;

    if (annotationId < 0) {
      // Remover anotação temporária
      annotations.removeWhere((a) => a.id == annotationId);
      pendingAnnotations.removeWhere((a) => a.id == annotationId);
      selectedAnnotation.value = null;
      editorState.value = AnnotationEditorState.idle;
    } else {
      // Confirmar exclusão de anotação existente
      Get.dialog(
        AlertDialog(
          title: const Text('Confirmar exclusão'),
          content: const Text('Deseja excluir esta anotação? Esta ação é imediata e não pode ser desfeita.'),
          actions: [
            TextButton(
              onPressed: () => Get.back(),
              child: const Text('Cancelar'),
            ),
            TextButton(
              onPressed: () {
                Get.back();
                deleteAnnotationFromApi(annotationId);
              },
              child: const Text('Excluir'),
            ),
          ],
        ),
      );
    }
  }

  /// Exclui uma anotação através da API
  Future<void> deleteAnnotationFromApi(int annotationId) async {
    isSaving.value = true;

    try {
      final bool result = await _annotationService.deleteAnnotation(annotationId);
      if (result) {
        annotations.removeWhere((a) => a.id == annotationId);
        pendingAnnotations.removeWhere((a) => a.id == annotationId);

        if (selectedAnnotation.value?.id == annotationId) {
          selectedAnnotation.value = null;
          editorState.value = AnnotationEditorState.idle;
        }

        Get.snackbar(
          'Sucesso',
          'Anotação excluída com sucesso',
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: Colors.green,
          colorText: Colors.white,
          duration: const Duration(seconds: 2),
        );
      }
    } catch (e) {
      LoggerUtil.error('Erro ao excluir anotação: $e');
      errorMessage.value = 'Erro ao excluir anotação: $e';

      Get.snackbar(
        'Erro',
        'Falha ao excluir anotação: $e',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.red,
        colorText: Colors.white,
      );
    } finally {
      isSaving.value = false;
    }
  }

  /// Salva todas as anotações pendentes
  Future<bool> saveAllAnnotations() async {
    if (pendingAnnotations.isEmpty) return true;

    isSaving.value = true;
    try {
      // Separar novas anotações e atualizações
      final List<Annotation> newAnnotations = pendingAnnotations
          .where((a) => a.id != null && a.id! < 0)
          .toList();

      final List<Annotation> updateAnnotations = pendingAnnotations
          .where((a) => a.id != null && a.id! > 0)
          .toList();

      // Processar novas anotações em lote
      if (newAnnotations.isNotEmpty) {
        final List<Annotation> preparedAnnotations = newAnnotations
            .map((a) => a.copyWith(id: null))
            .toList();

        final result = await _annotationService.createAnnotationsBatch(
            selectedImage.value!.id,
            selectedDataset.value!.id,
            preparedAnnotations
        );

        if (result.isNotEmpty) {
          // Substituir anotações temporárias pelas definitivas
          for (int i = 0; i < newAnnotations.length; i++) {
            if (i < result.length) {
              final int tempIndex = annotations.indexWhere((a) =>
              a.id == newAnnotations[i].id);

              if (tempIndex >= 0) {
                annotations[tempIndex] = result[i];

                // Atualizar a anotação selecionada se necessário
                if (selectedAnnotation.value?.id == newAnnotations[i].id) {
                  selectedAnnotation.value = result[i];
                }
              }
            }
          }
        }
      }

      // Processar atualizações
      for (final annotation in updateAnnotations) {
        final result = await _annotationService.updateAnnotation(annotation);
        if (result != null) {
          final int index = annotations.indexWhere((a) => a.id == annotation.id);
          if (index >= 0) {
            annotations[index] = result;

            // Atualizar a anotação selecionada se necessário
            if (selectedAnnotation.value?.id == annotation.id) {
              selectedAnnotation.value = result;
            }
          }
        }
      }

      // Limpar pendentes
      pendingAnnotations.clear();

      // Atualizar a imagem selecionada
      if (selectedImage.value != null) {
        selectedImage.value = selectedImage.value!.copyWith(
          annotations: annotations.toList(),
        );
      }

      Get.snackbar(
        'Sucesso',
        'Anotações salvas com sucesso',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.green,
        colorText: Colors.white,
      );

      return true;
    } catch (e) {
      LoggerUtil.error('Erro ao salvar anotações: $e');
      errorMessage.value = 'Erro ao salvar anotações: $e';

      Get.snackbar(
        'Erro',
        'Falha ao salvar anotações: $e',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.red,
        colorText: Colors.white,
      );

      return false;
    } finally {
      isSaving.value = false;
    }
  }

  /// Exporta as anotações para formato YOLO
  Future<void> exportToYolo() async {
    if (selectedDataset.value == null) return;

    // Verificar se há anotações pendentes
    if (hasUnsavedChanges.value) {
      Get.dialog(
        AlertDialog(
          title: const Text('Anotações não salvas'),
          content: const Text('Há anotações não salvas. Deseja salvá-las antes de exportar?'),
          actions: [
            TextButton(
              onPressed: () {
                Get.back();
                exportToYoloInternal();
              },
              child: const Text('Exportar sem salvar'),
            ),
            TextButton(
              onPressed: () async {
                Get.back();
                final saved = await saveAllAnnotations();
                if (saved) {
                  exportToYoloInternal();
                }
              },
              child: const Text('Salvar e exportar'),
            ),
          ],
        ),
      );
    } else {
      exportToYoloInternal();
    }
  }

  /// Implementação interna da exportação para YOLO
  Future<void> exportToYoloInternal() async {
    isSaving.value = true;

    try {
      final Map<String, dynamic> result =
      await _annotationService.convertToYolo(selectedDataset.value!.id);

      if (result.isNotEmpty) {
        Get.snackbar(
          'Sucesso',
          'Anotações exportadas para YOLO: ${result['export_path']}',
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: Colors.green,
          colorText: Colors.white,
          duration: const Duration(seconds: 5),
        );
      }
    } catch (e) {
      LoggerUtil.error('Erro ao exportar para YOLO: $e');
      errorMessage.value = 'Erro ao exportar para YOLO: $e';
    } finally {
      isSaving.value = false;
    }
  }

  /// Confirma com o usuário se deseja salvar as mudanças
  void _confirmSaveChanges() {
    Get.dialog(
      AlertDialog(
        title: const Text('Anotações não salvas'),
        content: const Text('Você tem anotações não salvas. Deseja salvá-las antes de continuar?'),
        actions: [
          TextButton(
            onPressed: () {
              Get.back();
              pendingAnnotations.clear();
              hasUnsavedChanges.value = false;
            },
            child: const Text('Descartar'),
          ),
          TextButton(
            onPressed: () {
              Get.back();
              saveAllAnnotations();
            },
            child: const Text('Salvar'),
          ),
        ],
      ),
    );
  }

  //
  // Métodos de navegação entre imagens
  //

  /// Verifica se há uma próxima imagem
  bool hasNextImage() {
    if (images.isEmpty || selectedImage.value == null) return false;

    final int currentIndex = images.indexWhere((img) => img.id == selectedImage.value!.id);
    return currentIndex < images.length - 1;
  }

  /// Verifica se há uma imagem anterior
  bool hasPreviousImage() {
    if (images.isEmpty || selectedImage.value == null) return false;

    final int currentIndex = images.indexWhere((img) => img.id == selectedImage.value!.id);
    return currentIndex > 0;
  }

  /// Navega para a próxima imagem
  void nextImage() {
    if (!hasNextImage()) return;

    if (hasUnsavedChanges.value) {
      _confirmSaveChanges();
      return;
    }

    final int currentIndex = images.indexWhere((img) => img.id == selectedImage.value!.id);
    if (currentIndex < images.length - 1) {
      selectImage(images[currentIndex + 1]);
    }
  }

  /// Navega para a imagem anterior
  void previousImage() {
    if (!hasPreviousImage()) return;

    if (hasUnsavedChanges.value) {
      _confirmSaveChanges();
      return;
    }

    final int currentIndex = images.indexWhere((img) => img.id == selectedImage.value!.id);
    if (currentIndex > 0) {
      selectImage(images[currentIndex - 1]);
    }
  }

  // Helpers
  double min(double a, double b) => a < b ? a : b;
  double max(double a, double b) => a > b ? a : b;
}