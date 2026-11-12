from controle_dados import ControleDados
from servicos_periodos import ServicosPeriodos

class ServicosFiltro:
    @staticmethod
    def filtrar_ocorrencias(dados, data_inicio=None, data_fim=None, cidade=None, tipo_crime=None):
        resultado = ControleDados._normalizar_dados(dados)

        if data_inicio is not None:
            resultado = resultado[resultado["Data"] >= data_inicio]
        if data_fim is not None:
            resultado = resultado[resultado["Data"] <= data_fim]
        if cidade is not None:
            resultado = resultado[
                resultado["Cidade"].map(ControleDados._normalizar_texto)
                == ControleDados._normalizar_texto(cidade)
            ]
        if tipo_crime is not None:
            resultado = resultado[
                resultado["Tipo do crime"].map(ControleDados._normalizar_texto)
                == ControleDados._normalizar_texto(tipo_crime)
            ]

        return resultado[ControleDados.COLUNAS_TESTE]