from typing import Optional

import pandas as pd

from controle_dados import ControleDados
from dados import Dados
from servicos_filtro import ServicosFiltro
from servicos_periodos import ServicosPeriodos
from servicos_ranking import ServicosRanking


class Controlador:
    """Facade que centraliza e coordena as operações entre a interface e os subsistemas."""

    def __init__(self):
        self.dados = Dados()
        self.controle_dados = ControleDados(self.dados)

    def _obter_base_dados(self, dados: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        if dados is not None:
            return dados
        base = self.controle_dados.obter_dados()
        if base.empty:
            raise ValueError("Nenhum dado carregado. Importe um arquivo TSV antes de continuar.")
        return base

    def importar_dados(self, caminho: str) -> pd.DataFrame:
        return self.controle_dados.carregar_dados(caminho)

    def carregar_tsv(self, caminho: str) -> pd.DataFrame:
        dados = self.controle_dados.carregar_dados(caminho)
        return ControleDados._normalizar_dados(dados)[ControleDados.COLUNAS_TESTE]

    def possui_dados(self) -> bool:
        return self.controle_dados.verificar_dados()

    def imprimir_dados(self) -> None:
        self.controle_dados.imprimir_todos_dados()

    def obter_dados(self) -> pd.DataFrame:
        return self.controle_dados.obter_dados()

    def filtrar_ocorrencias(
        self,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        cidade: Optional[str] = None,
        tipo_crime: Optional[str] = None,
        dados: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        base = self._obter_base_dados(dados)
        return ServicosFiltro.filtrar_ocorrencias(
            base,
            data_inicio=data_inicio,
            data_fim=data_fim,
            cidade=cidade,
            tipo_crime=tipo_crime,
        )

    def gerar_ranking_aisp(
        self,
        tipo_crime: Optional[str] = None,
        dados: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        base = self._obter_base_dados(dados)
        dados_normalizados = ServicosFiltro.filtrar_ocorrencias(base)

        crime_filtro = None
        if tipo_crime:
            tipos = dados_normalizados["Tipo do crime"]
            correspondencia = tipos[
                tipos.str.casefold() == tipo_crime.strip().casefold()
            ]
            if correspondencia.empty:
                raise ValueError(
                    "Não há ocorrências registradas para o tipo de crime escolhido."
                )
            crime_filtro = correspondencia.iloc[0]

        return ServicosRanking.gerar_ranking_aisp(
            dados_normalizados,
            tipo_crime=crime_filtro,
        )

    def analisar_regiao(
        self,
        cidade: str,
        bairro: str,
        dados: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        base = self._obter_base_dados(dados)
        return ServicosPeriodos.analisar_regiao(
            base,
            cidade=cidade,
            bairro=bairro,
        )

    def gerar_saida_json(self, dados: Optional[pd.DataFrame] = None) -> str:
        base = self._obter_base_dados(dados)
        return ControleDados.gerar_saida(base)

    def exportar_json(
        self,
        nome_arquivo: str,
        dados: Optional[pd.DataFrame] = None,
    ) -> str:
        if not nome_arquivo.lower().endswith(".json"):
            nome_arquivo += ".json"

        json_str = self.gerar_saida_json(dados)
        with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
            arquivo.write(json_str)

        return nome_arquivo