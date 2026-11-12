from pathlib import Path

import pandas as pd

from dados import Dados

class ControleDados:
    """Responsável por carregar, validar e apresentar os dados criminais."""

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
        """
        Carrega um arquivo TSV, valida suas colunas e seus campos
        e armazena os registros na classe Dados.
        """
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
        """Informa se já existem registros carregados."""
        return self._dados.possui_dados()

    def obter_dados(self) -> pd.DataFrame:
        """Disponibiliza os dados armazenados."""
        return self._dados.obter_dados()

    def imprimir_todos_dados(self) -> None:
        """Imprime todos os registros carregados no terminal."""
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
        return ControleDados._normalizar_dados(dados).to_json(orient="records", force_ascii=False)