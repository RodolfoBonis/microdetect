def get_logo_ascii(custom_text=""):
    """
    Retorna a representação ASCII/Unicode da logo MicroDetect."

    Args:
        custom_text: Texto personalizado para exibir ao lado da logo.
    """
    # Cores ANSI (se o terminal suportar)
    cyan = "\033[96m"
    blue = "\033[94m"
    reset = "\033[0m"
    bold = "\033[1m"

    logo = f"""
{cyan}           ╭────────────────────╮           
      ╭────┤                    ├────╮      
    ╭─┤    │  ╭──────────────╮  │    ├─╮    
    │ │    │  │              │  │    │ │    
    │ │    │  │  ╭────────╮  │  │    │ │    
    │ │    │  │  │        │  │  │    │ │    
    │ │    │  │  │  ╭──╮  │  │  │    │ │    
    │ │    │  │  │  │  │  │  │  │    │ │    
    │ │    │  │  │  ╰──╯  │  │  │    │ │    
    │ │    │  │  ╰────────╯  │  │    │ │    
    │ │    │  │              │  │    │ │    
    │ │    │  ╰──────────────╯  │    │ │    
    ╰─┤    │                    │    ├─╯    
      ╰────┤     {bold}MicroDetect{reset}{cyan}  {custom_text}    
           ╰────────────────────╯           
{reset}"""

    # Versão sem cores para terminais que não suportam cores ANSI
    plain_logo = """
           ╭────────────────────╮           
      ╭────┤                    ├────╮      
    ╭─┤    │  ╭──────────────╮  │    ├─╮    
    │ │    │  │              │  │    │ │    
    │ │    │  │  ╭────────╮  │  │    │ │    
    │ │    │  │  │        │  │  │    │ │    
    │ │    │  │  │  ╭──╮  │  │  │    │ │    
    │ │    │  │  │  │  │  │  │  │    │ │    
    │ │    │  │  │  ╰──╯  │  │  │    │ │    
    │ │    │  │  ╰────────╯  │  │    │ │    
    │ │    │  │              │  │    │ │    
    │ │    │  ╰──────────────╯  │    │ │    
    ╰─┤    │                    │    ├─╯    
      ╰────┤     MicroDetect custom_text}  
           ╰────────────────────╯           
"""

    # Use a versão colorida por padrão, mas tente detectar se o terminal suporta cores
    try:
        import os
        import sys

        if "NO_COLOR" in os.environ or not sys.stdout.isatty():
            return plain_logo
    except:
        pass

    return logo


def get_simple_logo_ascii(use_color=True, custom_text=""):
    """
    Retorna a representação ASCII da logo MicroDetect.

    Args:
        use_color: Se True, retorna a versão colorida (se o terminal suportar).
                   Se False, retorna a versão sem cor.
        custom_text: Texto personalizado para exibir ao lado da logo.
    """
    # Versão sem cor (compatível com todos os terminais)
    plain_logo = rf"""
 __  __ _                 _____       _            _   
|  \/  (_)               |  __ \     | |          | |  
| \  / |_  ___ _ __ ___  | |  | | ___| |_ ___  ___| |_ 
| |\/| | |/ __| '__/ _ \ | |  | |/ _ \ __/ _ \/ __| __|
| |  | | | (__| | | (_) || |__| |  __/ ||  __/ (__| |_ 
|_|  |_|_|\___|_|  \___/ |_____/ \___|\__\___|\___|\__| {custom_text}

    """

    if not use_color:
        return plain_logo

    # Códigos de cor ANSI
    cyan = "\033[96m"  # Ciano claro
    blue = "\033[94m"  # Azul
    reset = "\033[0m"  # Reset para cores padrão
    bold = "\033[1m"  # Texto em negrito

    # Versão colorida
    colored_logo = f"""
{cyan} __  __ {blue}_{cyan}                 {blue}_____ {cyan}      {blue}_ {cyan}           {blue}_ {cyan}  
{cyan}|  \\/  |{blue}(_){cyan}               {blue}|  __ \\ {cyan}    {blue}| |{cyan}          {blue}| |{cyan}  
{cyan}| \\  / |{blue}_ {cyan} ___ {blue}_ __ ___ {cyan} {blue}| |  | |{cyan} ___| |_ ___  ___| |_ 
{cyan}| |\\/| |{blue}| |{cyan}/ __| '__/ _ \\ {blue}| |  | |{cyan}/ _ \\ __/ _ \\/ __| __|
{cyan}| |  | |{blue}| |{cyan}| (__| | | (_) |{blue}| |__| |{cyan}  __/ ||  __/ (__| |_ 
{cyan}|_|  |_|{blue}|_|{cyan}\\___||_|  \\___/ {blue}|_____/ {cyan}\\___|\\_\\_\\___|\\___|\\___|   {custom_text}

{reset}"""

    return colored_logo


