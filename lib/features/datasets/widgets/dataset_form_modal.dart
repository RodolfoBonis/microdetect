import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import '../../../design_system/app_colors.dart';
import '../../../design_system/app_spacing.dart';
import '../../../design_system/app_typography.dart';
import '../models/dataset.dart';

class DatasetFormModal extends StatelessWidget {
  /// Indica se estamos editando um dataset existente
  final bool isEditing;

  /// Dataset a ser editado (opcional)
  final Dataset? dataset;

  /// Função chamada quando um dataset é criado com sucesso
  final Function(String name, String? description, List<String> classes)
      onSubmit;

  // Controllers para os campos do formulário
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();
  final TextEditingController _classController = TextEditingController();
  final RxList<String> _classes = RxList<String>([]);
  final RxBool _isSubmitting = RxBool(false);

  DatasetFormModal({
    Key? key,
    this.isEditing = false,
    this.dataset,
    required this.onSubmit,
  }) : super(key: key) {
    // Preencher os campos com dados do dataset existente, se fornecido
    if (dataset != null) {
      _nameController.text = dataset?.name ?? "";
      _descriptionController.text = dataset?.description ?? '';
      _classes.addAll(dataset?.classes ?? []);
    }
  }

  /// Mostra a modal de criação/edição de dataset
  static void show({
    required BuildContext context,
    bool isEditing = false,
    Dataset? dataset,
    required Function(String name, String? description, List<String> classes)
        onSubmit,
  }) {
    showDialog(
      context: context,
      builder: (context) => DatasetFormModal(
        isEditing: isEditing,
        dataset: dataset,
        onSubmit: onSubmit,
      ),
    );
  }

  // Adicionar uma nova classe
  void _addClass() {
    final className = _classController.text.trim();
    if (className.isNotEmpty && !_classes.contains(className)) {
      _classes.add(className);
      _classController.clear();
    }
  }

  // Remover uma classe
  void _removeClass(String className) {
    _classes.remove(className);
  }

  // Validar e enviar o formulário
  void _handleSubmit(BuildContext context) {
    final name = _nameController.text.trim();
    final description = _descriptionController.text.trim();

    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Por favor, digite um nome para o dataset'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    _isSubmitting.value = true;

    try {
      onSubmit(
        name,
        description.isEmpty ? null : description,
        _classes,
      );

      Navigator.of(context).pop();
    } finally {
      _isSubmitting.value = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      child: ConstrainedBox(
        constraints: const BoxConstraints(
          maxWidth: 600,
          maxHeight: 800,
        ),
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.medium),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Título do modal
                Text(
                  isEditing ? 'Editar Dataset' : 'Novo Dataset',
                  style: AppTypography.headlineSmall(context),
                ),
                const SizedBox(height: AppSpacing.medium),

                // Campo Nome
                TextField(
                  controller: _nameController,
                  decoration: const InputDecoration(
                    labelText: 'Nome *',
                    hintText: 'Digite o nome do dataset',
                    border: OutlineInputBorder(),
                  ),
                  maxLength: 100,
                ),
                const SizedBox(height: AppSpacing.medium),

                // Campo Descrição
                TextField(
                  controller: _descriptionController,
                  decoration: const InputDecoration(
                    labelText: 'Descrição',
                    hintText: 'Descreva o conteúdo do dataset',
                    border: OutlineInputBorder(),
                  ),
                  maxLines: 3,
                  maxLength: 500,
                ),
                const SizedBox(height: AppSpacing.medium),

                // Seção Classes
                Text(
                  'Classes (opcional)',
                  style: AppTypography.titleMedium(context),
                ),
                const SizedBox(height: AppSpacing.small),
                Text(
                  'Adicione classes para categorizar as imagens neste dataset',
                  style: AppTypography.bodySmall(context),
                ),
                const SizedBox(height: AppSpacing.small),

                // Campo Classes + Botão Adicionar
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _classController,
                        decoration: const InputDecoration(
                          labelText: 'Nova Classe',
                          hintText: 'Digite o nome da classe',
                          border: OutlineInputBorder(),
                        ),
                        onSubmitted: (_) => _addClass(),
                      ),
                    ),
                    const SizedBox(width: AppSpacing.small),
                    AppButton(
                      onPressed: _addClass,
                      label: "Adicionar",
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.small),

                // Lista de Classes
                Obx(() => Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (_classes.isNotEmpty)
                          const SizedBox(height: AppSpacing.small),
                        for (final className in _classes)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 4),
                            child: Chip(
                              label: Text(className),
                              deleteIcon: const Icon(Icons.close, size: 16),
                              onDeleted: () => _removeClass(className),
                            ),
                          ),
                      ],
                    )),
                const SizedBox(height: AppSpacing.large),

                // Botões de ação
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    TextButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('Cancelar'),
                    ),
                    const SizedBox(width: AppSpacing.small),
                    Obx(
                      () => AppButton(
                        onPressed: _isSubmitting.value
                            ? null
                            : () => _handleSubmit(context),
                        label: isEditing ? 'Atualizar' : 'Criar',
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
