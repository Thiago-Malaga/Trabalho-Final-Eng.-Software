from controlador import Controlador


class Terminal:
    """Interface mínima de interação com o usuário."""

    def __init__(self):
        self.controlador = Controlador()

    def exibir_menu(self) -> None:
        while True:
            print("\n=== ANALISADOR DE OCORRÊNCIAS CRIMINAIS ===")
            print("1 - Importar arquivo TSV")
            print("2 - Imprimir todos os dados")
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

            elif opcao == "0":
                print("Encerrando o sistema.")
                break

            else:
                print("Opção inválida. Tente novamente.")
