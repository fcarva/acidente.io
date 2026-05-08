"""
Campo de influência ponderado pela pegada de acidentes (Sonis & Hewings, 1989).

Definição clássica (não-ponderada):
    F_ij = Σ_k Σ_l l_ki · l_jl
         = (L · 1)[j] · (1' · L)[i]   (rank-1, simétrico)

Ponderação por pegada de acidentes — efeito de uma perturbação unitária
em a_ij sobre a pegada total ∑_k a_k · X_k:

    Φ_ij = (a' L)[i] · (L · 1)[j]

Interpretação: Φ_ij é proporcional ao impacto agregado em CATs que
adviria de uma perturbação unitária no coeficiente A[i,j]. Os pares com
maior Φ_ij são as relações intersetoriais cuja modificação (via política
ou choque tecnológico) teria maior impacto sobre o passivo de SST.

Saídas:
    outputs/tables/campo_influencia_top.csv (top 30 pares (i,j))
    outputs/tables/campo_influencia_matriz.csv (35x35)
    outputs/figures/campo_influencia.pdf (heatmap)
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
)

ROOT = Path(__file__).resolve().parents[1]
OUT_TOP = ROOT / "outputs" / "tables" / "campo_influencia_top.csv"
OUT_MATRIZ = ROOT / "outputs" / "tables" / "campo_influencia_matriz.csv"
OUT_FIG = ROOT / "outputs" / "figures" / "campo_influencia.pdf"

INK = "#1a1612"
OXBLOOD = "#6e1f1c"


def main() -> None:
    OUT_TOP.parent.mkdir(parents=True, exist_ok=True)
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)

    Z, A, L, X, Y, sectors, source_io = load_io_data()
    CAT, source_cat = load_accidents()

    print(f"[07_F]    MIP-ES fonte: {source_io}")
    print(f"[07_F]    CAT fonte:    {source_cat}")

    X_safe = np.where(X <= 0, MIN_PRODUCTION_THRESHOLD, X)
    a = CAT / X_safe
    f_pegada = a @ L                      # 1×N
    L_row_sum = L.sum(axis=1)             # N×1

    # Φ_ij = f_pegada[i] · L_row_sum[j]  → outer product
    Phi = np.outer(f_pegada, L_row_sum)
    n = N_SETORES

    # Sonis-Hewings clássico (não-ponderado): F = (1'L) · (L1)' (escalar simétrico)
    L_col_sum = L.sum(axis=0)
    F_classic = np.outer(L_col_sum, L_row_sum)

    # Top 30 pares (i,j) por Φ_ij ponderado
    flat_idx = np.argsort(-Phi.ravel())[:30]
    rows = []
    codigos = sectors["codigo"].tolist()
    nomes = sectors["nome"].tolist()
    for k in flat_idx:
        i, j = divmod(int(k), n)
        rows.append({
            "rank": len(rows) + 1,
            "i_origem": codigos[i],
            "i_nome": nomes[i],
            "j_destino": codigos[j],
            "j_nome": nomes[j],
            "phi_ponderado": float(Phi[i, j]),
            "f_origem": float(f_pegada[i]),
            "L_rowsum_destino": float(L_row_sum[j]),
            "A_ij_atual": float(A[i, j]),
        })
    pd.DataFrame(rows).to_csv(OUT_TOP, index=False)

    # Matriz completa
    pd.DataFrame(Phi, index=codigos, columns=codigos).to_csv(OUT_MATRIZ)

    print(f"[07_F]    tabela top -> {OUT_TOP}")
    print(f"[07_F]    matriz     -> {OUT_MATRIZ}")
    print(f"[07_F]    top 5 pares (i,j) por Φ_ij ponderado:")
    for r in rows[:5]:
        print(f"  #{r['rank']:>2}  i={r['i_origem']} → j={r['j_destino']}  "
              f"Φ={r['phi_ponderado']:.4f}  A={r['A_ij_atual']:.4f}")

    # Heatmap
    mpl.rcParams.update({"font.family": "serif", "font.size": 9})
    fig, ax = plt.subplots(figsize=(9.0, 7.5))
    im = ax.imshow(np.log10(Phi + 1e-9), cmap="magma_r", aspect="equal")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(codigos, rotation=90, fontsize=6, family="monospace")
    ax.set_yticklabels(codigos, fontsize=6, family="monospace")
    ax.set_xlabel(r"$j$ — destino do encadeamento", style="italic")
    ax.set_ylabel(r"$i$ — origem do encadeamento", style="italic")
    ax.set_title(
        r"Campo de influência ponderado: $\Phi_{ij}=(\mathbf{a}'L)_i\cdot(L\mathbf{1})_j$  "
        r"(escala $\log_{10}$)",
        pad=10, color=INK, fontsize=11,
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label(r"$\log_{10}(\Phi_{ij})$", style="italic")
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[07_F]    heatmap    -> {OUT_FIG}")


if __name__ == "__main__":
    main()
