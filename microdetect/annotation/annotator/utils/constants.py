"""
Constantes utilizadas no módulo de anotação.
"""

# Configurações padrão
DEFAULT_AUTO_SAVE = True
DEFAULT_AUTO_SAVE_INTERVAL = 20  # segundos

# Constantes para alças de redimensionamento
HANDLE_NONE = 0
HANDLE_NW = 1  # Noroeste
HANDLE_NE = 2  # Nordeste
HANDLE_SE = 3  # Sudeste
HANDLE_SW = 4  # Sudoeste
HANDLE_N = 5  # Norte
HANDLE_E = 6  # Leste
HANDLE_S = 7  # Sul
HANDLE_W = 8  # Oeste

# Atalhos de teclado para anotação
KEYBOARD_SHORTCUTS = {
    "a": "Imagem anterior",
    "d": "Próxima imagem",
    "p": "Ativar/desativar modo navegação",
    "r": "Reiniciar zoom e pan",
    "0-9": "Alternar visibilidade da classe",
    "s": "Salvar anotações",
    "S": "Mostrar estatísticas",
    "b": "Buscar imagens",
    "q": "Sair",
    "e": "Alternar modo de edição",
    "z": "Desfazer última ação",
    "x": "Salvar e sair",
    "n": "Salvar e próxima imagem",
    "i": "Abrir diálogo de exportação/importação",
    "g": "Ativar/desativar sugestões automáticas",
    "f": "Aplicar sugestões automáticas",
}
