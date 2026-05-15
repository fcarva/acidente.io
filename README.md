# acidente.io — Análise Insumo-Produto de Acidentes de Trabalho no Espírito Santo

> Pipeline reprodutível para mensurar o impacto sistêmico dos acidentes de
> trabalho na economia capixaba a partir da Matriz Insumo-Produto do Espírito
> Santo (MIP-ES 2015, IJSN) e dos microdados de Comunicação de Acidente de
> Trabalho (CAT) do SmartLab/MTE — com comparativo formal contra o Brasil
> usando a MIP-Brasil 2015 (IBGE, 67 atividades) e o AEAT-2015 nacional.

---

## Descrição do Projeto

Este repositório implementa um pipeline computacional baseado no modelo de
**Análise Insumo-Produto (AIP) de Leontief** para investigar quais setores
produtivos do Espírito Santo apresentam maior risco ocupacional direto e
indireto. O projeto combina:

- **MIP-ES 2015** (IJSN): matrizes de consumo intermediário (Z), demanda
  final (Y) e produção bruta (X) com 35 setores.
- **SmartLab/MTE — CAT 2015**: microdados de acidentes típicos de trabalho
  filtrados para o Espírito Santo.
- **AEAT-2015** (Anuário Estatístico de Acidentes do Trabalho): tabela 19.1
  (CAT por CNAE 4-dígitos) para a UF Espírito Santo e para o Brasil.
- **MIP-Brasil 2015** (IBGE, nível 67): VBP e matrizes A/L nacionais usadas
  como benchmark no comparativo BR×ES.

Os resultados identificam **setores-chave de risco** e **propagadores
estruturais**; estimam, via Método de Extração Hipotética (HEM), o impacto
de cada setor sobre o total de acidentes; e, via decomposição **shift-share**,
separam o diferencial de intensidade ES×Brasil em efeitos de composição,
intensidade e interação.

---

## Fontes de Dados

| Arquivo | Fonte | Descrição |
|---|---|---|
| `data/raw/MIP_ES_2015.xlsm` | IJSN | MIP-ES 2015 (Z, Y, X — 35 setores, R$ mil) |
| `data/raw/Matriz_Insumo-Produto_MIP_35x35.xlsx` | IJSN | Matriz oficial 35×35 (fonte primária de A e L) |
| `data/raw/aeat15_es_subsecao_a.csv` | MTE/AEAT | CAT por CNAE 4-dig — UF Espírito Santo |
| `data/raw/smartlab_cat_2015.csv` | SmartLab / MTE | Microdados CAT — Espírito Santo |
| `data/raw/de_para_cnae_setores.csv` | Elaboração própria | De-para CNAE 2.0 → 35 setores MIP-ES |
| `data/raw/br/MIP_Brasil_2015_N67.xls` | IBGE | MIP-Brasil 2015 (67 atividades) |
| `data/raw/br/aeat15_br/15Act01_*.xls` | MTE/AEAT | CAT por CNAE 4-dig — Brasil (667 códigos) |

