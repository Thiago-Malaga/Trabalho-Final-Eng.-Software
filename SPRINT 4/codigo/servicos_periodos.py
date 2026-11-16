from pathlib import Path
from controle_dados import ControleDados
from dados import Dados

import pandas as pd

class ServicosPeriodos:
    """Classe responsável pelas análises de períodos e utilitários de normalização."""
    
    DIAS = [
        "segunda-feira",
        "ter\u00e7a-feira",
        "quarta-feira",
        "quinta-feira",
        "sexta-feira",
        "s\u00e1bado",
        "domingo",
    ]

    def faixa_horaria(hora):
        if hora < 6:
            return "Madrugada"
        if hora < 12:
            return "Manhã"
        if hora < 18:
            return "Tarde"
        return "Noite"


    def analisar_regiao(dados, cidade, bairro):
        dados = ControleDados._normalizar_dados(dados)
        filtrado = dados[
            (dados["Cidade"].map(ControleDados._normalizar_texto) == ControleDados._normalizar_texto(cidade))
            & (dados["Bairro"].map(ControleDados._normalizar_texto) == ControleDados._normalizar_texto(bairro))
        ].copy()

        if filtrado.empty:
            raise ValueError("Não há ocorrências registradas para o bairro escolhido.")

        datas = pd.to_datetime(filtrado["Data"], dayfirst=True)
        horas = filtrado["Horário"].str.split(":").str[0].astype(int)

        filtrado["Dia da Semana"] = datas.dt.dayofweek.map(lambda d: ServicosPeriodos.DIAS[d])
        filtrado["Faixa Horária"] = horas.map(ServicosPeriodos.faixa_horaria)

        resultado = filtrado.groupby(["Dia da Semana", "Faixa Horária"]).size()
        resultado = resultado.reset_index(name="Quantidade")
        return resultado.sort_values("Quantidade", ascending=False)