from abc import ABC, abstractmethod  # necessário para criar a interface do Strategy

from servicos_filtro import FiltroTextoIgual


class RankingStrategy(ABC):
    """Strategy (interface): toda estratégia do ranking tem que ter o método aplicar(df)."""

    # Aqui só define *O QUE* uma etapa do ranking faz (recebe a tabela e devolve uma tabela).
    # COMO cada etapa transforma os dados fica por conta de cada classe filha.
    @abstractmethod
    def aplicar(self, df):
        pass


class AgruparPorAISPStrategy(RankingStrategy):
    """Estratégia: conta o total de ocorrências de cada AISP."""

    def aplicar(self, df):
        # Agrupa as ocorrências por AISP e cria a coluna Total com a quantidade de cada grupo.
        return df.groupby("AISP").size().reset_index(name="Total")


class OrdenarRankingStrategy(RankingStrategy):
    """Estratégia: ordena o ranking do maior para o menor total de ocorrências."""

    def aplicar(self, df):
        # Depende da coluna Total, que é criada pela estratégia de agrupamento.
        return df.sort_values("Total", ascending=False).reset_index(drop=True)


class ServicosRanking:
    """é quem USA as estratégias para montar o ranking de AISPs."""

    @staticmethod
    def gerar_ranking_aisp(dados, tipo_crime=None):
        # O filtro por tipo de crime usa o filtro de texto do  servicos_filtro.
        if tipo_crime is not None:
            dados = FiltroTextoIgual("Tipo do crime", tipo_crime).aplicar(dados)

        # apenas interrompe o ranking quando não há ocorrências para contar.
        if dados.empty:
            raise ValueError("Não há ocorrências registradas para o tipo de crime escolhido.")

        estrategias = [
            AgruparPorAISPStrategy(),
            OrdenarRankingStrategy(),
        ]

        resultado = dados
        for estrategia in estrategias:

            # Se surgir uma nova etapa no ranking, este método não precisa mudar.
            resultado = estrategia.aplicar(resultado)

        return resultado