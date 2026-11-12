from controlador import Controlador
from servicos_periodos import analisar_regiao, filtrar_ocorrencias
from servicos_ranking import gerar_ranking_aisp


class Terminal:
    """Interface mínima de interação com o usuário."""

    def __init__(self):
        self.controlador = Controlador()

    def exibir_menu(self) -> None:
        while True:
            print("\n=== ANALISADOR DE OCORRÊNCIAS CRIMINAIS ===")
            print("1 - Importar arquivo TSV")
            print("2 - Imprimir todos os dados")
            print("3 - Analisar região por dia e faixa horária")
            print("4 - Gerar ranking por AISP")
            print("0 - Sair")

            opcao = input("Escolha uma opção: ").strip()

            if opcao == "1":
                caminho = input("Caminho do arquivo TSV: ").strip()

                try:
                    dados = self.controlador.importar_dados(caminho)
                    print(f"\nImportação realizada com sucesso!")
                    print(f"Registros carregados: {len(dados)}")
                except (FileNotFoundError, ValueError, OSError) as erro:
                    print(f"Erro na importação: {erro}")

            elif opcao == "2":
                self.controlador.imprimir_dados()

            elif opcao == "3":
                dados = self.controlador.obter_dados()
                if dados.empty:
                    print("Erro: importe um arquivo TSV antes de analisar uma região.")
                    continue

                cidade = input("Município: ").strip()
                bairro = input("Bairro: ").strip()

                try:
                    resultado = analisar_regiao(dados, cidade, bairro)
                    print("\nAnálise da região:")
                    print(resultado.to_string(index=False))
                except ValueError as erro:
                    print(f"Erro na análise: {erro}")

            elif opcao == "4":
                dados = self.controlador.obter_dados()
                if dados.empty:
                    print("Erro: importe um arquivo TSV antes de gerar o ranking.")
                    continue

                tipo_crime = input(
                    "Tipo de crime (pressione Enter para todos): "
                ).strip()

                try:
                    dados_normalizados = filtrar_ocorrencias(dados)
                    if tipo_crime:
                        tipos = dados_normalizados["Tipo do crime"]
                        correspondencia = tipos[
                            tipos.str.casefold() == tipo_crime.casefold()
                        ]
                        if correspondencia.empty:
                            raise ValueError(
                                "Não há ocorrências registradas para o tipo de crime escolhido."
                            )
                        tipo_crime = correspondencia.iloc[0]

                    resultado = gerar_ranking_aisp(
                        dados_normalizados,
                        tipo_crime or None,
                    )
                    print("\nRanking por AISP:")
                    print(resultado.to_string(index=False))
                except ValueError as erro:
                    print(f"Erro no ranking: {erro}")

            elif opcao == "0":
                print("Encerrando o sistema.")
                break

            else:
                print("Opção inválida. Tente novamente.")
