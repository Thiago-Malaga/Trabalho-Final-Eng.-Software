from abc import ABC, abstractmethod  # necessário para criar a interface do Strategy

from controle_dados import ControleDados
from servicos_filtro import FiltroTextoIgual

import pandas as pd


class AnalisePeriodoStrategy(ABC):
    """Strategy (interface): toda estratégia de período tem que ter o método aplicar(df)."""

    # Aqui só define *O QUE* uma etapa da análise faz (recebe a tabela e devolve uma tabela).
    # COMO cada etapa transforma os dados fica por conta de cada classe filha.
    @abstractmethod
    def aplicar(self, df):
        pass


class CalcularDiaSemanaStrategy(AnalisePeriodoStrategy):
    """Estratégia: calcula o dia da semana a partir da coluna Data."""

    DIAS = [
        "segunda-feira",
        "ter\u00e7a-feira",
        "quarta-feira",
        "quinta-feira",
        "sexta-feira",
        "s\u00e1bado",
        "domingo",
    ]

    def aplicar(self, df):
        datas = pd.to_datetime(df["Data"], dayfirst=True)
        resultado = df.copy()
        resultado["Dia da Semana"] = datas.dt.dayofweek.map(
            lambda dia: CalcularDiaSemanaStrategy.DIAS[dia]
        )
        return resultado


class CalcularFaixaHorariaStrategy(AnalisePeriodoStrategy):
    """Estratégia: calcula a faixa horária a partir da coluna Horário."""

    @staticmethod
    def faixa_horaria(hora):
        if hora < 6:
            return "Madrugada"
        if hora < 12:
            return "Manhã"
        if hora < 18:
            return "Tarde"
        return "Noite"

    def aplicar(self, df):
        horas = df["Horário"].str.split(":").str[0].astype(int)
        resultado = df.copy()
        resultado["Faixa Horária"] = horas.map(
            CalcularFaixaHorariaStrategy.faixa_horaria
        )
        return resultado


class AgruparPeriodosStrategy(AnalisePeriodoStrategy):
    """Estratégia: agrupa as ocorrências por dia da semana e faixa horária."""

    def aplicar(self, df):
        resultado = df.groupby(["Dia da Semana", "Faixa Horária"]).size()
        resultado = resultado.reset_index(name="Quantidade")
        return resultado.sort_values("Quantidade", ascending=False)


class ServicosPeriodos:
    """Context: é quem USA as estratégias para montar a análise de períodos."""

    DIAS = CalcularDiaSemanaStrategy.DIAS

    @staticmethod
    def faixa_horaria(hora):
        """Mantém disponível o cálculo antigo de faixa horária."""
        return CalcularFaixaHorariaStrategy.faixa_horaria(hora)

    @staticmethod
    def analisar_regiao(dados, cidade, bairro):
        dados = ControleDados._normalizar_dados(dados)

        # A cidade e o bairro usam o filtro de texto que já existe em ServicosFiltro.
        # Assim não repetimos a lógica de normalização e comparação.
        filtros_regiao = [
            FiltroTextoIgual("Cidade", cidade),
            FiltroTextoIgual("Bairro", bairro),
        ]

        resultado = dados
        for filtro in filtros_regiao:
            resultado = filtro.aplicar(resultado)

        if resultado.empty:
            raise ValueError("Não há ocorrências registradas para o bairro escolhido.")

        # O restante da análise também fica dividido em etapas que aplicam sobre o resultado anterior.
        estrategias = [
            CalcularDiaSemanaStrategy(),
            CalcularFaixaHorariaStrategy(),
            AgruparPeriodosStrategy(),
        ]

        for estrategia in estrategias:
            # Toda estratégia tem o método aplicar(), mas cada uma faz uma etapa diferente.
            # Se surgir uma nova etapa na análise, este método não precisa mudar.
            resultado = estrategia.aplicar(resultado)

        return resultado