class ServicosRanking:
    @staticmethod
    def gerar_ranking_aisp(dados, tipo_crime=None):
        if tipo_crime is not None:
            dados = dados[dados["Tipo do crime"] == tipo_crime]

        if dados.empty:
            raise ValueError("Não há ocorrências registradas para o tipo de crime escolhido.")

        ranking = dados.groupby("AISP").size().reset_index(name="Total")
        return ranking.sort_values("Total", ascending=False).reset_index(drop=True)