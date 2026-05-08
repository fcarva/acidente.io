"""
Decomposição da pegada de acidentes por componente de demanda final.

Identidade base:
    CAT_total = a' L Y_total
              = a' L (Y_h + Y_FBKF + Y_gov + Y_ISFLSF + Y_exp_ext + Y_exp_BR + Y_var)

Onde Y_c é o vetor de demanda final do componente c, agregado a 35
setores via a matriz de participação D · h_produto da Tabela 03 (XLSX
IJSN, "Oferta e demanda de produtos DOMÉSTICOS").

Cada parcela CAT_c = a' L Y_c representa o número de CATs no estado
"requeridas" para satisfazer a demanda do componente c — uma decomposição
de responsabilidade (consumer responsibility) sobre o passivo de SST.

Saídas:
    outputs/tables/decomposicao_demanda.csv      (componentes globais)
    outputs/tables/decomposicao_demanda_setor.csv (por setor × componente)
    outputs/figures/decomposicao_demanda.pdf      (barras empilhadas)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common_io import (
    MIN_PRODUCTION_THRESHOLD,
    N_SETORES,
    load_accidents,
    load_io_data,
    load_y_components,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_GLOBAL = ROOT / "outputs" / "tables" / "decomposicao_demanda.csv"
OUT_SETOR = ROOT / "outputs" / "tables" / "decomposicao_demanda_setor.csv"
OUT_FIG = ROOT / "outputs" / "figures" / "decomposicao_demanda.pdf"

INK = "#1a1612"
OXBLOOD = "#6e1f1c"

COMPONENTS = [
    ("h_familias", "Consumo das famílias", "#6e1f1c"),
    ("fbkf", "FBKF (investimento)", "#8a3633"),
    ("gov", "Consumo do governo", "#3a342c"),
    ("isflsf", "Consumo das ISFLSF", "#6b6359"),
    ("exp_brasil", "Exportações p/ Brasil", "#a78854"),
    ("exp_exterior", "Exportações p/ exterior", "#d4a85f"),
    ("var_estoque", "Variação de estoques", "#c8b890"),
]


def main() -> None:
    OUT_GLOBAL.parent.mkdir(parents=True, exist_ok=True)
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)

    Z, A, L, X, Y, sectors, source_io = load_io_data()
    CAT, source_cat = load_accidents()
    y_comp = load_y_components()

    if y_comp is None:
        raise RuntimeError(
            "load_y_components() retornou None. Necessário XLSX IJSN com Tabelas 03 e 10."
        )

    print(f"[08_dec]  MIP-ES fonte: {source_io}")
    print(f"[08_dec]  CAT fonte:    {source_cat}")

    X_safe = np.where(X <= 0, MIN_PRODUCTION_THRESHOLD, X)
    a = CAT / X_safe
    a_L = a @ L  # row vector (N,)

    cat_total_balanco = float(a_L @ Y)  # baseline via Y de balanço
    print(f"[08_dec]  CAT total via a'L·Y_balanço:  {cat_total_balanco:>10,.1f}")

    # Decomposição por componente
    rows_global = []
    by_setor = sectors[["codigo", "nome"]].copy()

    cat_componentes_sum = 0.0
    for col, label, _color in COMPONENTS:
        Y_c = y_comp[col].to_numpy(dtype=float)
        cat_c_total = float(a_L @ Y_c)
        cat_c_setor = a_L * Y_c    # contribuição por setor de origem da demanda
        rows_global.append(
            {"componente": label, "campo": col, "Y_componente": float(Y_c.sum()), "CATs_atribuidas": cat_c_total}
        )
        by_setor[f"CAT_{col}"] = cat_c_setor
        cat_componentes_sum += cat_c_total

    print(f"[08_dec]  CAT total via Σ componentes:   {cat_componentes_sum:>10,.1f}")
    print(f"[08_dec]  diff (componentes − balanço):  {cat_componentes_sum - cat_total_balanco:>10,.1f}")
    print(f"[08_dec]  CATs reais (vetor satélite):   {CAT.sum():>10,.1f}")

    df_global = pd.DataFrame(rows_global)
    df_global["share_pct"] = 100.0 * df_global["CATs_atribuidas"] / cat_componentes_sum
    df_global = df_global.sort_values("CATs_atribuidas", ascending=False)
    df_global.to_csv(OUT_GLOBAL, index=False)

    by_setor["CAT_total_decomp"] = sum(by_setor[f"CAT_{c}"] for c, _, _ in COMPONENTS)
    by_setor.to_csv(OUT_SETOR, index=False)

    print(f"[08_dec]  tabela global -> {OUT_GLOBAL}")
    print(f"[08_dec]  tabela setor  -> {OUT_SETOR}")
    print(f"[08_dec]  decomposição global:")
    for _, r in df_global.iterrows():
        print(f"  {r['componente'][:30]:30s}  {r['CATs_atribuidas']:>8,.1f}  "
              f"({r['share_pct']:>5.1f}%)  Y={r['Y_componente']:>10,.1f}")

    # Barras empilhadas: 15 setores com maior CAT_total_decomp
    top15 = by_setor.nlargest(15, "CAT_total_decomp").iloc[::-1]
    mpl.rcParams.update({"font.family": "serif", "font.size": 10})
    fig, ax = plt.subplots(figsize=(9.0, 7.0))
    y_pos = np.arange(len(top15))
    cumulative = np.zeros(len(top15))
    for col, label, color in COMPONENTS:
        vals = top15[f"CAT_{col}"].to_numpy(dtype=float)
        ax.barh(y_pos, vals, left=cumulative, color=color, edgecolor=INK, linewidth=0.4, label=label)
        cumulative += vals
    labels = [f"{r.codigo}  {str(r['nome'])[:30]}" for _, r in top15.iterrows()]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlabel(r"CATs atribuídas — $\mathbf{a}' L \cdot Y_c$ por componente $c$",
                  fontsize=11, style="italic")
    ax.set_title(
        "Decomposição da pegada por componente de demanda final  —  top 15 setores",
        pad=10, color=INK, fontsize=11,
    )
    ax.legend(loc="lower right", fontsize=8.5, frameon=False, ncol=2)
    ax.grid(axis="x", alpha=0.18, lw=0.4)
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[08_dec]  fig -> {OUT_FIG}")


if __name__ == "__main__":
    main()
