from __future__ import annotations
from abc import ABC, abstractmethod
from collections import OrderedDict
import time #pra ver quando a consulta foi feita
import pandas as pd #talvez seja impor recursivo

from controle_dados import ControleDados
from dados import Dados
from servicos_filtro import (ServicosFiltro, FiltroDataInicio, FiltroDataFim, FiltroTextoIgual)
from servicos_periodos import ServicosPeriodos
from servicos_ranking import ServicosRanking

class InterfaceConsultas(ABC): #interface SUBJECT do padrao
    #interface que implementa os metodos abtratos que dps serao usados
    #pra sequestrar a chamada e verificar se a pesquisa ja foi feita anteriormente
    #pra n precisar fazer de novo

    #abstratos pq vai ser definido o que sera feito depois pra saber se tem cache ou n
    #se nao for declarado, da erro
    @abstractmethod
    def filtrar_ocorrencias(self, data_inicio: str | None = None, data_fim: str | None = None,
        cidade: str | None = None, tipo_crime: str | None = None) -> pd.DataFrame: #faz a alteracao p/ o strategy
        pass

    @abstractmethod
    def gerar_ranking_aisp(self, tipo_crime: str | None = None) -> pd.DataFrame: #mesmo aqui
        pass

    @abstractmethod
    def analisar_regiao(self, cidade: str | None, bairro: str | None) -> pd.DataFrame: #mesmo aqui
        pass


class ConsultasReais(InterfaceConsultas): #REAL SUBJECT do padrao
    #chama as consultas sem cache no caso de ser Miss

    def __init__(self, dados: pd.DataFrame) -> None:
        self._dados = dados

    def atualizar_dados(self, dados: pd.DataFrame) -> None:
        self._dados = dados

    #implementa os metodos abstratos da interface chamando os servicos
    def filtrar_ocorrencias(self, data_inicio: str | None = None, data_fim: str | None = None,
        cidade: str | None = None, tipo_crime: str | None = None) -> pd.DataFrame:


        #Strategy: o Controlador decide QUAIS filtros usar!! 
        #os `if` que antes ficavam dentro do ServicosFiltro vieram pra cá, 
        #mas agora eles só montam a lista. Quem filtra de verdade são as estratégias.

        filtros = []
        if data_inicio is not None:
            filtros.append(FiltroDataInicio(data_inicio))
        if data_fim is not None:
            filtros.append(FiltroDataFim(data_fim))
        if cidade is not None:
            filtros.append(FiltroTextoIgual("Cidade", cidade))
        if tipo_crime is not None:
            filtros.append(FiltroTextoIgual("Tipo do crime", tipo_crime))

        return ServicosFiltro.filtrar_ocorrencias(self._dados, filtros=filtros)
    

    def gerar_ranking_aisp(self, tipo_crime: str | None = None) -> pd.DataFrame:
        #mesma coisa pra esse
        dados_normalizados = ServicosFiltro.filtrar_ocorrencias(self._dados, []) # Filtro vazio, apenas para normalizar os dados

        return ServicosRanking.gerar_ranking_aisp(dados_normalizados, tipo_crime=tipo_crime)

    def analisar_regiao(self, cidade: str | None, bairro: str | None) -> pd.DataFrame:
        # e esse tbm
        return ServicosPeriodos.analisar_regiao(self._dados, cidade=cidade, bairro=bairro)



