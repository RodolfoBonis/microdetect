import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_borders.dart';

/// Widget para visualizar a matriz de confusão
class ConfusionMatrixWidget extends StatelessWidget {
  /// Dados da matriz de confusão
  final List<List<int>> matrix;

  /// Nomes das classes
  final List<String> classNames;

  /// Título do widget
  final String title;

  /// Se deve mostrar valores percentuais
  final bool showPercentages;

  /// Construtor
  const ConfusionMatrixWidget({
    Key? key,
    required this.matrix,
    required this.classNames,
    this.title = 'Matriz de Confusão',
    this.showPercentages = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (matrix.isEmpty || classNames.isEmpty || matrix.length != classNames.length) {
      // Renderizar mensagem de erro ou espaço vazio
      return Container(
        padding: AppSpacing.paddingMedium,
        decoration: BoxDecoration(
          color: ThemeColors.surfaceVariant(context),
          borderRadius: AppBorders.medium,
        ),
        child: Center(
          child: Text(
            'Dados inválidos para matriz de confusão',
            style: AppTypography.bodyMedium(context),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: AppSpacing.paddingMedium,
          child: Text(
            title,
            style: AppTypography.titleMedium(context),
          ),
        ),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Padding(
            padding: AppSpacing.paddingMedium,
            child: _buildMatrix(context),
          ),
        ),
      ],
    );
  }

  /// Constrói a matriz de confusão
  Widget _buildMatrix(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // Calcular tamanho máximo da célula com base nos nomes das classes
    final maxNameLength = classNames.fold<int>(
        0,
            (max, name) => name.length > max ? name.length : max
    );

    final cellSize = maxNameLength > 10 ? 90.0 : 70.0;

    // Criar linhas e colunas
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // Cabeçalho com "Predito" e nomes das classes
        Row(
          children: [
            // Célula vazia no canto superior esquerdo
            Container(
              width: cellSize,
              height: cellSize,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: isDark ? AppColors.neutralDarkest : AppColors.neutralLightest,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(AppBorders.radiusMedium),
                ),
                border: Border.all(
                  color: isDark ? AppColors.neutralDark : AppColors.neutralLight,
                ),
              ),
              child: RotatedBox(
                quarterTurns: 3,
                child: Text(
                  'Real',
                  style: AppTypography.labelMedium(context),
                ),
              ),
            ),
            // Rótulo "Predito"
            Container(
              width: cellSize * classNames.length,
              height: cellSize / 2,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: isDark ? AppColors.neutralDarkest : AppColors.neutralLightest,
                borderRadius: BorderRadius.only(
                  topRight: Radius.circular(AppBorders.radiusMedium),
                ),
                border: Border.all(
                  color: isDark ? AppColors.neutralDark : AppColors.neutralLight,
                ),
              ),
              child: Text(
                'Predito',
                style: AppTypography.labelMedium(context),
              ),
            ),
          ],
        ),
        // Linha com nomes das classes (preditos)
        Row(
          children: [
            // Célula vazia no canto esquerdo
            SizedBox(width: cellSize),
            // Nomes das classes
            ...classNames.map((name) => Container(
              width: cellSize,
              height: cellSize / 2,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: isDark ? AppColors.neutralDarkest : AppColors.neutralLightest,
                border: Border.all(
                  color: isDark ? AppColors.neutralDark : AppColors.neutralLight,
                ),
              ),
              child: Text(
                name,
                style: AppTypography.labelSmall(context),
                overflow: TextOverflow.ellipsis,
                textAlign: TextAlign.center,
              ),
            )),
          ],
        ),
        // Linhas da matriz
        ...List.generate(matrix.length, (i) {
          // Calcular total para percentagens
          final rowSum = matrix[i].fold<int>(0, (sum, value) => sum + value);

          return Row(
            children: [
              // Nome da classe (real)
              Container(
                width: cellSize,
                height: cellSize,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: isDark ? AppColors.neutralDarkest : AppColors.neutralLightest,
                  border: Border.all(
                    color: isDark ? AppColors.neutralDark : AppColors.neutralLight,
                  ),
                ),
                child: Text(
                  classNames[i],
                  style: AppTypography.labelSmall(context),
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.center,
                ),
              ),
              // Valores da matriz
              ...List.generate(matrix[i].length, (j) {
                final value = matrix[i][j];

                // Calcular cor da célula
                final colorIntensity = rowSum > 0
                    ? value / rowSum
                    : 0.0;

                final Color cellColor = i == j
                    ? AppColors.primary.withOpacity(colorIntensity)
                    : AppColors.error.withOpacity(colorIntensity);

                final textColor = colorIntensity > 0.5
                    ? Colors.white
                    : isDark
                    ? AppColors.white
                    : AppColors.neutralDarkest;

                // Texto a exibir (valor absoluto ou percentagem)
                final displayText = showPercentages && rowSum > 0
                    ? '${(value / rowSum * 100).toStringAsFixed(1)}%'
                    : '$value';

                return Container(
                  width: cellSize,
                  height: cellSize,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: cellColor,
                    border: Border.all(
                      color: isDark ? AppColors.neutralDark : AppColors.neutralLight,
                    ),
                  ),
                  child: Text(
                    displayText,
                    style: AppTypography.bodyMedium(context).copyWith(
                      fontWeight: i == j ? FontWeight.bold : FontWeight.normal,
                      color: textColor,
                    ),
                  ),
                );
              }),
            ],
          );
        }),
      ],
    );
  }
}