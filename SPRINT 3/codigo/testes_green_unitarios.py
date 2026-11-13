
import unittest
from pathlib import Path

import pandas as pd
import json

from controle_dados import ControleDados
from servicos_periodos import ServicosPeriodos
from servicos_ranking import ServicosRanking
from servicos_filtro import ServicosFiltro



ARQUIVO_TESTE = Path(__file__).with_name("dados_saida_5000.tsv")
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
        dados_legados = ControleDados.carregar_tsv(str(ARQUIVO_TESTE))

        # Converte o formato oficial do TSV para o formato usado pelos testes.
        self.dados = ServicosFiltro.filtrar_ocorrencias(dados_legados)
        self.cidade_teste = self.dados["Cidade"].iloc[0]
        self.bairro_teste = self.dados[self.dados["Cidade"] == self.cidade_teste]["Bairro"].iloc[0]
        self.tipo_teste = self.dados["Tipo do crime"].iloc[0]

# HU01 — Importação do arquivo TSV

    def test_importar_tsv(self):
        #le o arquivo de teste
        #criterio de aceitação: 1
        resultado = ControleDados.carregar_tsv(str(ARQUIVO_TESTE))
        self.assertIsInstance(resultado, pd.DataFrame) #verifica se o resultado é um DataFrame
        

    def test_importar_tsv_colunas(self):
        #criterio de aceitação: 2
        resultado = ControleDados.carregar_tsv(str(ARQUIVO_TESTE))
        self.assertEqual(list(resultado.columns), COLUNAS) #ve se tem todas as colunas

    def test_importar_tsv_registros(self):
        #criterio de aceitação: 3
        resultado = ControleDados.carregar_tsv(str(ARQUIVO_TESTE))
        self.assertGreater(len(resultado), 0) #ve se tem algum registro

# HU02 — Filtros por período, cidade e tipo de crime

    def test_filtrar_por_periodo(self):
        #criterio de aceitação: 1
        #pega os dados lidos pelo arquivo de teste e pega a primeira data do arquivo
        data = self.dados["Data"].iloc[0]
        #filtra os dados pea primeira linha
        resultado = ServicosFiltro.filtrar_ocorrencias(self.dados, data_inicio=data, data_fim=data)
        self.assertTrue((resultado["Data"] == data).all()) #ve se as datas batem

    def test_filtrar_por_cidade(self):
        #filtra os dados pelo nome da cidade
        resultado = ServicosFiltro.filtrar_ocorrencias(self.dados, cidade=self.cidade_teste)
        self.assertTrue((resultado["Cidade"] == self.cidade_teste).all())

    def test_filtrar_por_tipo_de_crime(self):
        #criterio de aceitação: 2
        #verifica se o filtro retorna o tipo de crime da primeira linha do arquivo de teste
        resultado = ServicosFiltro.filtrar_ocorrencias(self.dados, tipo_crime=self.tipo_teste)
        self.assertTrue((resultado["Tipo do crime"] == self.tipo_teste).all())

    def test_filtrar_cidade_e_crime__cidade(self):
        #pega a cidade e o tipo de crime da primeira linha do arquivo de teste
        resultado = ServicosFiltro.filtrar_ocorrencias(self.dados, cidade=self.cidade_teste, tipo_crime=self.tipo_teste)

        #verifica se as ocorrencias filtradas tem apenas a cidade esperada
        self.assertTrue((resultado["Cidade"] == self.cidade_teste).all())

    def test_filtrar_cidade_e_crime__crime(self):
        #verifica se as ocorrencias filtradas tem apenas o tipo de crime esperado
        resultado = ServicosFiltro.filtrar_ocorrencias(self.dados, cidade=self.cidade_teste, tipo_crime=self.tipo_teste)

        self.assertTrue((resultado["Tipo do crime"] == self.tipo_teste).all())

    def test_filtrar_retorna_dataframe_para_erro(self):
        #criterio de aceitação: 3
        #pega o resultado do filtro com uma cidade inexistente
        resultado = ServicosFiltro.filtrar_ocorrencias(self.dados, cidade="__CIDADE_INEXISTENTE__")

        self.assertIsInstance(resultado, pd.DataFrame) #ve se retorna um data frame

    def test_filtrar_retorna_dataframe_vazio_para_erro(self):
        #criterio de aceitação: 3
        resultado = ServicosFiltro.filtrar_ocorrencias(self.dados, cidade="__CIDADE_INEXISTENTE__")

        self.assertTrue(resultado.empty) #se ele ta vazio

    def test_filtrar_retorna_dataframe_com_colunas_esperadas(self):
        #criterio de aceitação: 3
        resultado = ServicosFiltro.filtrar_ocorrencias(self.dados, cidade="__CIDADE_INEXISTENTE__")

        self.assertEqual(list(resultado.columns), COLUNAS) #se as colunas batem com as esperadas

    def test_filtrar_mantem_colunas_em_ordem(self):
        #criterio de aceitação: 3
        #pega a cidade teste
        resultado = ServicosFiltro.filtrar_ocorrencias(self.dados, cidade=self.cidade_teste)

        self.assertEqual(list(resultado.columns), COLUNAS) #verifica a ordem das colunas

