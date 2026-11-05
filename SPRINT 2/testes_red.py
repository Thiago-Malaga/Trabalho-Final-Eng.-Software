import unittest
from pathlib import Path

import pandas as pd

def carregar_tsv(caminho):
    return 1

def filtrar_ocorrencias(dados, data_inicio=None, data_fim=None, cidade=None, tipo_crime=None):
    return 1

def gerar_ranking_aisp(dados, tipo_crime):
    return 1

def analisar_bairro(dados, cidade, bairro):
    return 1



ARQUIVO_TESTE = Path(__file__).with_name("dados_teste.tsv")
#colunas esperadas
COLUNAS = [
    "Cidade",
    "AISP",
    "Data",
    "Horário",
    "Tipo do crime",
    "Ambiente",
    "Bairro",
]


class TesteAnalisador(unittest.TestCase):

    def setUp(self):
        # A amostra será lida de um arquivo externo, ainda a ser criado.
        self.dados = pd.read_csv(ARQUIVO_TESTE, sep="\t", dtype=str)

        # Seleção de partes da amostra para cada conjunto de testes.
        self.dados = self.dados[COLUNAS]
        self.cidade_teste = self.dados["Cidade"].iloc[0]
        self.bairro_teste = self.dados[self.dados["Cidade"] == self.cidade_teste]["Bairro"].iloc[0]
        self.tipo_teste = self.dados["Tipo do crime"].iloc[0]

    # HU01 — Importação do arquivo TSV
    def test_importar_tsv(self):
        #le o arquivo de teste
        resultado = carregar_tsv(str(ARQUIVO_TESTE))

        self.assertIsInstance(resultado, pd.DataFrame) #verifica se o resultado é um DataFrame
        self.assertEqual(list(resultado.columns), COLUNAS) #ve se tem todas as colunas
        self.assertGreater(len(resultado), 0) #ve se tem algum registro

    # HU02 — Filtros por período, cidade e tipo de crime

    def test_filtrar_por_periodo(self):
        #pega os dados lidos pelo arquivo de teste e pega a primeira data do arquivo
        data = self.dados["Data"].iloc[0]
        #filtra os dados pea primeira linha
        resultado = filtrar_ocorrencias(self.dados, data_inicio=data, data_fim=data)

        self.assertTrue((resultado["Data"] == data).all()) #ve se as datas batem

    #testes de filtro HU02
    def test_filtrar_por_cidade(self):
        #filtra os dados pelo nome da cidade
        resultado = filtrar_ocorrencias(self.dados, cidade=self.cidade_teste)
        self.assertTrue((resultado["Cidade"] == self.cidade_teste).all())

    def test_filtrar_por_tipo_de_crime(self):
        #verifica se o filtro retorna o tipo de crime da primeira linha do arquivo de teste
        resultado = filtrar_ocorrencias(self.dados, tipo_crime=self.tipo_teste)
        self.assertTrue((resultado["Tipo do crime"] == self.tipo_teste).all())

    def test_filtrar_por_cidade_e_crime(self):
        #pega a cidade e o tipo de crime da primeira linha do arquivo de teste
        resultado = filtrar_ocorrencias(self.dados, cidade=self.cidade_teste, tipo_crime=self.tipo_teste)

        #verifica se as ocorrencias filtradas tem apenas a cidade esperada
        self.assertTrue((resultado["Cidade"] == self.cidade_teste).all())
        #verifica se as ocorrencias filtradas tem apenas o tipo de crime esperado
        self.assertTrue((resultado["Tipo do crime"] == self.tipo_teste).all())

    def test_retorna_dataframe_vazio_para_erro_filtro(self):
        #pega o resultado do filtro com uma cidade inexistente
        resultado = filtrar_ocorrencias(self.dados, cidade="__CIDADE_INEXISTENTE__")

        self.assertIsInstance(resultado, pd.DataFrame) #ve se retorna um data frame
        self.assertTrue(resultado.empty) #se ele ta vazio
        self.assertEqual(list(resultado.columns), COLUNAS) #se as colunas batem com as esperadas


    def test_mantem_colunas_apos_filtrar(self):
        #pega a cidade teste
        resultado = filtrar_ocorrencias(self.dados, cidade=self.cidade_teste)

        self.assertEqual(list(resultado.columns), COLUNAS) #verifica a ordem das colunas 
    #fim testes de filtro HU02
    


    # HU03 — Ranking de AISPs por tipo de crime

    def test_gerar_ranking_por_aisp(self):
        #gera o ranking do arquivo de teste 
        resultado = gerar_ranking_aisp(
            self.dados,
            tipo_crime=self.tipo_teste,
        )

        self.assertIsInstance(resultado, pd.DataFrame) #verifica se o resultado é um DataFrame
        self.assertEqual(list(resultado.columns), ["AISP", "Total"]) #verifica se tem as colunas AISP e total
        self.assertGreater(len(resultado), 0) #verifica se tem algum registro

    def test_ordenar_ranking_decrescente(self):

        resultado = gerar_ranking_aisp(
            self.dados,
            tipo_crime=self.tipo_teste,
        )

        totais = resultado["Total"].tolist()
        self.assertEqual(totais, sorted(totais, reverse=True))

    def test_considerar_tipo_de_crime_escolhido(self):
        resultado = gerar_ranking_aisp(
            self.dados,
            tipo_crime=self.tipo_teste,
        )

        ocorrencias = self.dados[
            self.dados["Tipo do crime"] == self.tipo_teste
        ]
        self.assertEqual(
            resultado["Total"].sum(),
            len(ocorrencias),
        )

    def test_avisar_quando_nao_houver_ocorrencias_no_ranking(self):
        with self.assertRaises(ValueError):
            gerar_ranking_aisp(
                self.dados,
                tipo_crime="__TIPO_INEXISTENTE__",
            )

    # HU04 — Estatísticas do bairro por faixa horária e dia da semana

    def test_analisar_cidade_e_bairro_selecionados(self):
        resultado = analisar_bairro(
            self.dados,
            cidade=self.cidade_teste,
            bairro=self.bairro_teste,
        )

        self.assertIsInstance(resultado, dict)
        self.assertIn("por_faixa_horaria", resultado)
        self.assertIn("por_dia_semana", resultado)


    def test_contabilizar_por_dia_da_semana(self):
        #pega o resultado da analise do bairro e cidade selecionados
        resultado = analisar_bairro(self.dados,cidade=self.cidade_teste,bairro=self.bairro_teste)

        #verifica se os dias da semana batem
        dias = resultado["por_dia_semana"]
        self.assertEqual(set(dias),{"seg.", "ter.", "qua.","qui.", "sex.", "sáb.", "dom.",})

        #verifica se a soma dos dias batem com a soma das ocorrencias selecionados
        self.assertEqual(
            sum(dias.values()),
            len(self.dados[
                (self.dados["Cidade"] == self.cidade_teste)
                & (self.dados["Bairro"] == self.bairro_teste)
            ]),
        )

    def test_avisar_quando_bairro_nao_tiver_ocorrencias(self):
        #verifica se o bairro selecionado tem ocorrencias, se nao tiver retorna um erro
        with self.assertRaises(ValueError):
            analisar_bairro(
                self.dados,
                cidade=self.cidade_teste,
                bairro="__BAIRRO_INEXISTENTE__",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)