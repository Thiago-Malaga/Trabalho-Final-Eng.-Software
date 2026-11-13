import pandas as pd

# 1. Nomes dos arquivos (confira se o nome de entrada bate com o seu arquivo)
arquivo_entrada = "dados_tsv_parana_2026.tsv"
arquivo_saida = "dados_saida_5000.tsv"
qtd_registros = 5000

# 2. Lê o arquivo respeitando a codificação do Windows (cp1252) ou UTF-8
try:
    df = pd.read_csv(arquivo_entrada, sep="\t", encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(arquivo_entrada, sep="\t", encoding="cp1252")

# 3. Remove espaços extras nos cabeçalhos e exclui 'ID' e 'Tipo Natureza'
df.columns = df.columns.str.strip()
df = df.drop(columns=["ID", "Tipo Natureza"], errors="ignore")

# 4. Caso o arquivo original já tenha sido baixado com '' gravado, corrige os termos
if df.to_string().find("\ufffd") != -1:
    df.columns = [c.replace("M\ufffds", "Mês").replace("Munic\ufffdpio", "Município") for c in df.columns]
    df = df.replace({
        r"s\ufffdb\.": "sáb.",
        r"(\d+)\ufffd": r"\1ª",
        r"AISP \ufffd ": "AISP – ",
        r"Igua\ufffdu": "Iguaçu",
        r"S\ufffdo Jos\ufffd": "São José",
    }, regex=True)

# 5. Pega 5.000 registros aleatórios
n_amostra = min(qtd_registros, len(df))
df_amostra = df.sample(n=n_amostra)

# 6. Salva o novo arquivo em UTF-8 com BOM (abre perfeitamente no VS Code e Excel)
df_amostra.to_csv(arquivo_saida, sep="\t", index=False, encoding="utf-8-sig")

print(f"Concluído! {len(df_amostra)} registros salvos em '{arquivo_saida}'.")