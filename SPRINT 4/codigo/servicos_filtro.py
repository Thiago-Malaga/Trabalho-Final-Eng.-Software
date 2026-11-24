from abc import ABC, abstractmethod  # necessário para criar a interface do Strategy

from controle_dados import ControleDados
from servicos_periodos import ServicosPeriodos


class FiltroStrategy(ABC):
    """Strategy (interface): todo filtro tem que ter o método aplicar(df)."""

    # Aqui só define *O QUE* um filtro faz (recebe a tabela e devolve ela filtrada).
    # COMO filtra fica por conta de cada classe filha.
    @abstractmethod
    def aplicar(self, df):
        pass


class FiltroDataInicio(FiltroStrategy):
    """Estratégia: mantém as ocorrências a partir de uma data."""

    def __init__(self, data_inicio):
        # Guardo a data dentro do próprio filtro assim o aplicar() só precisa receber a tabela, e todos os filtros ficam com o mesmo formato.
        self.data_inicio = data_inicio

    def aplicar(self, df):
        # Era o antigo `if data_inicio is not None`, só que agora está separado numa classe própria.
        return df[df["Data"] >= self.data_inicio]


class FiltroDataFim(FiltroStrategy):
    """Estratégia: mantém as ocorrências até uma data."""

    def __init__(self, data_fim):
        self.data_fim = data_fim

    def aplicar(self, df):
        return df[df["Data"] <= self.data_fim]


class FiltroTextoIgual(FiltroStrategy):
    """Estratégia: mantém as ocorrências em que a coluna é igual a um texto."""

    def __init__(self, coluna, valor):
        # O código antigo de cidade e de tipo de crime era igual, só mudava a coluna então a coluna virou parâmetro: com uma classe só eu posso usar o filtro qualquer coluna de texto (Cidade, Tipo do crime, Bairro...).
        self.coluna = coluna

        # Normalizo o texto já na criação do filtro, pra não repetir isso toda vez que o filtro for aplicado.
        self.valor = ControleDados._normalizar_texto(valor)

    def aplicar(self, df):
        # Mesma lógica de antes: normaliza a coluna inteira e compara com o valor que já está normalizado.
        return df[
            df[self.coluna].map(ControleDados._normalizar_texto) == self.valor
        ]


class ServicosFiltro:
    """Context: é quem USA os filtros (as estratégias)."""

    @staticmethod
    def filtrar_ocorrencias(dados, filtros):
        resultado = ControleDados._normalizar_dados(dados)

        # Antes tinha um `if` pra cada critério (data, cidade, crime). Agora esse método não sabe quais filtros existem: ele só recebe uma lista de filtros e manda cada um se aplicar, um depois do outro.
        for filtro in filtros:
            # Todo filtro tem o método aplicar(), mas cada um faz do seu jeito. Se eu criar um filtro novo, este método não precisa mudar.
            resultado = filtro.aplicar(resultado)

        return resultado[ControleDados.COLUNAS_TESTE]