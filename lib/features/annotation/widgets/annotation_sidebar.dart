import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/annotation/controllers/annotation_controller.dart';
import 'package:microdetect/features/annotation/models/annotation.dart';

/// Widget de barra lateral para controles de anotação
class AnnotationSidebar extends StatelessWidget {
  const AnnotationSidebar({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final AnnotationController controller = Get.find<AnnotationController>();
    
    return Container(
      width: 280,
      padding: const EdgeInsets.all(AppSpacing.medium),
      decoration: const BoxDecoration(
        color: AppColors.surfaceLight,
        border: Border(
          left: BorderSide(
            color: AppColors.surfaceDark,
            width: 1,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Título
          Text(
            'Ferramentas de Anotação',
            style: AppTypography.headlineSmall(context),
          ),
          const SizedBox(height: AppSpacing.medium),
          
          // Ações principais
          Obx(() => _buildMainActions(controller, context)),
          
          const SizedBox(height: AppSpacing.medium),
          
          // Lista de classes disponíveis
          Text(
            'Classes',
            style: AppTypography.titleMedium(context),
          ),
          const SizedBox(height: AppSpacing.xSmall),
          
          // Lista de classes
          Obx(() => _buildClassList(controller, context)),
          
          const Divider(height: AppSpacing.large),
          
          // Lista de anotações da imagem atual
          Text(
            'Anotações na Imagem',
            style: AppTypography.titleMedium(context),
          ),
          const SizedBox(height: AppSpacing.xSmall),
          
          // Lista de anotações
          Expanded(
            child: Obx(() => _buildAnnotationList(controller, context)),
          ),
        ],
      ),
    );
  }

  /// Constrói os botões de ação principais baseados no estado atual
  Widget _buildMainActions(AnnotationController controller, BuildContext context) {
    final bool hasSelectedAnnotation = controller.selectedAnnotation.value != null;
    final AnnotationEditorState editorState = controller.editorState.value;
    
    // Botões específicos para quando uma anotação está selecionada
    if (hasSelectedAnnotation && 
        (editorState == AnnotationEditorState.selected || 
         editorState == AnnotationEditorState.moving || 
         editorState == AnnotationEditorState.resizing)) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Informações da anotação selecionada
          Container(
            padding: const EdgeInsets.all(AppSpacing.small),
            decoration: BoxDecoration(
              color: AppColors.white,
              borderRadius: BorderRadius.circular(AppSpacing.xSmall),
              border: Border.all(color: AppColors.surfaceDark),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Anotação Selecionada',
                  style: AppTypography.bodyMedium(context).copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: AppSpacing.xxSmall),
                Text(
                  'Classe: ${controller.selectedAnnotation.value?.className ?? "Desconhecida"}',
                  style: AppTypography.bodySmall(context),
                ),
                const SizedBox(height: AppSpacing.xxSmall),
                Text(
                  'Dimensões: ${_formatDimensions(controller.selectedAnnotation.value)}',
                  style: AppTypography.bodySmall(context),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: AppSpacing.small),
          
          // Botões de ação para a anotação selecionada
          Row(
            children: [
              Expanded(
                child: AppButton(
                  onPressed: () {
                    // Se já estiver movendo, cancelar, senão, iniciar movimento
                    if (editorState == AnnotationEditorState.moving) {
                      controller.cancelSelection();
                    } else {
                      controller.onCanvasTapDown(Offset.zero); // Simular clique na anotação
                    }
                  },
                  label: 'Mover',
                  suffixIcon: Icons.open_with,
                  type: editorState == AnnotationEditorState.moving
                      ? AppButtonType.primary
                      : AppButtonType.secondary,
                ),
              ),
              const SizedBox(width: AppSpacing.small),
              AppButton(
                onPressed: controller.deleteSelectedAnnotation,
                suffixIcon: Icons.delete_outline,
                label: 'Excluir',
              ),
            ],
          ),
          
          const SizedBox(height: AppSpacing.small),
          
          // Botão para cancelar seleção
          AppButton(
            onPressed: controller.cancelSelection,
            label: 'Cancelar Seleção',
            suffixIcon: Icons.close,
            type: AppButtonType.secondary,
            isFullWidth: true,
          ),
        ],
      );
    }
    
    // Estado padrão - sem anotação selecionada
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Botão para exportar para YOLO
        Row(
          children: [
            Expanded(
              child: AppButton(
                onPressed: controller.selectedDataset.value != null 
                    ? controller.exportToYolo 
                    : null,
                label: 'Exportar YOLO',
                suffixIcon: Icons.file_download_outlined,
                type: AppButtonType.secondary,
              ),
            ),
            const SizedBox(width: AppSpacing.small),
            AppIconButton(
              onPressed: controller.hasUnsavedChanges.value 
                  ? controller.saveAllAnnotations 
                  : null,
              icon: Icons.save,
              tooltip: 'Salvar Anotações',
              type: AppButtonType.success,
            ),
          ],
        ),
        
        const SizedBox(height: AppSpacing.small),
        
        // Avisos e notificações
        if (controller.hasUnsavedChanges.value)
          Container(
            padding: const EdgeInsets.all(AppSpacing.small),
            decoration: BoxDecoration(
              color: AppColors.warning.withOpacity(0.1),
              borderRadius: BorderRadius.circular(AppSpacing.xSmall),
              border: Border.all(color: AppColors.warning),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.warning_amber_rounded,
                  color: AppColors.warning,
                  size: 18,
                ),
                const SizedBox(width: AppSpacing.small),
                Expanded(
                  child: Text(
                    'Há anotações não salvas',
                    style: AppTypography.bodySmall(context),
                  ),
                ),
              ],
            ),
          ),
        
        if (controller.hasUnsavedChanges.value)
          const SizedBox(height: AppSpacing.small),
      ],
    );
  }

  /// Formata as dimensões da anotação de forma legível
  String _formatDimensions(Annotation? annotation) {
    if (annotation == null) return 'N/A';
    
    // Converter coordenadas normalizadas para porcentagens
    final int xPercent = (annotation.x * 100).round();
    final int yPercent = (annotation.y * 100).round();
    final int widthPercent = (annotation.width * 100).round();
    final int heightPercent = (annotation.height * 100).round();
    
    return '$widthPercent% × $heightPercent% em ($xPercent%, $yPercent%)';
  }

  /// Constrói a lista de classes disponíveis
  Widget _buildClassList(AnnotationController controller, BuildContext context) {
    if (controller.classes.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(AppSpacing.small),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppSpacing.xSmall),
        ),
        child: Text(
          'Nenhuma classe definida para este dataset',
          style: AppTypography.bodySmall(context),
          textAlign: TextAlign.center,
        ),
      );
    }
    
    return Container(
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(AppSpacing.xSmall),
        border: Border.all(color: AppColors.surfaceDark),
      ),
      constraints: const BoxConstraints(
        maxHeight: 150,
      ),
      child: ListView.builder(
        shrinkWrap: true,
        padding: const EdgeInsets.all(AppSpacing.xxSmall),
        itemCount: controller.classes.length,
        itemBuilder: (context, index) {
          final className = controller.classes[index];
          final isSelected = controller.selectedClass.value == className;
          final color = controller.classColors[className] ?? AppColors.primary;
          
          return Material(
            color: isSelected ? color.withOpacity(0.1) : Colors.transparent,
            borderRadius: BorderRadius.circular(AppSpacing.xxSmall),
            child: InkWell(
              onTap: () => controller.selectClass(className),
              borderRadius: BorderRadius.circular(AppSpacing.xxSmall),
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.small,
                  vertical: AppSpacing.xSmall,
                ),
                child: Row(
                  children: [
                    Container(
                      width: 16,
                      height: 16,
                      decoration: BoxDecoration(
                        color: color,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                    const SizedBox(width: AppSpacing.small),
                    Expanded(
                      child: Text(
                        className,
                        style: AppTypography.bodyMedium(context).copyWith(
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                        ),
                      ),
                    ),
                    if (isSelected)
                      const Icon(
                        Icons.check,
                        size: 18,
                      ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  /// Constrói a lista de anotações da imagem atual
  Widget _buildAnnotationList(AnnotationController controller, BuildContext context) {
    if (controller.selectedImage.value == null) {
      return Center(
        child: Text(
          'Selecione uma imagem para ver suas anotações',
          style: AppTypography.bodyMedium(context),
          textAlign: TextAlign.center,
        ),
      );
    }
    
    if (controller.annotations.isEmpty) {
      return Center(
        child: Text(
          'Nenhuma anotação encontrada nesta imagem',
          style: AppTypography.bodyMedium(context),
          textAlign: TextAlign.center,
        ),
      );
    }
    
    return Container(
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(AppSpacing.xSmall),
        border: Border.all(color: AppColors.surfaceDark),
      ),
      child: ListView.separated(
        padding: const EdgeInsets.all(AppSpacing.xxSmall),
        itemCount: controller.annotations.length,
        separatorBuilder: (context, index) => const Divider(height: 1),
        itemBuilder: (context, index) {
          final annotation = controller.annotations[index];
          final isSelected = controller.selectedAnnotation.value?.id == annotation.id;
          final isPending = controller.pendingAnnotations.any((a) => a.id == annotation.id);
          
          Color? color;
          if (annotation.colorValue != null) {
            color = Color(annotation.colorValue!);
          } else if (annotation.className != null && controller.classColors.containsKey(annotation.className)) {
            color = controller.classColors[annotation.className];
          } else {
            color = AppColors.primary;
          }
          
          return Material(
            color: isSelected ? color!.withOpacity(0.1) : Colors.transparent,
            child: InkWell(
              onTap: () => controller.selectedAnnotation.value = annotation,
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.small),
                child: Row(
                  children: [
                    Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        color: color,
                        borderRadius: BorderRadius.circular(3),
                      ),
                    ),
                    const SizedBox(width: AppSpacing.small),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            annotation.className ?? 'Desconhecido',
                            style: AppTypography.bodyMedium(context).copyWith(
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          Text(
                            '#${annotation.id ?? 'novo'} - ${_formatDimensions(annotation)}',
                            style: AppTypography.bodySmall(context).copyWith(
                              color: AppColors.grey,
                              fontSize: 10,
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (isPending)
                      const Padding(
                        padding: EdgeInsets.only(right: AppSpacing.xxSmall),
                        child: Tooltip(
                          message: 'Anotação não salva',
                          child: Icon(
                            Icons.sync,
                            size: 16,
                            color: AppColors.warning,
                          ),
                        ),
                      ),
                    const Icon(
                      Icons.chevron_right,
                      size: 18,
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
} 