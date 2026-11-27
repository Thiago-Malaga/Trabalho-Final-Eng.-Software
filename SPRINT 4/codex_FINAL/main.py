from __future__ import annotations
from typing import Optional
from abc import ABC, abstractmethod
from collections import OrderedDict
import time #pra ver quando a consulta foi feita
import pandas as pd #talvez seja impor recursivo
from pathlib import Path


class Dados:
    #Armazena os registros criminais em um DataFrame

    def __init__(self):
        self._dados = pd.DataFrame()

    def definir_dados(self, dados: pd.DataFrame) -> None:
        #Substitui os dados armazenados por uma cópia do DataFrame recebido
        self._dados = dados.copy()

    def obter_dados(self) -> pd.DataFrame:
        #Retorna uma cópia dos dados para evitar alterações externas acidentais
        return self._dados.copy()

    def possui_dados(self) -> bool:
        return not self._dados.empty


class ControleDados:
    #Responsável por carregar, validar e apresentar os dados criminais

    COLUNAS_ESPERADAS = [
        "Ano",
        "Mês",
        "Dia",
        "Dia da Semana",
        "Hora",
        "AISP",
        "Município",
        "Bairro",
        "Natureza",
        "Ambiente",
    ]

    COLUNAS_TESTE = [
            "Cidade",
            "AISP",
            "Data",
            "Horário",
            "Tipo do crime",
            "Ambiente",
            "Bairro",
        ]

    def __init__(self, dados: Dados):
        self._dados = dados

    def carregar_dados(self, caminho: str) -> pd.DataFrame:
        #Carrega um arquivo TSV, valida suas colunas e seus campose armazena os registros na classe Dados.
        arquivo = Path(caminho)

        if not arquivo.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        if arquivo.suffix.lower() != ".tsv":
            raise ValueError("Formato inválido. Informe um arquivo .tsv.")

        try:
            dataframe = pd.read_csv(
                arquivo,
                sep="\t",
                dtype=str,
                encoding="utf-8-sig",
                keep_default_na=False,
            )
        except (pd.errors.ParserError, UnicodeDecodeError) as erro:
            raise ValueError(f"Não foi possível interpretar o TSV: {erro}") from erro

        # Remove espaços acidentais dos nomes das colunas.
        dataframe.columns = [coluna.strip() for coluna in dataframe.columns]

        if dataframe.columns.tolist() != self.COLUNAS_ESPERADAS:
            recebidas = dataframe.columns.tolist()
            faltantes = [
                coluna for coluna in self.COLUNAS_ESPERADAS
                if coluna not in recebidas
            ]
            extras = [
                coluna for coluna in recebidas
                if coluna not in self.COLUNAS_ESPERADAS
            ]

            detalhes = []
            if faltantes:
                detalhes.append(f"colunas ausentes: {', '.join(faltantes)}")
            if extras:
                detalhes.append(f"colunas não esperadas: {', '.join(extras)}")
            if not faltantes and not extras:
                detalhes.append("as colunas estão em uma ordem diferente da esperada")

            raise ValueError("Estrutura TSV inválida: " + "; ".join(detalhes) + ".")

        if dataframe.empty:
            raise ValueError("O arquivo TSV não contém registros.")

        # Remove espaços nas extremidades e identifica campos vazios.
        for coluna in self.COLUNAS_ESPERADAS:
            dataframe[coluna] = dataframe[coluna].str.strip()

        campos_vazios = dataframe.isna() | dataframe.eq("")
        if campos_vazios.any().any():
            colunas_com_vazios = campos_vazios.columns[
                campos_vazios.any()
            ].tolist()
            raise ValueError(
                "Existem informações vazias nas colunas: "
                + ", ".join(colunas_com_vazios)
            )

        self._dados.definir_dados(dataframe)
        return self._dados.obter_dados()

    def verificar_dados(self) -> bool:
        #Informa se já existem registros carregados
        return self._dados.possui_dados()

    def obter_dados(self) -> pd.DataFrame:
        #Disponibiliza os dados armazenados
        return self._dados.obter_dados()

    def imprimir_todos_dados(self) -> None:
        #Imprime todos os registros carregados no terminal
        dataframe = self._dados.obter_dados()

        if dataframe.empty:
            print("Nenhum dado foi carregado.")
            return

        print(dataframe.to_string(index=False))
        print(f"\nTotal de registros: {len(dataframe)}")

    def carregar_tsv(caminho):
        controle = ControleDados(Dados())
        dados = controle.carregar_dados(caminho)
        return ControleDados._normalizar_dados(dados)[ControleDados.COLUNAS_TESTE]

    def _mes_para_numero(mes):
        meses = {
            "jan": "01",
            "fev": "02",
            "mar": "03",
            "abr": "04",
            "mai": "05",
            "jun": "06",
            "jul": "07",
            "ago": "08",
            "set": "09",
            "out": "10",
            "nov": "11",
            "dez": "12",
        }
        chave = str(mes).strip().lower().replace(".", "")[:3]
        if chave not in meses:
            raise ValueError(f"Mês inválido: {mes}")
        return meses[chave]

    def _normalizar_hora(hora):
        valor = str(hora).strip()
        return valor if ":" in valor else f"{valor.zfill(2)}:00"

    def _normalizar_texto(valor):
        return str(valor).strip().casefold()

    def _normalizar_dados(dados):
        if set(ControleDados.COLUNAS_TESTE).issubset(dados.columns):
            return dados.copy()

        faltantes = [coluna for coluna in ControleDados.COLUNAS_ESPERADAS if coluna not in dados.columns]
        if faltantes:
            raise ValueError(
                "Dados inválidos. Colunas ausentes: " + ", ".join(faltantes)
            )

        resultado = dados.copy()
        resultado["Cidade"] = resultado["Município"]
        resultado["Data"] = (
            resultado["Dia"].str.zfill(2)
            + "/"
            + resultado["Mês"].map(ControleDados._mes_para_numero).str.zfill(2)
            + "/"
            + resultado["Ano"]
        )
        resultado["Horário"] = resultado["Hora"].map(ControleDados._normalizar_hora)
        resultado["Tipo do crime"] = resultado["Natureza"]
        return resultado

    def gerar_saida(dados):
        return dados.to_json(orient="records", force_ascii=False)


