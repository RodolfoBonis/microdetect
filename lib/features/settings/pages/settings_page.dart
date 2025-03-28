import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/settings/controllers/settings_controller.dart';
import 'package:microdetect/features/settings/widgets/settings_button_tile.dart';
import 'package:microdetect/features/settings/widgets/settings_section.dart';
import 'package:microdetect/features/settings/widgets/settings_switch_tile.dart';
import 'package:microdetect/features/settings/widgets/system_status_card.dart';

/// Tela de configurações do sistema com UI/UX aprimorada
class SettingsPage extends StatefulWidget {
  const SettingsPage({Key? key}) : super(key: key);

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> with SingleTickerProviderStateMixin {
  // Controller
  final SettingsController controller = Get.find<SettingsController>();
  
  // TabController
  late TabController _tabController;
  
  @override
  void initState() {
    super.initState();
    
    // Inicializar o TabController
    _tabController = TabController(length: 3, vsync: this);
    
    // Configurar o controller
    controller.setTabController(_tabController);
  }
  
  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Obx(() => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Barra de tabs
          _buildTabBar(),
          
          // Conteúdo da aba selecionada
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                // 1. Aba de interface
                _buildInterfaceTab(),
                
                // 2. Aba de sistema
                _buildSystemTab(),
                
                // 3. Aba de avançado
                _buildAdvancedTab(),
              ],
            ),
          ),
        ],
      )),
    );
  }

  // Constrói a barra de tabs
  Widget _buildTabBar() {
    final isDark = Get.isDarkMode;
    final tabBarColor = isDark ? AppColors.surfaceDark : AppColors.white;
    final tabBarTextColor = isDark ? AppColors.neutralLight : AppColors.neutralDark;
    
    return Container(
      decoration: BoxDecoration(
        color: tabBarColor,
        borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
        boxShadow: [
          BoxShadow(
            color: AppColors.black.withOpacity(0.05),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      margin: const EdgeInsets.only(
        left: AppSpacing.medium, 
        right: AppSpacing.medium,
        top: AppSpacing.medium,
      ),
      child: TabBar(
        controller: _tabController,
        labelColor: AppColors.primary,
        unselectedLabelColor: tabBarTextColor,
        indicatorColor: AppColors.primary,
        indicatorSize: TabBarIndicatorSize.tab,
        labelStyle: AppTypography.textTheme.bodyMedium?.copyWith(
          fontWeight: FontWeight.w600,
        ),
        tabs: const [
          Tab(
            icon: Icon(Icons.palette_outlined),
            text: 'Interface',
          ),
          Tab(
            icon: Icon(Icons.settings_outlined),
            text: 'Sistema',
          ),
          Tab(
            icon: Icon(Icons.code_outlined),
            text: 'Avançado',
          ),
        ],
      ),
    );
  }
  
  // Constrói a aba de interface
  Widget _buildInterfaceTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.medium),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Seção: Aparência
          SettingsSection(
            title: 'Aparência',
            children: [
              // Tema: Light, Dark, Sistema
              _buildThemeSelector(),
              
              // Configurações de câmera
              SettingsSwitchTile(
                title: 'Mostrar opções avançadas',
                subtitle: 'Exibe configurações e funcionalidades avançadas na interface',
                value: controller.settings.value.showAdvancedOptions,
                onChanged: (value) => controller.updateSetting(showAdvancedOptions: value),
                icon: Icons.view_comfy_alt_outlined,
              ),
            ],
          ),
          
          const SizedBox(height: AppSpacing.medium),
          
          // Seção: Idioma
          SettingsSection(
            title: 'Idioma',
            children: [
              // Seletor de idioma
              _buildLanguageSelector(),
            ],
          ),
          
          const SizedBox(height: AppSpacing.medium),
          
          // Seção: Diretórios
          SettingsSection(
            title: 'Diretórios',
            children: [
              // Diretório padrão de exportação
              SettingsButtonTile(
                title: 'Diretório de exportação',
                subtitle: controller.settings.value.defaultExportDir.isNotEmpty 
                    ? controller.settings.value.defaultExportDir 
                    : 'Nenhum diretório selecionado',
                onPressed: () => controller.selectDirectory('defaultExportDir'),
                icon: Icons.folder_outlined,
              ),
              
              // Diretório padrão de imagens da câmera
              SettingsButtonTile(
                title: 'Diretório de imagens da câmera',
                subtitle: controller.settings.value.defaultCameraDir.isNotEmpty 
                    ? controller.settings.value.defaultCameraDir 
                    : 'Nenhum diretório selecionado',
                onPressed: () => controller.selectDirectory('defaultCameraDir'),
                icon: Icons.camera_outlined,
              ),
            ],
          ),
          
          const SizedBox(height: AppSpacing.medium),
          
          // Seção: Gerenciamento de configurações
          SettingsSection(
            title: 'Gerenciamento de configurações',
            children: [
              // Exportar configurações
              SettingsButtonTile(
                title: 'Exportar configurações',
                subtitle: 'Salvar suas configurações em um arquivo JSON',
                onPressed: controller.exportSettingsToFile,
                icon: Icons.upload_file_outlined,
                isLoading: controller.isExportingSettings.value,
              ),
              
              // Importar configurações
              SettingsButtonTile(
                title: 'Importar configurações',
                subtitle: 'Carregar configurações a partir de um arquivo JSON',
                onPressed: controller.importSettingsFromFile,
                icon: Icons.download_outlined,
                isLoading: controller.isImportingSettings.value,
              ),
              
              // Restaurar configurações
              SettingsButtonTile(
                title: 'Restaurar configurações padrão',
                subtitle: 'Redefinir todas as configurações para os valores padrão',
                onPressed: controller.resetToDefaults,
                icon: Icons.restore_outlined,
                isDestructive: true,
              ),
            ],
          ),
        ],
      ),
    );
  }
  
  // Constrói a aba de sistema
  Widget _buildSystemTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.medium),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Status do sistema
          SystemStatusCard(isDarkMode: Get.isDarkMode),
          
          const SizedBox(height: AppSpacing.medium),
          
          // Seção: Backend
          SettingsSection(
            title: 'Backend Python',
            children: [
              // Status do backend simplificado para a tela de configurações
              Container(
                padding: const EdgeInsets.symmetric(
                  vertical: AppSpacing.small,
                  horizontal: AppSpacing.medium,
                ),
                child: Obx(() => Row(
                  children: [
                    Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        color: controller.isRestartingBackend.value 
                            ? AppColors.warning 
                            : controller.backendVersion.value.isNotEmpty 
                                ? AppColors.success 
                                : AppColors.warning,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.small),
                    Text(
                      controller.isRestartingBackend.value 
                          ? 'Reiniciando backend...'
                          : controller.backendVersion.value.isNotEmpty 
                              ? 'Backend Python em execução' 
                              : 'Status desconhecido',
                      style: AppTypography.textTheme.bodyMedium?.copyWith(
                        color: Get.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                      ),
                    ),
                  ],
                )),
              ),
              
              // Versão do backend
              Container(
                padding: const EdgeInsets.symmetric(
                  vertical: AppSpacing.small,
                  horizontal: AppSpacing.medium,
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.info_outline,
                      color: AppColors.primary,
                      size: 24,
                    ),
                    const SizedBox(width: AppSpacing.small),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Versão instalada',
                            style: AppTypography.textTheme.bodyMedium?.copyWith(
                              color: Get.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                            ),
                          ),
                          Text(
                            controller.backendVersion.value.isNotEmpty
                                ? controller.backendVersion.value
                                : 'Desconhecida',
                            style: AppTypography.textTheme.bodySmall?.copyWith(
                              color: Get.isDarkMode ? AppColors.neutralLight.withOpacity(0.7) : AppColors.neutralDark.withOpacity(0.7),
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (controller.updateAvailable.value)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.small,
                          vertical: 3,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.warning.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
                        ),
                        child: Text(
                          'Atualização disponível',
                          style: AppTypography.textTheme.labelSmall?.copyWith(
                            color: AppColors.warning,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
              
              // Iniciar automaticamente
              SettingsSwitchTile(
                title: 'Iniciar automaticamente',
                subtitle: 'Iniciar o backend Python automaticamente ao abrir o aplicativo',
                value: controller.settings.value.autoStartBackend,
                onChanged: (value) => controller.updateSetting(autoStartBackend: value),
              ),
              
              // Reiniciar backend
              Obx(() => SettingsButtonTile(
                title: 'Reiniciar backend',
                subtitle: 'Reinicia o servidor Python',
                onPressed: controller.isRestartingBackend.value 
                    ? null 
                    : controller.restartBackend,
                icon: Icons.refresh_outlined,
                isLoading: controller.isRestartingBackend.value,
              )),
              
              // Atualizar backend (apenas se houver atualizações)
              if (controller.updateAvailable.value)
                SettingsButtonTile(
                  title: 'Atualizar backend',
                  subtitle: 'Atualiza o backend para a versão mais recente',
                  onPressed: controller.updateBackend,
                  icon: Icons.system_update_outlined,
                ),
            ],
          ),
          
          const SizedBox(height: AppSpacing.medium),
          
          // Seção: Recursos computacionais
          SettingsSection(
            title: 'Recursos computacionais',
            children: [
              // Processamento em segundo plano
              SettingsSwitchTile(
                title: 'Processamento em segundo plano',
                subtitle: 'Permite que tarefas de processamento rodem em threads separadas',
                value: controller.settings.value.backgroundProcessing,
                onChanged: (value) => controller.updateSetting(backgroundProcessing: value),
                icon: Icons.memory_outlined,
              ),
            ],
          ),
          
          const SizedBox(height: AppSpacing.medium),
          
          // Seção: Backup e armazenamento
          SettingsSection(
            title: 'Backup e armazenamento',
            children: [
              // Backup automático
              SettingsSwitchTile(
                title: 'Backup automático',
                subtitle: 'Criar cópias de segurança automáticas dos projetos',
                value: controller.settings.value.backupEnabled,
                onChanged: (value) => controller.updateSetting(backupEnabled: value),
                icon: Icons.backup_outlined,
              ),
              
              // Intervalo de auto-save
              _buildAutoSaveSelector(),
            ],
          ),
        ],
      ),
    );
  }
  
  // Constrói a aba de configurações avançadas
  Widget _buildAdvancedTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.medium),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Seção: Ajustes de imagem
          SettingsSection(
            title: 'Ajustes de imagem',
            children: [
              // Brilho
              _buildSliderSetting(
                title: 'Brilho',
                subtitle: 'Ajuste de brilho padrão para imagens',
                value: controller.settings.value.adjustBrightness,
                min: -1.0,
                max: 1.0,
                divisions: 20,
                onChanged: (value) => controller.updateSetting(adjustBrightness: value),
              ),
              
              // Contraste
              _buildSliderSetting(
                title: 'Contraste',
                subtitle: 'Ajuste de contraste padrão para imagens',
                value: controller.settings.value.adjustContrast,
                min: -1.0,
                max: 1.0,
                divisions: 20,
                onChanged: (value) => controller.updateSetting(adjustContrast: value),
              ),
              
              // Saturação
              _buildSliderSetting(
                title: 'Saturação',
                subtitle: 'Ajuste de saturação padrão para imagens',
                value: controller.settings.value.adjustSaturation,
                min: -1.0,
                max: 1.0,
                divisions: 20,
                onChanged: (value) => controller.updateSetting(adjustSaturation: value),
              ),
              
              // Nitidez
              _buildSliderSetting(
                title: 'Nitidez',
                subtitle: 'Ajuste de nitidez padrão para imagens',
                value: controller.settings.value.adjustSharpness,
                min: 0.0,
                max: 1.0,
                divisions: 10,
                onChanged: (value) => controller.updateSetting(adjustSharpness: value),
              ),
              
              // Normalização de imagens
              SettingsSwitchTile(
                title: 'Normalizar imagens',
                subtitle: 'Normaliza as imagens antes do processamento',
                value: controller.settings.value.normalizeImages,
                onChanged: (value) => controller.updateSetting(normalizeImages: value),
                icon: Icons.auto_fix_high_outlined,
              ),
            ],
          ),
          
          const SizedBox(height: AppSpacing.medium),
          
          // Seção: Logs e diagnósticos
          SettingsSection(
            title: 'Logs e diagnósticos',
            children: [
              // Logs principal
              SettingsSwitchTile(
                title: 'Habilitar logs',
                subtitle: 'Registra operações e erros para diagnósticos',
                value: controller.settings.value.enableLogging,
                onChanged: (value) => controller.updateSetting(enableLogging: value),
                icon: Icons.history_outlined,
              ),
              
              // Persistência de logs
              SettingsSwitchTile(
                title: 'Persistir logs em arquivo',
                subtitle: 'Salva logs em arquivo para análise posterior',
                value: controller.settings.value.enableLogPersistence,
                onChanged: (value) => controller.updateSetting(enableLogPersistence: value),
                icon: Icons.save_outlined,
              ),
              
              // Exportar logs (apenas se persistência estiver ativada)
              if (controller.settings.value.enableLogPersistence)
                SettingsButtonTile(
                  title: 'Exportar logs',
                  subtitle: 'Exporta logs para análise em arquivo de texto',
                  onPressed: controller.exportLogFile,
                  icon: Icons.upload_file_outlined,
                  isLoading: controller.isLoading.value,
                ),
              
              // Limpar logs (apenas se persistência estiver ativada)
              if (controller.settings.value.enableLogPersistence)
                SettingsButtonTile(
                  title: 'Limpar logs',
                  subtitle: 'Remove todos os logs persistidos',
                  onPressed: controller.clearLogFiles,
                  icon: Icons.delete_outline,
                  isLoading: controller.isLoading.value,
                  isDestructive: true,
                ),
              
              // Debug
              SettingsSwitchTile(
                title: 'Modo de depuração',
                subtitle: 'Habilita logs detalhados e ferramentas de depuração',
                value: controller.settings.value.enableDebugMode,
                onChanged: (value) => controller.updateSetting(enableDebugMode: value),
                icon: Icons.bug_report_outlined,
              ),
            ],
          ),
          
          const SizedBox(height: AppSpacing.medium),
          
          // Seção: Configurações avançadas
          SettingsSection(
            title: 'Configurações avançadas',
            children: [
              // Diretório de dados
              SettingsButtonTile(
                title: 'Diretório de dados',
                subtitle: controller.settings.value.dataDirectory.isNotEmpty
                    ? controller.settings.value.dataDirectory
                    : 'Diretório padrão',
                onPressed: () => controller.selectDirectory('dataDirectory'),
                icon: Icons.storage_outlined,
              ),
              
              // Caminho do Python
              SettingsButtonTile(
                title: 'Caminho do Python',
                subtitle: controller.settings.value.pythonPath.isNotEmpty
                    ? controller.settings.value.pythonPath
                    : 'Python padrão do sistema',
                onPressed: controller.selectPythonPath,
                icon: Icons.code_outlined,
              ),
            ],
          ),
        ],
      ),
    );
  }
  
  // Construir seletor de tema
  Widget _buildThemeSelector() {
    final String currentTheme = controller.settings.value.themeMode;
    
    return Container(
      padding: const EdgeInsets.symmetric(
        vertical: AppSpacing.small,
        horizontal: AppSpacing.medium,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.palette_outlined,
                color: AppColors.primary,
                size: 24,
              ),
              const SizedBox(width: AppSpacing.small),
              Text(
                'Tema',
                style: AppTypography.textTheme.bodyLarge?.copyWith(
                  color: Get.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 4),
          
          Text(
            'Selecione o tema da aplicação',
            style: AppTypography.textTheme.bodySmall?.copyWith(
              color: Get.isDarkMode 
                  ? AppColors.neutralLight.withOpacity(0.7) 
                  : AppColors.neutralDark.withOpacity(0.7),
            ),
          ),
          
          const SizedBox(height: AppSpacing.small),
          
          // Botões de seleção de tema
          Row(
            children: [
              // Botão tema claro
              Expanded(
                child: _buildThemeButton(
                  title: 'Claro',
                  icon: Icons.light_mode_outlined,
                  isSelected: currentTheme == 'light',
                  onTap: () {
                    controller.changeThemeMode(ThemeMode.light);
                  },
                ),
              ),
              
              const SizedBox(width: AppSpacing.xSmall),
              
              // Botão tema escuro
              Expanded(
                child: _buildThemeButton(
                  title: 'Escuro',
                  icon: Icons.dark_mode_outlined,
                  isSelected: currentTheme == 'dark',
                  onTap: () {
                    controller.changeThemeMode(ThemeMode.dark);
                  },
                ),
              ),
              
              const SizedBox(width: AppSpacing.xSmall),
              
              // Botão tema sistema
              Expanded(
                child: _buildThemeButton(
                  title: 'Sistema',
                  icon: Icons.settings_outlined,
                  isSelected: currentTheme == 'system',
                  onTap: () {
                    controller.changeThemeMode(ThemeMode.system);
                  },
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
  
  // Botão de seleção de tema
  Widget _buildThemeButton({
    required String title,
    required IconData icon,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
      child: Container(
        padding: const EdgeInsets.symmetric(
          vertical: AppSpacing.small,
          horizontal: AppSpacing.xSmall,
        ),
        decoration: BoxDecoration(
          color: isSelected 
              ? AppColors.primary.withOpacity(0.1) 
              : Colors.transparent,
          border: Border.all(
            color: isSelected 
                ? AppColors.primary 
                : Get.isDarkMode 
                    ? AppColors.neutralLight.withOpacity(0.3)
                    : AppColors.neutralLight,
            width: 1,
          ),
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected 
                  ? AppColors.primary 
                  : Get.isDarkMode 
                      ? AppColors.neutralLight
                      : AppColors.neutralDark,
              size: 20,
            ),
            const SizedBox(height: 4),
            Text(
              title,
              style: AppTypography.textTheme.labelSmall?.copyWith(
                color: isSelected 
                    ? AppColors.primary 
                    : Get.isDarkMode 
                        ? AppColors.neutralLight
                        : AppColors.neutralDark,
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  // Seletor de idioma
  Widget _buildLanguageSelector() {
    final String currentLanguage = controller.settings.value.language;
    final Map<String, String> languages = {
      'pt': 'Português',
      'en': 'English',
      'es': 'Español',
    };
    
    return Container(
      padding: const EdgeInsets.symmetric(
        vertical: AppSpacing.small,
        horizontal: AppSpacing.medium,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.language_outlined,
                color: AppColors.primary,
                size: 24,
              ),
              const SizedBox(width: AppSpacing.small),
              Text(
                'Idioma',
                style: AppTypography.textTheme.bodyLarge?.copyWith(
                  color: Get.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 4),
          
          Text(
            'Selecione o idioma da interface',
            style: AppTypography.textTheme.bodySmall?.copyWith(
              color: Get.isDarkMode 
                  ? AppColors.neutralLight.withOpacity(0.7) 
                  : AppColors.neutralDark.withOpacity(0.7),
            ),
          ),
          
          const SizedBox(height: AppSpacing.small),
          
          // Dropdown de idiomas
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.small,
            ),
            decoration: BoxDecoration(
              color: Get.isDarkMode 
                  ? AppColors.surfaceDark.withOpacity(0.3)
                  : AppColors.neutralLightest,
              borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
              border: Border.all(
                color: Get.isDarkMode 
                    ? AppColors.neutralLight.withOpacity(0.1)
                    : AppColors.neutralLight,
                width: 1,
              ),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: currentLanguage,
                isExpanded: true,
                icon: Icon(
                  Icons.arrow_drop_down,
                  color: Get.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                ),
                dropdownColor: Get.isDarkMode 
                    ? AppColors.surfaceDark 
                    : AppColors.white,
                items: languages.entries.map((entry) {
                  return DropdownMenuItem<String>(
                    value: entry.key,
                    child: Text(
                      entry.value,
                      style: AppTypography.textTheme.bodyMedium?.copyWith(
                        color: Get.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                      ),
                    ),
                  );
                }).toList(),
                onChanged: (value) {
                  if (value != null) {
                    controller.updateSetting(language: value);
                  }
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  // Configuração do intervalo de auto-save
  Widget _buildAutoSaveSelector() {
    final Map<int, String> intervals = {
      60: '1 minuto',
      300: '5 minutos',
      600: '10 minutos',
      1800: '30 minutos',
      3600: '1 hora',
      0: 'Desativado',
    };
    
    final int currentInterval = controller.settings.value.autoSaveInterval;
    final String currentValue = intervals[currentInterval] ?? '${currentInterval} segundos';
    
    return Container(
      padding: const EdgeInsets.symmetric(
        vertical: AppSpacing.small,
        horizontal: AppSpacing.medium,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.timer_outlined,
                color: AppColors.primary,
                size: 24,
              ),
              const SizedBox(width: AppSpacing.small),
              Text(
                'Intervalo de salvamento automático',
                style: AppTypography.textTheme.bodyLarge?.copyWith(
                  color: Get.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 4),
          
          Text(
            'Define o intervalo para salvar automaticamente alterações',
            style: AppTypography.textTheme.bodySmall?.copyWith(
              color: Get.isDarkMode 
                  ? AppColors.neutralLight.withOpacity(0.7) 
                  : AppColors.neutralDark.withOpacity(0.7),
            ),
          ),
          
          const SizedBox(height: AppSpacing.small),
          
          // Dropdown de intervalos
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.small,
            ),
            decoration: BoxDecoration(
              color: Get.isDarkMode 
                  ? AppColors.surfaceDark.withOpacity(0.3)
                  : AppColors.neutralLightest,
              borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
              border: Border.all(
                color: Get.isDarkMode 
                    ? AppColors.neutralLight.withOpacity(0.1)
                    : AppColors.neutralLight,
                width: 1,
              ),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<int>(
                value: intervals.containsKey(currentInterval) ? currentInterval : 300,
                isExpanded: true,
                icon: Icon(
                  Icons.arrow_drop_down,
                  color: Get.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                ),
                dropdownColor: Get.isDarkMode 
                    ? AppColors.surfaceDark 
                    : AppColors.white,
                items: intervals.entries.map((entry) {
                  return DropdownMenuItem<int>(
                    value: entry.key,
                    child: Text(
                      entry.value,
                      style: AppTypography.textTheme.bodyMedium?.copyWith(
                        color: Get.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                      ),
                    ),
                  );
                }).toList(),
                onChanged: (value) {
                  if (value != null) {
                    controller.updateSetting(autoSaveInterval: value);
                  }
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  // Widget para configuração com slider
  Widget _buildSliderSetting({
    required String title,
    required String subtitle,
    required double value,
    required double min,
    required double max,
    required int divisions,
    required ValueChanged<double> onChanged,
  }) {
    // Formatar o valor para exibição
    String valueLabel;
    if (value == 0.0) {
      valueLabel = 'Padrão';
    } else if (value > 0.0) {
      valueLabel = '+${(value * 100).round()}%';
    } else {
      valueLabel = '${(value * 100).round()}%';
    }
    
    return Container(
      padding: const EdgeInsets.symmetric(
        vertical: AppSpacing.small,
        horizontal: AppSpacing.medium,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                title,
                style: AppTypography.textTheme.bodyLarge?.copyWith(
                  color: Get.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.small,
                  vertical: 2,
                ),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
                ),
                child: Text(
                  valueLabel,
                  style: AppTypography.textTheme.labelSmall?.copyWith(
                    color: AppColors.primary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 4),
          
          Text(
            subtitle,
            style: AppTypography.textTheme.bodySmall?.copyWith(
              color: Get.isDarkMode 
                  ? AppColors.neutralLight.withOpacity(0.7) 
                  : AppColors.neutralDark.withOpacity(0.7),
            ),
          ),
          
          const SizedBox(height: AppSpacing.xSmall),
          
          // Slider
          Slider(
            value: value,
            min: min,
            max: max,
            divisions: divisions,
            activeColor: AppColors.primary,
            inactiveColor: Get.isDarkMode 
                ? AppColors.neutralLight.withOpacity(0.3)
                : AppColors.neutralLight,
            onChanged: onChanged,
          ),
          
          // Legenda dos valores
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                min.toString(),
                style: AppTypography.textTheme.labelSmall?.copyWith(
                  color: Get.isDarkMode 
                      ? AppColors.neutralLight.withOpacity(0.5)
                      : AppColors.neutralDark.withOpacity(0.5),
                ),
              ),
              Text(
                max.toString(),
                style: AppTypography.textTheme.labelSmall?.copyWith(
                  color: Get.isDarkMode 
                      ? AppColors.neutralLight.withOpacity(0.5)
                      : AppColors.neutralDark.withOpacity(0.5),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
