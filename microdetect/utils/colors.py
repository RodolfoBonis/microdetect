try:
    from colorama import Fore, Style, init

    # Inicializar colorama (necessário para Windows)
    init(autoreset=True)
    # Definir cores e estilos
    INFO = Fore.CYAN
    SUCCESS = Fore.GREEN
    WARNING = Fore.YELLOW
    ERROR = Fore.RED
    BRIGHT = Style.BRIGHT
    RESET = Style.RESET_ALL
    COLORS_AVAILABLE = True
except ImportError:
    # Fallback se colorama não estiver disponível
    INFO = WARNING = SUCCESS = ERROR = BRIGHT = RESET = ""
    COLORS_AVAILABLE = False
    Fore = type('Fore', (), {'GREEN': '', 'YELLOW': '', 'RED': '', 'CYAN': ''})
    Style = type('Style', (), {'BRIGHT': '', 'RESET_ALL': ''})