# HU03 — Ranking de AISPs por tipo de crime

    def test_gerar_ranking_por_aisp(self):
        #criterio de aceitação: 1
        #gera o ranking do arquivo de teste
        resultado = ServicosRanking.gerar_ranking_aisp(
            self.dados,
        )

        self.assertIsInstance(resultado, pd.DataFrame) #verifica se o resultado é um DataFrame

    def test_ranking_colunas_esperadas(self):
        #criterio de aceitação: 1
        resultado = ServicosRanking.gerar_ranking_aisp(self.dados)

        self.assertEqual(list(resultado.columns), ["AISP", "Total"]) #verifica se tem as colunas AISP e total

    def test_ranking_verificaregistros(self):
        #criterio de aceitação: 1
        resultado = ServicosRanking.gerar_ranking_aisp(self.dados)

        self.assertGreater(len(resultado), 0) #verifica se tem algum registro

    def test_ranking_ordem_decrescente(self):
        #criterio de aceitação: 1
        resultado = ServicosRanking.gerar_ranking_aisp(self.dados)

        totais = resultado["Total"].tolist()
        self.assertEqual(totais, sorted(totais, reverse=True))

    def test_ranking_ranking_crime_com_quantidade_esperada(self):
        #criterio de aceitação: 2
        resultado = ServicosRanking.gerar_ranking_aisp(self.dados,tipo_crime=self.tipo_teste)

        ocorrencias = self.dados[self.dados["Tipo do crime"] == self.tipo_teste]
        self.assertEqual(
            resultado["Total"].sum(),
            len(ocorrencias),
        )

    def test_ranking_avisa_quando_nao_houver_ocorrencias(self):
        #criterio de aceitação: 3
        with self.assertRaises(ValueError):
            ServicosRanking.gerar_ranking_aisp(
                self.dados,
                tipo_crime="__TIPO_INEXISTENTE__",
            )

# HU04 — Estatísticas do bairro por faixa horária e dia da semana

    def test_analisar_regiao_retorna_dataframe(self):
        #criterio de aceitação: 1 e 2
        resultado = ServicosPeriodos.analisar_regiao(
            self.dados,
            cidade=self.cidade_teste,
            bairro=self.bairro_teste,
        )

        self.assertIsInstance(resultado, pd.DataFrame)

    def test_analisar_regiao_tem_coluna_dia_da_semana(self):
        resultado = ServicosPeriodos.analisar_regiao(
            self.dados,
            cidade=self.cidade_teste,
            bairro=self.bairro_teste,
        )

        self.assertIn("Dia da Semana", resultado.columns)

    def test_analisar_regiao_tem_coluna_faixa_horaria(self):
        resultado = ServicosPeriodos.analisar_regiao(
            self.dados,
            cidade=self.cidade_teste,
            bairro=self.bairro_teste,
        )

        self.assertIn("Faixa Horária", resultado.columns)

    def test_analisar_regiao_tem_coluna_quantidade(self):
        resultado = ServicosPeriodos.analisar_regiao(
            self.dados,
            cidade=self.cidade_teste,
            bairro=self.bairro_teste,
        )

        self.assertIn("Quantidade", resultado.columns)

    def test_analisar_regiao_avisa_quando_bairro_nao_tiver_ocorrencias(self):
        #criterio de aceitação: 3
        #verifica se o bairro selecionado tem ocorrencias, se nao tiver retorna um erro
        with self.assertRaises(ValueError):
            ServicosPeriodos.analisar_regiao(
                self.dados,
                cidade=self.cidade_teste,
                bairro="__BAIRRO_INEXISTENTE__",
            )

#testes de saida

    def test_gerar_saida_json(self):
        resultado = ControleDados.gerar_saida(self.dados)

        self.assertIsInstance(resultado, str)

    def test_gerar_saida_json_valido(self):
        resultado = ControleDados.gerar_saida(self.dados)

        #verifica se o resultado pode ser interpretado como um json valido
        json.loads(resultado)

    def test_gerar_saida_json_estrutura(self):
        resultado = ControleDados.gerar_saida(self.dados)
        dados_json = json.loads(resultado)

        self.assertIsInstance(dados_json, (dict, list))


if __name__ == "__main__":
    unittest.main(verbosity=2)
