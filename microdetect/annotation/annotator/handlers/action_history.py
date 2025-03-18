"""
Gerenciamento do histórico de ações para suportar operações de desfazer.
"""


class ActionHistory:
    """
    Classe para gerenciar o histórico de ações, permitindo desfazer operações.
    """

    def __init__(self, max_history=50):
        """
        Inicializa o histórico de ações.

        Args:
            max_history: Número máximo de ações a serem armazenadas no histórico
        """
        self.history = []
        self.max_history = max_history

    def add(self, action_type, data):
        """
        Adiciona uma ação ao histórico.

        Args:
            action_type: Tipo da ação ('add', 'move', 'resize', 'delete')
            data: Dados específicos da ação
        """
        self.history.append({"type": action_type, "data": data})

        # Limitar tamanho do histórico
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def undo(self):
        """
        Remove e retorna a última ação do histórico.

        Returns:
            Dict com informações da última ação ou None se o histórico estiver vazio
        """
        if not self.history:
            return None

        return self.history.pop()

    def clear(self):
        """Limpa todo o histórico de ações."""
        self.history.clear()

    def is_empty(self):
        """
        Verifica se o histórico está vazio.

        Returns:
            True se o histórico estiver vazio, False caso contrário
        """
        return len(self.history) == 0