class FiltroStrategy(ABC):
    #Strategy (interface): todo filtro tem que ter o método aplicar(df)

    # Aqui só define *O QUE* um filtro faz (recebe a tabela e devolve ela filtrada).
    # COMO filtra fica por conta de cada classe filha.
    @abstractmethod
    def aplicar(self, df):
        pass


class FiltroDataInicio(FiltroStrategy):
    #Estratégia: mantém as ocorrências a partir de uma data

    def __init__(self, data_inicio):
        # Guardo a data dentro do próprio filtro assim o aplicar() só precisa receber a tabela, e todos os filtros ficam com o mesmo formato.
        self.data_inicio = data_inicio

    def aplicar(self, df):
        # Era o antigo `if data_inicio is not None`, só que agora está separado numa classe própria.
        return df[df["Data"] >= self.data_inicio]


class FiltroDataFim(FiltroStrategy):
    #Estratégia: mantém as ocorrências até uma data

    def __init__(self, data_fim):
        self.data_fim = data_fim

    def aplicar(self, df):
        return df[df["Data"] <= self.data_fim]


class FiltroTextoIgual(FiltroStrategy):
    #Estratégia: mantém as ocorrências em que a coluna é igual a um texto

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
    #Context: é quem USA os filtros (as estratégias)

    @staticmethod
    def filtrar_ocorrencias(dados, filtros):
        resultado = ControleDados._normalizar_dados(dados)

        # Antes tinha um `if` pra cada critério (data, cidade, crime). Agora esse método não sabe quais filtros existem: ele só recebe uma lista de filtros e manda cada um se aplicar, um depois do outro.
        for filtro in filtros:
            # Todo filtro tem o método aplicar(), mas cada um faz do seu jeito. Se eu criar um filtro novo, este método não precisa mudar.
            resultado = filtro.aplicar(resultado)

        return resultado[ControleDados.COLUNAS_TESTE]




