# Pegada Estrutural de Acidentes de Trabalho no Espírito Santo (MIP-ES)

Repositório de apoio ao paper da disciplina de pós-graduação, com foco em reprodutibilidade computacional para análise de acidentes de trabalho via Matriz Insumo-Produto do Espírito Santo.

## Objetivo do Repositório

Implementar um pipeline reproduzível para calcular a **pegada estrutural de acidentes** com base na MIP-ES e em dados do SmartLab, gerando tabelas e figuras prontas para uso na redação acadêmica.

## Estrutura do Projeto

```text
mip-es-acidentes/
│
├── data/
│   ├── raw/
│   │   ├── MIP_ES_2015.xlsm
│   │   └── smartlab_cat_2015.csv
│   └── processed/
│       ├── de_para_cnae_mip.csv
│       └── vetor_acidentes_35_setores.csv
│
├── notebooks/
│   ├── 01_data_preparation.ipynb
│   ├── 02_io_model_and_multipliers.ipynb
│   ├── 03_hypothetical_extraction.ipynb
│   └── 04_visualizations.ipynb
│
├── outputs/
│   ├── tables/
│   └── figures/
│
├── .gitignore
├── requirements.txt
└── README.md
```

## Metodologia Implementada

- Modelo de Leontief
- Extensão social para acidentes de trabalho
- Índices de Rasmussen-Hirschman
- Método de Extração Hipotética (HEM)

## Fontes de Dados

- Matriz Insumo-Produto (IBGE/IJSN):
  - IBGE: <https://www.ibge.gov.br/>
  - IJSN: <https://ijsn.es.gov.br/>
- Acidentes de trabalho (SmartLab):
  - <https://smartlabbr.org/>

## Como Rodar

1. Crie e ative um ambiente Python (recomendado).
2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Execute os notebooks nesta ordem:
   1. `notebooks/01_data_preparation.ipynb`
   2. `notebooks/02_io_model_and_multipliers.ipynb`
   3. `notebooks/03_hypothetical_extraction.ipynb`
   4. `notebooks/04_visualizations.ipynb`

## Fluxo de Trabalho

1. Finalizar o `de_para` de compatibilização CNAE → 35 setores.
2. Rodar os notebooks sequencialmente.
3. Gerar tabelas em `outputs/tables/` e figuras em `outputs/figures/`.
4. Consumir os arquivos gerados diretamente no manuscrito (ex.: LaTeX).
