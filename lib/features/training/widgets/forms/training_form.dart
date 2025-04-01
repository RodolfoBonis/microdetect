import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';

/// Formulário para criar/editar um treinamento
class TrainingForm extends StatefulWidget {
  /// Parâmetros iniciais (opcional)
  final Map<String, dynamic>? initialData;

  /// Função chamada ao submeter o formulário
  final Function(Map<String, dynamic>) onSubmit;

  /// Construtor
  const TrainingForm({
    Key? key,
    this.initialData,
    required this.onSubmit,
  }) : super(key: key);

  @override
  State<TrainingForm> createState() => _TrainingFormState();
}

class _TrainingFormState extends State<TrainingForm> {
  // Controllers para os campos de texto
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();

  // Valores do formulário
  int? _selectedDatasetId;
  String _selectedModelType = 'yolov8';
  String _selectedModelVersion = 'n';
  int _epochs = 100;
  int _batchSize = 16;
  int _imageSize = 640;
  double _learningRate = 0.01;
  String _optimizer = 'auto';
  String _device = 'auto';
  int _patience = 50;

  // Chave do formulário para validação
  final _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _initializeForm();
  }

  /// Inicializa o formulário com valores padrão ou dados existentes
  void _initializeForm() {
    if (widget.initialData != null) {
      final data = widget.initialData!;

      _nameController.text = data['name'] ?? '';
      _descriptionController.text = data['description'] ?? '';
      _selectedDatasetId = data['dataset_id'];
      _selectedModelType = data['model_type'] ?? 'yolov8';
      _selectedModelVersion = data['model_version'] ?? 'n';

      // Hiperparâmetros
      if (data['hyperparameters'] != null) {
        final hyperparams = data['hyperparameters'] as Map<String, dynamic>;
        _epochs = hyperparams['epochs'] ?? 100;
        _batchSize = hyperparams['batch_size'] ?? 16;
        _imageSize = hyperparams['imgsz'] ?? 640;
        _learningRate = hyperparams['lr0'] ?? 0.01;
        _optimizer = hyperparams['optimizer'] ?? 'auto';
        _device = hyperparams['device'] ?? 'auto';
        _patience = hyperparams['patience'] ?? 50;
      }
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final datasetController =
        Get.find<DatasetController>(tag: 'datasetController');

    return Form(
      key: _formKey,
      child: ListView(
        padding: AppSpacing.paddingLarge,
        children: [
          // Seção de informações básicas
          _buildSectionTitle(context, 'Informações Básicas'),

          // Nome do treinamento
          TextFormField(
            controller: _nameController,
            decoration: const InputDecoration(
              labelText: 'Nome do treinamento*',
              hintText: 'Ex: YOLOv8 Detecção de Microorganismos',
            ),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Por favor, informe um nome para o treinamento';
              }
              return null;
            },
          ),
          const SizedBox(height: 16),

          // Descrição
          TextFormField(
            controller: _descriptionController,
            decoration: const InputDecoration(
              labelText: 'Descrição',
              hintText:
                  'Ex: Modelo para detectar microorganismos em imagens microscópicas',
            ),
            maxLines: 3,
          ),
          const SizedBox(height: 16),

          // Dataset
          Obx(() {
            if (datasetController.isLoading) {
              return const Center(
                child: Padding(
                  padding: EdgeInsets.all(16.0),
                  child: CircularProgressIndicator(),
                ),
              );
            }

            if (datasetController.datasets.isEmpty) {
              return Container(
                padding: AppSpacing.paddingMedium,
                decoration: BoxDecoration(
                  color: AppColors.errorLight,
                  borderRadius: AppBorders.medium,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(
                          Icons.warning_amber_rounded,
                          color: AppColors.error,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Nenhum dataset disponível',
                          style: AppTypography.labelMedium(context).copyWith(
                            color: AppColors.error,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Você precisa criar um dataset antes de iniciar um treinamento.',
                      style: AppTypography.bodySmall(context),
                    ),
                    const SizedBox(height: 8),
                    AppButton(
                      label: 'Criar Dataset',
                      onPressed: () => Get.toNamed('/root/datasets'),
                      type: AppButtonType.secondary,
                      prefixIcon: Icons.add,
                    ),
                  ],
                ),
              );
            }

            return DropdownButtonFormField<int>(
              decoration: const InputDecoration(
                labelText: 'Dataset*',
                hintText: 'Selecione um dataset',
              ),
              value: _selectedDatasetId,
              items: datasetController.datasets.map((Dataset dataset) {
                return DropdownMenuItem<int>(
                  value: dataset.id,
                  child: Text(dataset.name),
                );
              }).toList(),
              validator: (value) {
                if (value == null) {
                  return 'Por favor, selecione um dataset';
                }
                return null;
              },
              onChanged: (value) {
                setState(() {
                  _selectedDatasetId = value;
                });
              },
            );
          }),
          const SizedBox(height: 16),

          // Tipo e versão do modelo
          Row(
            children: [
              Expanded(
                flex: 3,
                child: DropdownButtonFormField<String>(
                  decoration: const InputDecoration(
                    labelText: 'Tipo de modelo*',
                  ),
                  value: _selectedModelType,
                  items: const [
                    DropdownMenuItem<String>(
                      value: 'yolov8',
                      child: Text('YOLOv8'),
                    ),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _selectedModelType = value!;
                    });
                  },
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                flex: 2,
                child: DropdownButtonFormField<String>(
                  decoration: const InputDecoration(
                    labelText: 'Versão*',
                  ),
                  value: _selectedModelVersion,
                  items: const [
                    DropdownMenuItem<String>(
                      value: 'n',
                      child: Text('Nano (n)'),
                    ),
                    DropdownMenuItem<String>(
                      value: 's',
                      child: Text('Small (s)'),
                    ),
                    DropdownMenuItem<String>(
                      value: 'm',
                      child: Text('Medium (m)'),
                    ),
                    DropdownMenuItem<String>(
                      value: 'l',
                      child: Text('Large (l)'),
                    ),
                    DropdownMenuItem<String>(
                      value: 'x',
                      child: Text('XLarge (x)'),
                    ),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _selectedModelVersion = value!;
                    });
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Seção de hiperparâmetros
          _buildSectionTitle(context, 'Hiperparâmetros de Treinamento'),

          // Épocas e Batch Size
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  decoration: const InputDecoration(
                    labelText: 'Épocas*',
                    hintText: '100',
                    helperText: 'Ciclos de treinamento',
                  ),
                  keyboardType: TextInputType.number,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  initialValue: _epochs.toString(),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Obrigatório';
                    }
                    final epochs = int.tryParse(value);
                    if (epochs == null || epochs < 1) {
                      return 'Min: 1';
                    }
                    return null;
                  },
                  onChanged: (value) {
                    setState(() {
                      _epochs = int.tryParse(value) ?? _epochs;
                    });
                  },
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: TextFormField(
                  decoration: const InputDecoration(
                    labelText: 'Batch Size*',
                    hintText: '16',
                    helperText: 'Imagens por lote',
                  ),
                  keyboardType: TextInputType.number,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  initialValue: _batchSize.toString(),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Obrigatório';
                    }
                    final batchSize = int.tryParse(value);
                    if (batchSize == null || batchSize < 1) {
                      return 'Min: 1';
                    }
                    return null;
                  },
                  onChanged: (value) {
                    setState(() {
                      _batchSize = int.tryParse(value) ?? _batchSize;
                    });
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Tamanho da Imagem e Taxa de Aprendizado
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<int>(
                  decoration: const InputDecoration(
                    labelText: 'Tamanho da Imagem*',
                    helperText: 'Resolução de entrada',
                  ),
                  value: _imageSize,
                  items: const [
                    DropdownMenuItem<int>(
                      value: 416,
                      child: Text('416 × 416'),
                    ),
                    DropdownMenuItem<int>(
                      value: 512,
                      child: Text('512 × 512'),
                    ),
                    DropdownMenuItem<int>(
                      value: 640,
                      child: Text('640 × 640'),
                    ),
                    DropdownMenuItem<int>(
                      value: 768,
                      child: Text('768 × 768'),
                    ),
                    DropdownMenuItem<int>(
                      value: 1024,
                      child: Text('1024 × 1024'),
                    ),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _imageSize = value!;
                    });
                  },
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: TextFormField(
                  decoration: const InputDecoration(
                    labelText: 'Taxa de Aprendizado*',
                    hintText: '0.01',
                    helperText: 'Taxa inicial (lr0)',
                  ),
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*$')),
                  ],
                  initialValue: _learningRate.toString(),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Obrigatório';
                    }
                    final lr = double.tryParse(value);
                    if (lr == null || lr <= 0 || lr > 1) {
                      return 'Entre 0 e 1';
                    }
                    return null;
                  },
                  onChanged: (value) {
                    setState(() {
                      _learningRate = double.tryParse(value) ?? _learningRate;
                    });
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Otimizador e Dispositivo
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  decoration: const InputDecoration(
                    labelText: 'Otimizador*',
                    helperText: 'Algoritmo de otimização',
                  ),
                  value: _optimizer,
                  items: const [
                    DropdownMenuItem<String>(
                      value: 'auto',
                      child: Text('Auto (recomendado)'),
                    ),
                    DropdownMenuItem<String>(
                      value: 'SGD',
                      child: Text('SGD'),
                    ),
                    DropdownMenuItem<String>(
                      value: 'Adam',
                      child: Text('Adam'),
                    ),
                    DropdownMenuItem<String>(
                      value: 'AdamW',
                      child: Text('AdamW'),
                    ),
                    DropdownMenuItem<String>(
                      value: 'RMSProp',
                      child: Text('RMSProp'),
                    ),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _optimizer = value!;
                    });
                  },
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: DropdownButtonFormField<String>(
                  decoration: const InputDecoration(
                    labelText: 'Dispositivo*',
                    helperText: 'Hardware de treinamento',
                  ),
                  value: _device,
                  items: const [
                    DropdownMenuItem<String>(
                      value: 'auto',
                      child: Text('Auto (recomendado)'),
                    ),
                    DropdownMenuItem<String>(
                      value: 'cpu',
                      child: Text('CPU'),
                    ),
                    DropdownMenuItem<String>(
                      value: '0',
                      child: Text('GPU 0'),
                    ),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _device = value!;
                    });
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Early Stopping
          TextFormField(
            decoration: const InputDecoration(
              labelText: 'Paciência (Early Stopping)*',
              hintText: '50',
              helperText: 'Parar se não houver melhoria após X épocas',
            ),
            keyboardType: TextInputType.number,
            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
            initialValue: _patience.toString(),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Obrigatório';
              }
              final patience = int.tryParse(value);
              if (patience == null || patience < 0) {
                return 'Min: 0';
              }
              return null;
            },
            onChanged: (value) {
              setState(() {
                _patience = int.tryParse(value) ?? _patience;
              });
            },
          ),
          const SizedBox(height: 32),

          // Botões de ação
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              AppButton(
                label: 'Cancelar',
                onPressed: () => Get.back(),
                type: AppButtonType.secondary,
              ),
              const SizedBox(width: 16),
              AppButton(
                label: 'Iniciar Treinamento',
                onPressed: _submitForm,
                prefixIcon: Icons.play_arrow,
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Constrói o título de uma seção
  Widget _buildSectionTitle(BuildContext context, String title) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: AppTypography.titleMedium(context),
        ),
        const SizedBox(height: 8),
        Divider(
          color: isDark ? AppColors.neutralDark : AppColors.neutralLight,
          thickness: 1,
        ),
        const SizedBox(height: 16),
      ],
    );
  }

  /// Submete o formulário
  void _submitForm() {
    if (_formKey.currentState?.validate() ?? false) {
      // Construir dados do treinamento
      final trainingData = {
        'name': _nameController.text,
        'description': _descriptionController.text,
        'dataset_id': _selectedDatasetId,
        'model_type': _selectedModelType,
        'model_version': _selectedModelVersion,
        'hyperparameters': {
          'epochs': _epochs,
          'batch_size': _batchSize,
          'imgsz': _imageSize,
          'lr0': _learningRate,
          'optimizer': _optimizer,
          'device': _device,
          'patience': _patience,
        },
      };

      // Chamar a função de callback
      widget.onSubmit(trainingData);
    }
  }
}
