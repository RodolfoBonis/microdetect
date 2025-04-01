import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/widgets/base_page_scaffold.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';

import '../controllers/training_controller.dart';
import '../widgets/forms/training_form.dart';

/// Página para criar um novo treinamento
class TrainingCreatePage extends StatelessWidget {
  final controller = Get.find<TrainingController>();

  // Verificar se há dados iniciais via argumentos de rota
  final Map<String, dynamic>? initialData =
      Get.arguments as Map<String, dynamic>?;

  /// Construtor
  TrainingCreatePage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return BasePageScaffold(
      title: 'Novo Treinamento',
      body: Obx(() {
        // Mostrar loading se necessário
        if (controller.isLoading.value) {
          return const Center(
            child: CircularProgressIndicator(),
          );
        }

        // Mostrar erro se ocorrer
        if (controller.errorMessage.value.isNotEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.error_outline,
                  size: 64,
                  color: AppColors.error,
                ),
                const SizedBox(height: 16),
                Text(
                  'Erro ao iniciar treinamento',
                  style: AppTypography.titleMedium(context),
                ),
                const SizedBox(height: 8),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 32.0),
                  child: Text(
                    controller.errorMessage.value,
                    style: AppTypography.bodyMedium(context),
                    textAlign: TextAlign.center,
                  ),
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: () => controller.errorMessage.value = '',
                  child: const Text('Tentar Novamente'),
                ),
              ],
            ),
          );
        }

        // Formulário de treinamento
        return TrainingForm(
          initialData: initialData,
          onSubmit: (data) async {
            // Iniciar treinamento
            final session = await controller.startTraining(data);
            if (session != null) {
              // Navegar para página de detalhes
              Get.offAndToNamed('/root/training/details/${session.id}');
            }
          },
        );
      }),
    );
  }
}
