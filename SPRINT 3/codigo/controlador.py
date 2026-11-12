from dados import Dados
from controle_dados import ControleDados


class Controlador:
    """Coordena as operações entre o Terminal e as classes de dados."""

    def __init__(self):
        self.dados = Dados()
        self.controle_dados = ControleDados(self.dados)

    def importar_dados(self, caminho: str):
        return self.controle_dados.carregar_dados(caminho)

    def imprimir_dados(self) -> None:
        self.controle_dados.imprimir_todos_dados()

    def obter_dados(self):
        return self.controle_dados.obter_dados()
