
import pandas as pd
from pathlib import Path

# ============================================================
# CONFIGURAÇÕES
# ============================================================

arquivo_entrada = Path("dados_tsv_parana_2026.tsv")
arquivo_saida = Path("dados_saida_500k.tsv")

qtd_registros = 490000
SEED = 42  # Permite reproduzir a mesma amostra

# ============================================================
# 1. LEITURA DO ARQUIVO
# ============================================================

df = None
codificacoes = ["utf-8-sig", "cp1252", "latin1"]

for encoding in codificacoes:
    try:
        df = pd.read_csv(
            arquivo_entrada,
            sep="\t",
            encoding=encoding,
            dtype=str,
            keep_default_na=False,
            on_bad_lines="error"
        )
        print(f"Arquivo lido com codificação: {encoding}")
        break

    except UnicodeDecodeError:
        continue

if df is None:
    raise ValueError("Não foi possível identificar a codificação.")

# ============================================================
# 2. LIMPEZA DOS CABEÇALHOS
# ============================================================

df.columns = (
    df.columns
    .str.strip()
    .str.replace("\ufeff", "", regex=False)
)

# Remove colunas desnecessárias
df = df.drop(
    columns=["ID", "Tipo Natureza"],
    errors="ignore"
)

# ============================================================
# 3. LIMPEZA DOS DADOS
# ============================================================

# Remove espaços extras nas extremidades
for coluna in df.columns:
    df[coluna] = df[coluna].str.strip()

# Substitui caracteres de substituição por vazio
df = df.replace("\ufffd", "", regex=False)

# Remove caracteres de controle que podem prejudicar o TSV
for coluna in df.columns:
    df[coluna] = (
        df[coluna]
        .str.replace(r"[\r\n\t]+", " ", regex=True)
        .str.replace(r"\s{2,}", " ", regex=True)
        .str.strip()
    )

# Preenche campos sem informação com o rótulo "SEM_DADO"
# Inclui células vazias ou que contenham somente espaços.
# Converte células vazias ou compostas apenas por espaços em valores ausentes
df = df.replace(r"^\\s*$", pd.NA, regex=True)

# Garante o preenchimento de todos os valores ausentes em todas as colunas
df = df.fillna("SEM_DADO")

# ============================================================
# 3.1. TRATAMENTO DE DADOS AUSENTES
# ============================================================

# Representações de ausência de informação
valores_ausentes = [
    "",
    "N/A",
    "NA",
    "NAO INFORMADO",
    "NÃO INFORMADO",
    "NULL",
    "NONE",
    "NAN"
]

for coluna in df.columns:
    df[coluna] = df[coluna].str.strip()

    df[coluna] = df[coluna].apply(
        lambda valor: "SEM_DADO"
        if valor.upper() in valores_ausentes
        else valor
    )

# ============================================================
# 4. VERIFICAÇÃO DA ESTRUTURA
# ============================================================

print("\nEstrutura do arquivo:")
print(f"Registros: {len(df)}")
print(f"Colunas: {len(df.columns)}")
print(f"Nomes: {list(df.columns)}")

# ============================================================
# 5. AMOSTRAGEM ALEATÓRIA
# ============================================================

n_amostra = min(qtd_registros, len(df))

df_amostra = df.sample(
    n=n_amostra,
    random_state=SEED
).reset_index(drop=True)

# ============================================================
# 6. EXPORTAÇÃO TSV
# ============================================================

df_amostra.to_csv(
    arquivo_saida,
    sep="\t",
    index=False,
    encoding="utf-8-sig",
    lineterminator="\n",
    quoting=3,
    quotechar='"'
)

# ============================================================
# 7. VERIFICAÇÃO FINAL
# ============================================================

# Reabre o arquivo para verificar se a estrutura foi preservada
df_teste = pd.read_csv(
    arquivo_saida,
    sep="\t",
    encoding="utf-8-sig",
    dtype=str,
    keep_default_na=False
)

assert list(df_teste.columns) == list(df_amostra.columns)
assert len(df_teste) == len(df_amostra)
assert df_teste.shape[1] == df_amostra.shape[1]
# Verifica se ainda existe alguma célula vazia ou somente com espaços
assert not df_teste.apply(
    lambda coluna: coluna.str.fullmatch(r"\\s*", na=False)
).any().any(), "Ainda existem células vazias no arquivo de saída."

print("\n======================================")
print("          PROCESSAMENTO OK")
print("======================================")
print(f"Arquivo: {arquivo_saida}")
print(f"Registros: {len(df_teste)}")
print(f"Colunas: {len(df_teste.columns)}")
print(f"Tamanho: {arquivo_saida.stat().st_size / 1024:.2f} KB")
print("Separador: TAB")
print("Codificação: UTF-8 com BOM")
print("Integridade estrutural: OK")