def get_logo_with_name_ascii(use_color=True, custom_text=""):
    """
    Retorna a representação ASCII da logo do MicroDetect com o nome ao lado, com alinhamento adequado.

    Args:
        use_color: Se True, retorna a versão colorida (se o terminal suportar).
        custom_text: Texto personalizado para exibir ao lado da logo.
    """
    # Versão sem cor
    plain_logo = rf"""
       ╭────────╮    __  __ _                 _____       _            _   
      ╭┤        ├╮  |  \\/  (_)               |  __ \\     | |          | |  
     ╭┤│ ╭────╮ │├╮ | \\  / |_  ___ _ __ ___  | |  | | ___| |_ ___  ___| |_ 
     │││ │╭──╮│ │││ | |\\/| | |/ __| '__/ _ \\ | |  | |/ _ \\ __/ _ \\/ __| __|
     │││ │└──┘│ │││ | |  | | | (__| | | (_) || |__| |  __/ ||  __/ (__| |_ 
     ╰┤│ ╰────╯ │├╯ |_|  |_|_|\\___||_|  \\___/ |_____/ \\___|\\_\\_\\___|\\___|\\__|
      ╰┤        ├╯  
       ╰────────╯   Detecção e classificação de microorganismos {custom_text}
    """

    if not use_color:
        return plain_logo

    # Códigos de cor ANSI
    cyan = "\033[96m"  # Ciano claro (para a logo)
    blue = "\033[94m"  # Azul (para parte do texto)
    reset = "\033[0m"  # Reset cores
    bold = "\033[1m"  # Negrito

    # Versão colorida
    colored_logo = f"""
    {cyan}   ╭────────╮    {blue}__  __ {cyan}_{blue}                 {cyan}_____       {blue}_ {cyan}           {blue}_ {cyan}  
    {cyan}  ╭┤        ├╮  {blue}|  \\/  |{cyan}({blue}_{cyan})               {blue}|  __ \\ {cyan}    {blue}| |{cyan}          {blue}| |{cyan}  
    {cyan} ╭┤│ {blue}╭────╮{cyan} │├╮ {blue}| \\  / |{cyan}_{blue} {cyan} ___ {blue}_ __ ___ {cyan} {blue}| |  | |{cyan} ___| |_ ___  ___| |_ 
    {cyan} │││ {blue}│{cyan}╭──╮{blue}│{cyan} │││ {blue}| |\\/| | |{cyan}/ __| '__/ _ \\ {blue}| |  | |{cyan}/ _ \\ __/ _ \\/ __| __|
    {cyan} │││ {blue}│{cyan}└──┘{blue}│{cyan} │││ {blue}| |  | | |{cyan}| (__| | | (_) |{blue}| |__| |{cyan}  __/ ||  __/ (__| |_ 
    {cyan} ╰┤│ {blue}╰────╯{cyan} │├╯ {blue}|_|  |_|_|{cyan}\\___||_|  \\___/ {blue}|_____/ {cyan}\\___|\\_\\_\\___|\\___|\\__|     {custom_text}
    {cyan}  ╰┤        ├╯  {reset}
    {cyan}   ╰────────╯   {bold}Detecção e classificação de microorganismos{reset} 
    """

    return colored_logo
