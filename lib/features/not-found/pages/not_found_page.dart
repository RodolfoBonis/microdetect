import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';

class NotFoundPage extends StatelessWidget {
  final String title;

  const NotFoundPage({
    Key? key,
    required this.title,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.construction,
              size: 64,
              color: AppColors.tertiary,
            ),
            const SizedBox(height: 16),
            Text(
              'Módulo $title',
              style: AppTypography.textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Este módulo está em desenvolvimento',
              style: AppTypography.textTheme.bodyLarge?.copyWith(
                color: AppColors.neutralDark,
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(context);
              },
              child: const Text('Voltar'),
            ),
          ],
        ),
      ),
    );
  }
}