Links oficiais: [IBGE](https://www.ibge.gov.br/) · [IJSN](https://ijsn.es.gov.br/) ·
[SmartLab](https://smartlabbr.org/) · [AEAT/MTE](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/inspecao-do-trabalho/seguranca-e-saude-no-trabalho/sst-estatisticas).

---

## Arcabouço Matemático

### Modelo de Leontief

**Coeficientes técnicos** $\quad A = Z \cdot \hat{X}^{-1}$

**Inversa de Leontief** $\quad L = (I - A)^{-1}$

### Extensão Social — Acidentes de Trabalho

**Intensidade direta** $\quad a_i = \dfrac{CAT_i}{X_i}$

**Pegada de acidentes** $\quad \mathbf{f}' = \mathbf{a}' \cdot L$

### Índice de Rasmussen-Hirschman (encadeamento para trás)

$$U_j = \frac{\sum_i l_{ij}}{\bar{l}}$$

### Método de Extração Hipotética (HEM)

Para cada setor $k$, zera-se a linha e coluna $k$ de $A$:

$$\Delta CAT_k = \mathbf{a}'X - \mathbf{a}'X^*_k, \qquad X^*_k = (I - A^*_k)^{-1}\mathbf{Y}$$

### Decomposição shift-share ES × Brasil

A diferença na intensidade agregada $\bar{a}^{ES} - \bar{a}^{BR}$ decompõe-se em:

$$\Delta\bar{a} \;=\; \underbrace{\sum_j (s_j^{ES} - s_j^{BR})\,a_j^{BR}}_{\text{composição}}
\;+\; \underbrace{\sum_j s_j^{BR}(a_j^{ES} - a_j^{BR})}_{\text{intensidade}}
\;+\; \underbrace{\sum_j (s_j^{ES} - s_j^{BR})(a_j^{ES} - a_j^{BR})}_{\text{interação}}$$

onde $s_j = x_j / \sum_k x_k$ é a participação setorial no VBP.

### Classificação por Quadrantes de Risco

| Condição | Perfil |
|---|---|
| $a > \bar{a}$ e $U_j > \bar{U}_j$ | **Setor-chave de risco** |
| $a \leq \bar{a}$ e $U_j > \bar{U}_j$ | **Propagador estrutural** |
| $a > \bar{a}$ e $U_j \leq \bar{U}_j$ | **Risco localizado** |
| $a \leq \bar{a}$ e $U_j \leq \bar{U}_j$ | **Residual** |

### Análise de sensibilidade

Monte Carlo log-normal sobre $a_j$ ($N = 1{,}000$, $\sigma_{\log} = 0{,}20$)
para avaliar a estabilidade das pegadas e da classificação por quadrantes.

---

## Estrutura do Pipeline

O pipeline está organizado em scripts numerados em `src/`, executados em
sequência por `run_pipeline.sh`:

| Etapa | Script | Função |
|---|---|---|
| 0 | `src/00_extract_aeat.py` | Extrai tabela 19.1 do AEAT-2015 (ES) |
| 1 | `src/01_data_prep.py` | Agrega CAT por CNAE → 35 setores MIP-ES |
| 2 | `src/02_io_model.py` | Calcula $A$, $L$, $\mathbf{a}$, $\mathbf{f}$, $U_j$ e quadrantes |
| 3 | `src/03_hem_analysis.py` | Extração hipotética setor a setor |
| 4 | `src/04_viz.py` | Gráfico de quadrantes de risco |
| 5 | `src/05_sensibilidade.py` | Monte Carlo log-normal sobre $a_j$ |
| 6 | `src/06_article_builder.py` | Geração automática do artigo LaTeX |
| 7 | `src/07_compare_br_es.py` | Comparativo formal ES × Brasil (shift-share + contrafactual) |

`src/common_io.py` concentra utilitários compartilhados de I/O.

### Camada multi-agente (opcional)

`agents/` mantém uma orquestração alternativa em três agentes
(Data Engineer, IO Specialist, Data Viz) coordenados por
`agents/orchestrator.py`, útil para execuções programáticas em pipelines
de orquestração externos.

---

## Estrutura de Diretórios

```
acidente.io/
├── src/                      # Pipeline principal (00..07 + common_io)
├── agents/                   # Camada multi-agente alternativa
├── data/
│   ├── raw/                  # MIP-ES, AEAT-ES, SmartLab
│   │   └── br/               # MIP-Brasil 67, AEAT nacional
│   └── processed/            # Matrizes limpas + comparativo BR×ES
├── notebooks/                # Notebooks de análise interativa
├── outputs/
│   ├── figures/              # quadrante_risco_es.pdf, sensibilidade_pegada.pdf
│   └── tables/               # resultados_principais.xlsx, tabelas_resultados.xlsx
├── latex/                    # pegada_acidentes_es.{tex,pdf} (gerado pela etapa 6)
├── docs/                     # Auditorias e notas técnicas
├── run_pipeline.sh           # Pipeline ponta-a-ponta
├── requirements.txt
└── README.md
```

---

## Instalação

```bash
git clone https://github.com/fcarva/acidente.io.git
cd acidente.io
pip install -r requirements.txt
```

> Python ≥ 3.11 recomendado. Para o comparativo BR×ES, `xlrd` é necessário
> (já listado em `requirements.txt`) por causa dos arquivos `.xls` do AEAT
> e da MIP-Brasil 2015 do IBGE.

---

## Uso

### Pipeline completo

```bash
./run_pipeline.sh
```

Executa as etapas 0–6 em sequência. A etapa 7 (comparativo BR×ES) é
executada separadamente:

```bash
python3 src/07_compare_br_es.py
```

### Execução interativa

```bash
jupyter notebook notebooks/analise_mip_es.ipynb
```

### Saídas

- `outputs/figures/quadrante_risco_es.pdf` — mapa de quadrantes de risco
- `outputs/figures/sensibilidade_pegada.pdf` — bandas de incerteza Monte Carlo
- `outputs/tables/resultados_principais.xlsx` — tabelas principais
- `data/processed/comparativo_br_es.csv` — comparativo setorial ES × Brasil
- `data/processed/comparativo_br_es_summary.csv` — agregados e shift-share
- `latex/pegada_acidentes_es.pdf` — artigo completo (compilado)

---

## Licença

Distribuído sob a licença **MIT**. Consulte o arquivo `LICENSE` para detalhes.

---

*Desenvolvido para fins de pesquisa acadêmica sobre saúde e segurança do
trabalho na economia capixaba.*