class AnalisePeriodoStrategy(ABC):
    #Strategy (interface): toda estratégia de período tem que ter o método aplicar(df)

    # Aqui só define *O QUE* uma etapa da análise faz (recebe a tabela e devolve uma tabela).
    # COMO cada etapa transforma os dados fica por conta de cada classe filha.
    @abstractmethod
    def aplicar(self, df):
        pass


class CalcularDiaSemanaStrategy(AnalisePeriodoStrategy):
    #Estratégia: calcula o dia da semana a partir da coluna Data

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
    #Estratégia: calcula a faixa horária a partir da coluna Horário

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
    #Estratégia: agrupa as ocorrências por dia da semana e faixa horária

    def aplicar(self, df):
        resultado = df.groupby(["Dia da Semana", "Faixa Horária"]).size()
        resultado = resultado.reset_index(name="Quantidade")
        return resultado.sort_values("Quantidade", ascending=False)


class ServicosPeriodos:
    #Context: é quem USA as estratégias para montar a análise de períodos

    DIAS = CalcularDiaSemanaStrategy.DIAS

    @staticmethod
    def faixa_horaria(hora):
        #Mantém disponível o cálculo antigo de faixa horária
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

class RankingStrategy(ABC):
    #Strategy (interface): toda estratégia do ranking tem que ter o método aplicar(df)

    # Aqui só define *O QUE* uma etapa do ranking faz (recebe a tabela e devolve uma tabela).
    # COMO cada etapa transforma os dados fica por conta de cada classe filha.
    @abstractmethod
    def aplicar(self, df):
        pass


class AgruparPorAISPStrategy(RankingStrategy):
    #Estratégia: conta o total de ocorrências de cada AISP

    def aplicar(self, df):
        # Agrupa as ocorrências por AISP e cria a coluna Total com a quantidade de cada grupo.
        return df.groupby("AISP").size().reset_index(name="Total")


class OrdenarRankingStrategy(RankingStrategy):
    #Estratégia: ordena o ranking do maior para o menor total de ocorrências

    def aplicar(self, df):
        # Depende da coluna Total, que é criada pela estratégia de agrupamento.
        return df.sort_values("Total", ascending=False).reset_index(drop=True)


class ServicosRanking:
    #é quem USA as estratégias para montar o ranking de AISPs

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

class Controlador:
    #Facade que centraliza e coordena as operações entre a interface e os subsistemas

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

