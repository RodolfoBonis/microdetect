import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import '../controllers/backend_monitor_controller.dart';

class ErrorScreenWidget extends StatelessWidget {
  final BackendMonitorController controller = Get.find<BackendMonitorController>();

  ErrorScreenWidget({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 600),
          padding: const EdgeInsets.all(AppSpacing.large),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const Icon(
                Icons.error_outline,
                color: AppColors.error,
                size: 80,
              ),
              const SizedBox(height: AppSpacing.medium),
              Text(
                'Erro no Backend',
                textAlign: TextAlign.center,
                style: AppTypography.headlineLarge(context).copyWith(
                  color: AppColors.error,
                ),
              ),
              const SizedBox(height: AppSpacing.medium),
              Obx(() => Text(
                controller.getDetailedErrorMessage(),
                textAlign: TextAlign.center,
                style: AppTypography.bodyLarge(context),
              )),
              const SizedBox(height: AppSpacing.large),
              
              // Card com os diagnósticos
              Card(
                elevation: 3,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(color: ThemeColors.border(context)),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.medium),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Diagnóstico',
                        style: AppTypography.titleMedium(context),
                      ),
                      const SizedBox(height: AppSpacing.small),
                      Obx(() => controller.lastDiagnosticResult.value != null
                        ? _buildDiagnosticResults(context)
                        : const Center(
                            child: Text(
                              'Execute o diagnóstico para analisar o problema',
                              textAlign: TextAlign.center,
                            ),
                          ),
                      ),
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: AppSpacing.large),
              
              // Logs (resumido)
              Card(
                elevation: 3,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(color: ThemeColors.border(context)),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.medium),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Últimos Logs',
                        style: AppTypography.titleMedium(context),
                      ),
                      const SizedBox(height: AppSpacing.small),
                      Container(
                        constraints: const BoxConstraints(maxHeight: 200),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1E1E1E),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        padding: const EdgeInsets.all(AppSpacing.small),
                        child: Obx(() => ListView.builder(
                          itemCount: controller.logs.isEmpty 
                              ? 1 
                              : controller.logs.length > 10 
                                  ? 10 
                                  : controller.logs.length,
                          itemBuilder: (context, index) {
                            if (controller.logs.isEmpty) {
                              return const Center(
                                child: Text(
                                  'Nenhum log disponível',
                                  style: TextStyle(color: Colors.white70),
                                ),
                              );
                            }
                            
                            final logIndex = controller.logs.length > 10 
                                ? controller.logs.length - 10 + index 
                                : index;
                            final log = controller.logs[logIndex];
                            
                            return Text(
                              log,
                              style: const TextStyle(
                                color: Colors.white,
                                fontFamily: 'monospace',
                                fontSize: 12,
                              ),
                            );
                          },
                        )),
                      ),
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: AppSpacing.large),
              
              // Botões de ação
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  OutlinedButton.icon(
                    onPressed: controller.runDiagnostics,
                    icon: const Icon(Icons.search),
                    label: const Text('Executar Diagnóstico'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.medium,
                        vertical: AppSpacing.small,
                      ),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.medium),
                  ElevatedButton.icon(
                    onPressed: controller.forceRestartBackend,
                    icon: const Icon(Icons.restart_alt),
                    label: const Text('Forçar Reinício'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.medium,
                        vertical: AppSpacing.small,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDiagnosticResults(BuildContext context) {
    final diagnostics = controller.lastDiagnosticResult.value!;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: diagnostics.entries.map((entry) {
        final title = entry.key;
        final value = entry.value;
        final bool? isSuccess = value is bool ? value : null;
        
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Row(
            children: [
              if (isSuccess != null)
                Icon(
                  isSuccess ? Icons.check_circle : Icons.error,
                  color: isSuccess ? AppColors.success : AppColors.error,
                  size: 18,
                )
              else
                const Icon(
                  Icons.info,
                  color: AppColors.info,
                  size: 18,
                ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: AppTypography.bodySmall(context).copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (value is String && value.isNotEmpty)
                      Text(
                        value,
                        style: AppTypography.bodySmall(context),
                      ),
                  ],
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}
