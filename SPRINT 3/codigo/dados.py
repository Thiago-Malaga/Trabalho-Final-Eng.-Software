import pandas as pd


class Dados:
    """Armazena os registros criminais em um DataFrame."""

    def __init__(self):
        self._dados = pd.DataFrame()

    def definir_dados(self, dados: pd.DataFrame) -> None:
        """Substitui os dados armazenados por uma cópia do DataFrame recebido."""
        self._dados = dados.copy()

    def obter_dados(self) -> pd.DataFrame:
        """Retorna uma cópia dos dados para evitar alterações externas acidentais."""
        return self._dados.copy()

    def possui_dados(self) -> bool:
        return not self._dados.empty
