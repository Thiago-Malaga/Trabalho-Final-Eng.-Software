from pathlib import Path

import pandas as pd

DIAS = [
    "segunda-feira",
    "ter\u00e7a-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "s\u00e1bado",
    "domingo",
]
COLUNAS_LEGADO = [
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


def carregar_tsv(caminho):
    return pd.read_csv(
        Path(caminho),
        sep="\t",
        dtype=str,
        encoding="utf-8-sig",
        keep_default_na=False,
    )


def _normalizar_dados(dados):
    if set(COLUNAS_TESTE).issubset(dados.columns):
        return dados.copy()

    faltantes = [coluna for coluna in COLUNAS_LEGADO if coluna not in dados.columns]
    if faltantes:
        raise ValueError(
            "Dados inválidos. Colunas ausentes: " + ", ".join(faltantes)
        )

    resultado = dados.copy()
    resultado["Cidade"] = resultado["Município"]
    resultado["Data"] = (
        resultado["Dia"].str.zfill(2)
        + "/"
        + resultado["Mês"].map(_mes_para_numero).str.zfill(2)
        + "/"
        + resultado["Ano"]
    )
    resultado["Hor\u00e1rio"] = resultado["Hora"].map(_normalizar_hora)
    resultado["Tipo do crime"] = resultado["Natureza"]
    return resultado


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


def filtrar_ocorrencias(
    dados,
    data_inicio=None,
    data_fim=None,
    cidade=None,
    tipo_crime=None,
):
    resultado = _normalizar_dados(dados)

    if data_inicio is not None:
        resultado = resultado[resultado["Data"] >= data_inicio]
    if data_fim is not None:
        resultado = resultado[resultado["Data"] <= data_fim]
    if cidade is not None:
        resultado = resultado[
            resultado["Cidade"].map(_normalizar_texto)
            == _normalizar_texto(cidade)
        ]
    if tipo_crime is not None:
        resultado = resultado[
            resultado["Tipo do crime"].map(_normalizar_texto)
            == _normalizar_texto(tipo_crime)
        ]

    return resultado[COLUNAS_TESTE]


def gerar_ranking_aisp(dados, tipo_crime=None):
    filtrado = _normalizar_dados(dados)
    if tipo_crime is not None:
        filtrado = filtrado[filtrado["Tipo do crime"] == tipo_crime]

    if filtrado.empty:
        raise ValueError("Não há ocorrências para os filtros informados.")

    return (
        filtrado.groupby("AISP")
        .size()
        .reset_index(name="Total")
        .sort_values("Total", ascending=False)
        .reset_index(drop=True)
    )


def gerar_saida(dados):
    return _normalizar_dados(dados).to_json(orient="records", force_ascii=False)


def faixa_horaria(hora):
    if hora < 6:
        return "Madrugada"
    if hora < 12:
        return "Manhã"
    if hora < 18:
        return "Tarde"
    return "Noite"


def analisar_regiao(dados, cidade, bairro):
    dados = _normalizar_dados(dados)
    filtrado = dados[
        (dados["Cidade"].map(_normalizar_texto) == _normalizar_texto(cidade))
        & (dados["Bairro"].map(_normalizar_texto) == _normalizar_texto(bairro))
    ].copy()

    if filtrado.empty:
        raise ValueError("Não há ocorrências registradas para o bairro escolhido.")

    datas = pd.to_datetime(filtrado["Data"], dayfirst=True)
    horas = filtrado["Horário"].str.split(":").str[0].astype(int)

    filtrado["Dia da Semana"] = datas.dt.dayofweek.map(lambda d: DIAS[d])
    filtrado["Faixa Horária"] = horas.map(faixa_horaria)

    resultado = filtrado.groupby(["Dia da Semana", "Faixa Horária"]).size()
    resultado = resultado.reset_index(name="Quantidade")
    return resultado.sort_values("Quantidade", ascending=False)