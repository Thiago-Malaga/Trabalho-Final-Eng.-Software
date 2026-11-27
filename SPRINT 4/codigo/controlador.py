from typing import Optional

import pandas as pd

from controle_dados import ControleDados
from dados import Dados
from servicos_filtro import  (
    ServicosFiltro,
    FiltroDataInicio,
    FiltroDataFim,
    FiltroTextoIgual,
 ) # atualizado strategy

from servicos_periodos import ServicosPeriodos
from servicos_ranking import ServicosRanking

from padrao_caching_proxy import CachingProxyConsultas, ConsultasReais


class Controlador:
    """Facade que centraliza e coordena as operações entre a interface e os subsistemas."""

    def __init__(self):
        self.dados = Dados()
        self.controle_dados = ControleDados(self.dados)

        #instancia o proxy de caching
        consultas_reais = ConsultasReais(self.controle_dados.obter_dados())
        self.consultas = CachingProxyConsultas(consultas_reais)

    def _obter_base_dados(self, dados: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        if dados is not None:
            return dados
        base = self.controle_dados.obter_dados()
        if base.empty:
            raise ValueError("Nenhum dado carregado. Importe um arquivo TSV antes de continuar.")
        return base

    def importar_dados(self, caminho: str) -> pd.DataFrame:
        retorno = self.controle_dados.carregar_dados(caminho)
        self.consultas._servico_real._dados = self.controle_dados.obter_dados()
        self.consultas.limpar_cache() #limpa o cache quando novos dados sao carregados
        return retorno

    def carregar_tsv(self, caminho: str) -> pd.DataFrame:
        self.consultas.limpar_cache() #limpa o cache quando novos dados sao carregados
        dados = self.controle_dados.carregar_dados(caminho)
        retorno = ControleDados._normalizar_dados(dados)[ControleDados.COLUNAS_TESTE]
        self.consultas._servico_real._dados = self.controle_dados.obter_dados()
        return retorno

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
        #dados: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        #base = self._obter_base_dados(dados)

        

        #proxy sequeestra o chamado e verifica se ja tem cache ou n
        return self.consultas.filtrar_ocorrencias(data_inicio=data_inicio, data_fim=data_fim, cidade=cidade, tipo_crime=tipo_crime)
        #return ServicosFiltro.filtrar_ocorrencias(base, filtros) #antes do proxy

    def gerar_ranking_aisp(
        self,
        tipo_crime: Optional[str] = None,
        #dados: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        #base = self._obter_base_dados(dados)

        return self.consultas.gerar_ranking_aisp(tipo_crime=tipo_crime)
        #return ServicosRanking.gerar_ranking_aisp( dados_normalizados, tipo_crime=crime_filtro)

    def analisar_regiao(
        self,
        cidade: str,
        bairro: str,
        #dados: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        #base = self._obter_base_dados(dados)

        #proxy no lugar de chamar direto o servico
        return self.consultas.analisar_regiao(cidade=cidade, bairro=bairro)
        #return ServicosPeriodos.analisar_regiao( base, cidade=cidade, bairro=bairro)

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