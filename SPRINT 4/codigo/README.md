# Analisador de Ocorrências Criminais — versão mínima

## Requisitos
- Python 3.10 ou superior
- pandas

## Instalação
```bash
pip install -r pandas>=2.0
```

## Execução
Coloque o arquivo `.tsv` em um local acessível e execute:

```bash
python main.py
```

No menu, escolha `1` para importar o TSV e informe seu caminho.
Escolha `2` para imprimir todos os registros carregados.

## Estrutura esperada do TSV
O arquivo deve possuir cabeçalho e as colunas nesta ordem:

`Ano`, `Mês`, `Dia`, `Dia da Semana`, `Hora`, `AISP`, `Município`, `Bairro`, `Natureza`, `Ambiente`.

O separador deve ser tabulação (TAB).