class CachingProxyConsultas(InterfaceConsultas): #PROXY
    #Verifica se tem cache e as estatisticas do padrao pra ver se deu certo
    def __init__(self, servico_real: InterfaceConsultas, capacidade_maxima: int = 32) -> None:
        #inicializa o proxy definindo quantas consultas podem ser armazenadas em cache
        if capacidade_maxima <= 0:
            raise ValueError("A capacidade máxima do cache deve ser maior que zero.")
        self._capacidade_maxima = capacidade_maxima #define a capacidade maxima do cache

        
        self._servico_real = servico_real #instancia a classe pra chamada das funcoes
        #classe essa que herda a interface e implementa os metodos abstratos

        #dicionario ordenado pra armazenar as consultas feitas e os resultados
        self._cache: OrderedDict[tuple, pd.DataFrame] = OrderedDict()

        #estatisticas do padrao
        self.hits: int = 0
        self.misses: int = 0
        self.ultimo_tempo_ms: float = 0.0
        self.ultimo_status: str = "N/A"


    @staticmethod #(vira apenas uma funcao dentro da classe, n precisa de self)
    def _normalizar_chave(valor: str | None) -> str | None:
        if valor is None:
            return None
        limpo = " ".join(str(valor).strip().split()).casefold()
        return limpo if limpo else None

    @classmethod #porque chama outros metodos (_normalizar_chave)
    def _criar_chave(cls, operacao: str, *parametros: str | None) -> tuple:
        #usa o nome da operacao e todos os parametros passados pra criar uma chave
        return (operacao, *(cls._normalizar_chave(p) for p in parametros))

    def _obter_ou_computar(self, chave: tuple, operacao) -> pd.DataFrame:
        inicio = time.perf_counter()
        #Cache Hit: retorna o resultado armazenado no cache
        if chave in self._cache:
            #move a chave para o final (mais recentemente usada)
            self._cache.move_to_end(chave)
            resultado = self._cache[chave].copy()

            #atualiza as estatisticas do padrao
            self.hits += 1
            self.ultimo_status = "CACHE HIT"
            self.ultimo_tempo_ms = (time.perf_counter() - inicio) * 1000
            return resultado

        # Cache Miss: chama a implementacao do objeto real
        resultado = operacao()
        self.misses += 1
        self.ultimo_status = "CACHE MISS"

        # retira o item last recentrly used se o cache estiver cheio
        if len(self._cache) >= self._capacidade_maxima:
            self._cache.popitem(last=False)

        # adiciona o resultado novo ao cache
        self._cache[chave] = resultado.copy()

        #atualiza as estatisticas do padrao
        self.ultimo_tempo_ms = (time.perf_counter() - inicio) * 1000
        return resultado.copy()

    def limpar_cache(self) -> None:
        #reseta o cache e as estatisticas do padrao
        #usado quando muda de arquivo
        self._cache.clear()
        self.hits = 0
        self.misses = 0
        self.ultimo_status = "CACHE LIMPO"
        self.ultimo_tempo_ms = 0.0

    def obter_estatisticas(self) -> dict[str, int | float | str]:
        total = self.hits + self.misses
        taxa_acerto = (self.hits / total * 100.0) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "itens_em_cache": len(self._cache),
            "capacidade_maxima": self._capacidade_maxima,
            "taxa_acerto_percent": round(taxa_acerto, 2),
            "ultimo_status": self.ultimo_status,
            "ultimo_tempo_ms": round(self.ultimo_tempo_ms, 3),
        }

    #declara os metodos abstratos da interface
    #Sequestra as chamadas de funcao pra ver se ja foram feiras
    def filtrar_ocorrencias(self, data_inicio: str | None = None, data_fim: str | None = None,
        cidade: str | None = None, tipo_crime: str | None = None) -> pd.DataFrame:
        # '->' define o tipo de retorno da funcao
        chave = self._criar_chave("filtro", data_inicio, data_fim, cidade, tipo_crime)

        #chama a funcao que verifica se ja foi feita a consulta
        #se sim, retorna o resultado do cache
        #se nao, chama a funcao real e armazena o resultado no cache
        return self._obter_ou_computar(
            chave,
            lambda: self._servico_real.filtrar_ocorrencias(data_inicio=data_inicio, data_fim=data_fim, cidade=cidade, tipo_crime=tipo_crime),
)

    def gerar_ranking_aisp(self, tipo_crime: str | None = None) -> pd.DataFrame:
        chave = self._criar_chave("ranking_aisp", tipo_crime)
        return self._obter_ou_computar(
            chave,
            lambda: self._servico_real.gerar_ranking_aisp(tipo_crime=tipo_crime),
        )

    def analisar_regiao(self, cidade: str | None, bairro: str | None) -> pd.DataFrame:
        chave = self._criar_chave("analisar_regiao", cidade, bairro)
        return self._obter_ou_computar(
            chave,
            lambda: self._servico_real.analisar_regiao(cidade=cidade, bairro=bairro),
        )