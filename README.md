# acidente.io — Análise Insumo-Produto de Acidentes de Trabalho no Espírito Santo

> Pipeline multi-agente para mensuração do impacto sistêmico dos acidentes
> laborais típicos na economia capixaba, com base na Matriz Insumo-Produto do
> Espírito Santo de 2015 (MIP-ES 2015) e nos microdados de Comunicação de
> Acidente de Trabalho (CAT) do SmartLab/MTE.

---

## Descrição do Projeto

Este repositório implementa um pipeline computacional baseado no modelo de
**Análise Insumo-Produto (AIP) de Leontief** para investigar quais setores
produtivos do Espírito Santo apresentam maior risco ocupacional direto e
indireto.  O projeto combina:

- **MIP-ES 2015** (UFES / IJSN): matrizes de consumo intermediário (Z),
  demanda final (Y) e produção bruta (X) com 35 setores.
- **SmartLab/MTE -- CAT 2015**: microdados de acidentes típicos de trabalho
  (Comunicação de Acidente de Trabalho) filtrados para o Espírito Santo.

Os resultados identificam setores-chave de risco, propagadores estruturais e
estimam, via Método de Extração Hipotética, o impacto que cada setor exerce
sobre o total de acidentes na economia.

---

## Fontes de Dados

| Arquivo | Fonte | Descrição |
|---|---|---|
| `data/raw/MIP_ES_2015.xlsm` | UFES / IJSN | Matrizes Z, Y e X (35 setores, R$ mil, 2015) |
| `data/raw/smartlab_cat_2015.csv` | SmartLab / MTE | Microdados CAT -- acidentes típicos |
| `data/raw/de_para_cnae_setores.csv` | Elaboração própria | De-para CNAE 2.0 → setores MIP (35) |

Links oficiais:
- IBGE: <https://www.ibge.gov.br/>
- IJSN: <https://ijsn.es.gov.br/>
- SmartLab: <https://smartlabbr.org/>

---

## Arcabouço Matemático

### Modelo de Leontief

**Matriz de coeficientes técnicos**

$$A = Z \cdot \hat{X}^{-1}$$

onde $\hat{X}$ é a matriz diagonal com a produção bruta setorial.

**Inversa de Leontief**

$$L = (I - A)^{-1}$$

### Extensão Social -- Acidentes de Trabalho

**Intensidade direta de acidentes**

$$a_i = \frac{CAT_i}{X_i}$$

**Vetor multiplicador de pegada de acidentes**

$$\mathbf{f}' = \mathbf{a}' \cdot L$$

### Índice de Rasmussen-Hirschman (Encadeamento Retroativo)

$$U_j = \frac{\sum_i l_{ij}}{\bar{l}}$$

onde $\bar{l}$ é a média global de todos os elementos de $L$.

### Método de Extração Hipotética (HEM)

Para cada setor $k$, zera-se a linha e coluna $k$ de $A$:

$$\Delta CAT_k = \mathbf{a}'X - \mathbf{a}'X^*_k$$

$$X^*_k = (I - A^*_k)^{-1} \mathbf{Y}$$

### Classificação por Quadrantes de Risco

| Condição | Perfil |
|---|---|
| $a > \bar{a}$ e $U_j > \bar{U}_j$ | **Setor-chave de Risco** |
| $a \leq \bar{a}$ e $U_j > \bar{U}_j$ | **Propagador Estrutural** |
| $a > \bar{a}$ e $U_j \leq \bar{U}_j$ | **Risco Localizado** |
| $a \leq \bar{a}$ e $U_j \leq \bar{U}_j$ | **Residual** |

---

## Arquitetura Multi-Agente

```
Orchestrator (agents/orchestrator.py)
│
├── Agente 1 -- Data Engineer (agents/data_engineer.py)
│   ├── 1.1 Extração MIP (Z, Y, X)
│   ├── 1.2 Ingestão SmartLab CAT
│   └── 1.3 Compatibilização CNAE → 35 setores
│   └── [Gate] validate_dimensions()
│
├── Agente 2 -- IO Specialist (agents/io_specialist.py)
│   ├── 2.1 Leontief: A, L
│   ├── 2.2 Extensão social: a, f
│   ├── 2.3 Rasmussen-Hirschman: U_j
│   └── 2.4 HEM: delta_CAT
│
└── Agente 3 -- Data Viz (agents/data_viz.py)
    ├── 3.1 DataFrame de resultados + quadrantes
    ├── 3.2 Gráfico de dispersão (PDF, 300 dpi)
    └── 3.3 Exportação Excel (3 abas)
```

---

## Estrutura de Diretórios

```
acidente.io/
├── agents/
│   ├── __init__.py
│   ├── data_engineer.py   # Agente 1
│   ├── io_specialist.py   # Agente 2
│   ├── data_viz.py        # Agente 3
│   └── orchestrator.py    # Manager
├── data/
│   ├── raw/               # Arquivos-fonte (não versionados)
│   └── processed/         # Matrizes limpas
├── notebooks/
│   └── analise_mip_es.ipynb
├── outputs/
│   ├── figures/           # quadrante_risco_es.pdf
│   └── tables/            # tabelas_resultados.xlsx
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

> Recomenda-se Python ≥ 3.11 e o uso de um ambiente virtual (`venv` ou `conda`).

---

## Uso

### Execução completa via linha de comando

```bash
python agents/orchestrator.py
```

### Execução interativa (Jupyter)

```bash
jupyter notebook notebooks/analise_mip_es.ipynb
```

### Uso programático

```python
from agents.orchestrator import run_pipeline

df = run_pipeline(
    mip_path="data/raw/MIP_ES_2015.xlsm",
    cat_path="data/raw/smartlab_cat_2015.csv",
    de_para_path="data/raw/de_para_cnae_setores.csv",
    sector_names=["Agropecuária", "Petróleo e gás", ...],  # 35 nomes
)
print(df.nlargest(10, "f"))
```

Os outputs são gravados automaticamente em:
- `outputs/figures/quadrante_risco_es.pdf`
- `outputs/tables/tabelas_resultados.xlsx`

---

## Licença

Este projeto é distribuído sob a licença **MIT**.  
Consulte o arquivo `LICENSE` para mais detalhes.

---

*Desenvolvido para fins de pesquisa acadêmica sobre saúde e segurança do
trabalho na economia capixaba.*
