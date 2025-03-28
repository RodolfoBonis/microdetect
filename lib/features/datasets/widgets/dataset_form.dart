import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../design_system/app_colors.dart';
import '../../../design_system/app_spacing.dart';
import '../../../design_system/app_typography.dart';
import '../../../design_system/app_buttons.dart';
import '../../../design_system/app_text.dart';
import '../models/dataset.dart';

class DatasetForm extends StatefulWidget {
  final Function(String name, String? description, List<String> classes) onSubmit;
  final Function()? onCancel;
  final String? initialName;
  final String? initialDescription;
  final List<String>? initialClasses;

  const DatasetForm({
    Key? key,
    required this.onSubmit,
    this.onCancel,
    this.initialName,
    this.initialDescription,
    this.initialClasses,
  }) : super(key: key);

  @override
  _DatasetFormState createState() => _DatasetFormState();
}

class _DatasetFormState extends State<DatasetForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _classController = TextEditingController();
  
  List<String> _classes = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.initialName != null) {
      _nameController.text = widget.initialName!;
    }
    
    if (widget.initialDescription != null) {
      _descriptionController.text = widget.initialDescription!;
    }
    
    if (widget.initialClasses != null) {
      _classes = List.from(widget.initialClasses!);
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    _classController.dispose();
    super.dispose();
  }

  void _addClass() {
    final className = _classController.text.trim();
    if (className.isNotEmpty && !_classes.contains(className)) {
      setState(() {
        _classes.add(className);
        _classController.clear();
      });
    }
  }
  
  void _removeClass(String className) {
    setState(() {
      _classes.remove(className);
    });
  }

  Future<void> _submitForm() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
      });
      
      try {
        await widget.onSubmit(
          _nameController.text.trim(),
          _descriptionController.text.trim().isNotEmpty ? _descriptionController.text.trim() : null,
          _classes,
        );
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Nome do Dataset',
            style: AppTypography.labelMedium(context).copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: AppSpacing.xSmall),
          TextFormField(
            controller: _nameController,
            decoration: const InputDecoration(
              hintText: 'Ex: Bactérias Gram Positivas',
            ),
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Por favor, insira um nome para o dataset';
              }
              return null;
            },
          ),
          const SizedBox(height: AppSpacing.medium),
          
          Text(
            'Descrição (opcional)',
            style: AppTypography.labelMedium(context).copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: AppSpacing.xSmall),
          TextFormField(
            controller: _descriptionController,
            decoration: const InputDecoration(
              hintText: 'Descreva o propósito deste dataset...',
            ),
            maxLines: 3,
          ),
          const SizedBox(height: AppSpacing.medium),
          
          Text(
            'Classes (opcional)',
            style: AppTypography.labelMedium(context).copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: AppSpacing.xSmall),
          Text(
            'Defina as possíveis classes de objetos neste dataset',
            style: AppTypography.bodySmall(context).copyWith(
              color: AppColors.grey,
            ),
          ),
          const SizedBox(height: AppSpacing.small),
          
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _classController,
                  decoration: const InputDecoration(
                    hintText: 'Ex: Bacilo, Coco, Estreptococo...',
                  ),
                  onFieldSubmitted: (_) => _addClass(),
                ),
              ),
              const SizedBox(width: AppSpacing.small),
              IconButton(
                onPressed: _addClass,
                icon: const Icon(Icons.add),
                tooltip: 'Adicionar classe',
                color: AppColors.primary,
              ),
            ],
          ),
          
          if (_classes.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.small),
            Container(
              padding: const EdgeInsets.all(AppSpacing.small),
              decoration: BoxDecoration(
                color: Theme.of(context).cardColor,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: Theme.of(context).dividerColor,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Classes definidas',
                    style: AppTypography.labelMedium(context).copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.xSmall),
                  Wrap(
                    spacing: AppSpacing.xSmall,
                    runSpacing: AppSpacing.xSmall,
                    children: _classes.map((className) {
                      return Chip(
                        label: Text(className),
                        deleteIcon: const Icon(Icons.close, size: 16),
                        onDeleted: () => _removeClass(className),
                        backgroundColor: AppColors.secondary.withOpacity(0.1),
                        labelStyle: AppTypography.labelSmall(context).copyWith(
                          color: AppColors.secondary,
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
          ],
          
          const SizedBox(height: AppSpacing.large),
          
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              if (widget.onCancel != null)
                AppButton(
                  onPressed: widget.onCancel!,
                  label: 'Cancelar',
                  type: AppButtonType.tertiary,
                ),
              const SizedBox(width: AppSpacing.medium),
              AppButton(
                onPressed: _isLoading ? null : _submitForm,
                label: 'Salvar Dataset',
                type: AppButtonType.primary,
                isLoading: _isLoading,
              ),
            ],
          ),
        ],
      ),
    );
  }
} 