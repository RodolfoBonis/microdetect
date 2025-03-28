import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:flutter/foundation.dart';

import '../models/camera_image.dart';

/// Controles para a tela de câmera
class CameraControls extends StatelessWidget {
  /// Se a câmera tem uma imagem capturada (em modo de visualização)
  final bool isImageCaptured;
  
  /// Se está carregando para salvar a imagem
  final bool isSaving;
  
  /// Callback quando uma imagem é capturada
  final VoidCallback onCapture;
  
  /// Callback quando a imagem capturada é descartada
  final VoidCallback onDiscard;
  
  /// Callback quando a imagem é salva
  final VoidCallback onSave;
  
  /// Callback para aumentar o zoom
  final VoidCallback onZoomIn;
  
  /// Callback para diminuir o zoom
  final VoidCallback onZoomOut;
  
  /// Se o zoom está disponível
  final bool isZoomAvailable;
  
  /// ID do dataset atual
  final int? datasetId;
  
  /// Construtor padrão
  const CameraControls({
    Key? key,
    required this.isImageCaptured,
    this.isSaving = false,
    required this.onCapture,
    required this.onDiscard,
    required this.onSave,
    required this.onZoomIn,
    required this.onZoomOut,
    this.isZoomAvailable = true,
    this.datasetId,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(AppSpacing.medium),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.transparent,
            Colors.black.withOpacity(0.7),
          ],
        ),
      ),
      child: isImageCaptured
          ? _buildCaptureActions()
          : _buildCaptureButton(),
    );
  }

  /// Constrói o botão de captura
  Widget _buildCaptureButton() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // Zoom out
        IconButton(
          icon: Icon(
            Icons.remove_circle_outline,
            color: AppColors.white,
            size: 28,
          ),
          onPressed: isZoomAvailable ? onZoomOut : null,
          tooltip: 'Diminuir Zoom',
        ),
        
        SizedBox(width: AppSpacing.medium),
        
        // Botão de captura principal
        InkWell(
          onTap: onCapture,
          borderRadius: BorderRadius.circular(40),
          child: Container(
            width: 76,
            height: 76,
            decoration: BoxDecoration(
              color: Colors.transparent,
              shape: BoxShape.circle,
              border: Border.all(
                color: AppColors.white,
                width: 3,
              ),
            ),
            padding: const EdgeInsets.all(6),
            child: Container(
              decoration: BoxDecoration(
                color: AppColors.white,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.camera_alt,
                color: AppColors.black,
                size: 30,
              ),
            ),
          ),
        ),
        
        SizedBox(width: AppSpacing.medium),
        
        // Zoom in
        IconButton(
          icon: Icon(
            Icons.add_circle_outline,
            color: AppColors.white,
            size: 28,
          ),
          onPressed: isZoomAvailable ? onZoomIn : null,
          tooltip: 'Aumentar Zoom',
        ),
      ],
    );
  }

  /// Constrói os botões para ações após a captura
  Widget _buildCaptureActions() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // Botão de descartar
        ElevatedButton.icon(
          onPressed: onDiscard,
          icon: const Icon(Icons.delete_outline),
          label: const Text('Descartar'),
          style: ElevatedButton.styleFrom(
            foregroundColor: AppColors.white,
            backgroundColor: AppColors.error,
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.medium,
              vertical: AppSpacing.small,
            ),
          ),
        ),
        
        const SizedBox(width: AppSpacing.large),
        
        // Botão de salvar
        ElevatedButton.icon(
          onPressed: onSave,
          icon: const Icon(Icons.save_alt),
          label: Text(
            datasetId != null
                ? 'Salvar no Dataset'
                : 'Salvar na Galeria',
          ),
          style: ElevatedButton.styleFrom(
            foregroundColor: AppColors.white,
            backgroundColor: AppColors.secondary,
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.medium,
              vertical: AppSpacing.small,
            ),
          ),
        ),
      ],
    );
  }
} 