class Terminal:
    #Interface mínima de interação com o usuário

    def __init__(self):
        self.controlador = Controlador()

    def _perguntar_exportacao_json(self, dataframe) -> None:
        #Pergunta ao usuário se deseja exportar o resultado atual para JSON
        escolha = input("\nDeseja exportar esta consulta para um arquivo JSON? (s/n): ").strip().lower()
        if escolha == "s":
            nome_arquivo = input("Digite o nome do arquivo (ex: consulta.json): ").strip()

            try:
                arquivo_salvo = self.controlador.exportar_json(nome_arquivo, dataframe)
                print(f"Arquivo '{arquivo_salvo}' salvo com sucesso!")
            except Exception as erro:
                print(f"Erro ao salvar o arquivo JSON: {erro}")

    def _imprimir_analise_periodos(self, resultado) -> None:
        #Exibe os dias por total de ocorrências e suas faixas horárias
        totais_dia = (
            resultado.groupby("Dia da Semana")["Quantidade"]
            .sum()
            .sort_values(ascending=False, kind="stable")
        )

        for dia, total in totais_dia.items():
            print(f"\n=========== {dia} (total={total}) ===========")
            faixas = resultado[resultado["Dia da Semana"] == dia]
            faixas = faixas.sort_values("Quantidade", ascending=False, kind="stable")
            for _, faixa in faixas.iterrows():
                print(f"{faixa['Faixa Horária']}: {faixa['Quantidade']}")

    def exibir_menu(self) -> None:
        while True:
            print("\n=== ANALISADOR DE OCORRÊNCIAS CRIMINAIS ===")
            print("1 - Importar arquivo TSV")
            print("2 - Imprimir todos os dados")
            print("3 - Analisar região por dia e faixa horária")
            print("4 - Gerar ranking por AISP")
            print("5 - Filtrar ocorrências")
            print("0 - Sair")

            opcao = input("Escolha uma opção: ").strip()

            if opcao == "1":
                caminho = input("Caminho do arquivo TSV: ").strip()

                try:
                    dados = self.controlador.importar_dados(caminho)
                    print("\nImportação realizada com sucesso!")
                    print(f"Registros carregados: {len(dados)}")
                except (FileNotFoundError, ValueError, OSError) as erro:
                    print(f"Erro na importação: {erro}")

            elif opcao == "2":
                self.controlador.imprimir_dados()

            elif opcao == "3":
                if not self.controlador.possui_dados():
                    print("Erro: importe um arquivo TSV antes de analisar uma região.")
                    continue

                cidade = input("Município: ").strip()
                bairro = input("Bairro: ").strip()

                try:
                    hits_antes = self.controlador.consultas.obter_estatisticas()["hits"]

                    inicio = time.perf_counter()
                    resultado = self.controlador.analisar_regiao(cidade, bairro)
                    tempo = time.perf_counter() - inicio

                    print("\nAnálise da região:")
                    self._imprimir_analise_periodos(resultado)
                    self._exibir_status_cache(hits_antes, tempo)

                    self._perguntar_exportacao_json(resultado)

                except ValueError as erro:
                    print(f"Erro na análise: {erro}")

            elif opcao == "4":
                if not self.controlador.possui_dados():
                    print("Erro: importe um arquivo TSV antes de gerar o ranking.")
                    continue

                tipo_crime = input(
                    "Tipo de crime (pressione Enter para todos): "
                ).strip() or None

                try:
                    hits_antes = self.controlador.consultas.obter_estatisticas()["hits"]

                    inicio = time.perf_counter()
                    resultado = self.controlador.gerar_ranking_aisp(
                        tipo_crime=tipo_crime
                    )
                    tempo = time.perf_counter() - inicio

                    print("\nRanking por AISP:")
                    print(resultado.to_string(index=False))
                    self._exibir_status_cache(hits_antes, tempo)

                    self._perguntar_exportacao_json(resultado)

                except ValueError as erro:
                    print(f"Erro no ranking: {erro}")

            elif opcao == "5":
                if not self.controlador.possui_dados():
                    print("Erro: importe um arquivo TSV antes de filtrar.")
                    continue

                print("\nInsira os parâmetros de filtro (pressione Enter para ignorar um parâmetro):")
                data_inicio = input("Data início (DD/MM/AAAA): ").strip() or None
                data_fim = input("Data fim (DD/MM/AAAA): ").strip() or None
                cidade = input("Município: ").strip() or None
                tipo_crime = input("Tipo de crime: ").strip() or None

                try:
                    hits_antes = self.controlador.consultas.obter_estatisticas()["hits"]

                    inicio = time.perf_counter()
                    resultado = self.controlador.filtrar_ocorrencias(
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        cidade=cidade,
                        tipo_crime=tipo_crime,
                    )
                    tempo = time.perf_counter() - inicio

                    if resultado.empty:
                        print("\nNenhuma ocorrência encontrada com os filtros aplicados.")
                    else:
                        print("\nResultados do Filtro:")
                        print(resultado.to_string(index=False))
                        print(f"\nTotal de registros filtrados: {len(resultado)}")

                        self._exibir_status_cache(hits_antes, tempo)
                        self._perguntar_exportacao_json(resultado)

                except ValueError as erro:
                    print(f"Erro ao filtrar: {erro}")

            elif opcao == "0":
                print("Encerrando o sistema.")
                break

            else:
                print("Opção inválida. Tente novamente.")

    def _exibir_status_cache(self, hits_antes: int, tempo: float) -> None:
        stats = self.controlador.consultas.obter_estatisticas()

        if stats["hits"] > hits_antes:
            print("[CACHE HIT] Resultado obtido do cache.")
        else:
            print("[CACHE MISS] Consulta executada na base.")

        print(f"Tempo da pesquisa: {tempo:.6f} segundos.")
        print(f"Hits: {stats['hits']} | Misses: {stats['misses']}")


if __name__ == "__main__":
    terminal = Terminal()
    terminal.exibir_menu()
