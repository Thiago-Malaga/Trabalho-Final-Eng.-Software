import time

from controlador import Controlador


class Terminal:
    """Interface mínima de interação com o usuário."""

    def __init__(self):
        self.controlador = Controlador()

    def _perguntar_exportacao_json(self, dataframe) -> None:
        """Pergunta ao usuário se deseja exportar o resultado atual para JSON."""
        escolha = input("\nDeseja exportar esta consulta para um arquivo JSON? (s/n): ").strip().lower()
        if escolha == "s":
            nome_arquivo = input("Digite o nome do arquivo (ex: consulta.json): ").strip()

            try:
                arquivo_salvo = self.controlador.exportar_json(nome_arquivo, dataframe)
                print(f"Arquivo '{arquivo_salvo}' salvo com sucesso!")
            except Exception as erro:
                print(f"Erro ao salvar o arquivo JSON: {erro}")

    def _imprimir_analise_periodos(self, resultado) -> None:
        """Exibe os dias por total de ocorrências e suas faixas horárias."""
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