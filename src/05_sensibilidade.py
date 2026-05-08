"""
Análise de sensibilidade do vetor satélite a (Monte Carlo).

Motivação:
    A subnotificação de CAT no Brasil varia de ~19% (média nacional INSS)
    a 50–70% em setores com alta informalidade ou trabalho temporário
    (agropecuária, construção, domésticos). Este script propaga essa
    incerteza no vetor a e mede a robustez do ranking de quadrantes.

Procedimento:
    1. Para cada iteração k = 1..N_ITER, gera ε ~ LogNormal(0, σ²)
       multiplicativo com σ = 0.20 (≈ ±20% em escala log).
    2. Recalcula a* = a · ε, f* = a* · L, quadrante.
    3. Reporta para cada setor: probabilidade de permanecer no quadrante
       "Setor-chave de risco", percentil 5/50/95 de f.

Saídas:
    outputs/tables/sensibilidade.csv — sumário por setor
    outputs/figures/sensibilidade_pegada.pdf — boxplot da pegada
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
OUT_TABLE = ROOT / "outputs" / "tables" / "sensibilidade.csv"
OUT_FIG = ROOT / "outputs" / "figures" / "sensibilidade_pegada.pdf"

N_ITER = 1000
SIGMA_LOG = 0.20           # ≈ ±20% multiplicativo
SEED = 2026

OXBLOOD = "#6e1f1c"
INK = "#1a1612"


def main() -> None:
    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)

    Z, A, L, X, Y, sectors, source_io = load_io_data()
    CAT, source_cat = load_accidents()

    print(f"[05_sens] MIP-ES fonte: {source_io}")
    print(f"[05_sens] CAT fonte:    {source_cat}")
    print(f"[05_sens] iterações:    {N_ITER}, σ_log={SIGMA_LOG}")

    X_safe = np.where(X <= 0, MIN_PRODUCTION_THRESHOLD, X)
    a_base = CAT / X_safe
    f_base = a_base @ L
    L_grand_mean = L.mean()
    U_backward = L.sum(axis=0) / N_SETORES / L_grand_mean

    a_mean_base = float(a_base.mean())
    U_mean = float(U_backward.mean())

    rng = np.random.default_rng(SEED)
    f_samples = np.zeros((N_ITER, N_SETORES))
    is_chave = np.zeros((N_ITER, N_SETORES), dtype=bool)

    for k in range(N_ITER):
        eps = rng.lognormal(mean=0.0, sigma=SIGMA_LOG, size=N_SETORES)
        a_pert = a_base * eps
        f_pert = a_pert @ L
        f_samples[k] = f_pert
        a_med_pert = float(a_pert.mean())
        is_chave[k] = (a_pert > a_med_pert) & (U_backward > U_mean)

    p05 = np.percentile(f_samples, 5, axis=0)
    p50 = np.percentile(f_samples, 50, axis=0)
    p95 = np.percentile(f_samples, 95, axis=0)
    prob_chave = is_chave.mean(axis=0)
    cv = f_samples.std(axis=0) / np.where(p50 > 0, p50, 1.0)

    df = sectors.copy()
    df["a_base"] = a_base
    df["f_base"] = f_base
    df["f_p05"] = p05
    df["f_p50"] = p50
    df["f_p95"] = p95
    df["f_cv"] = cv
    df["prob_setor_chave"] = prob_chave

    df_sorted = df.sort_values("prob_setor_chave", ascending=False)
    df_sorted.to_csv(OUT_TABLE, index=False)

    print(f"[05_sens] tabela     -> {OUT_TABLE}")
    print(f"[05_sens] setores com prob_chave > 0.5:")
    for _, r in df_sorted[df_sorted["prob_setor_chave"] > 0.5].iterrows():
        print(f"  {r.codigo}  prob={r.prob_setor_chave:.2f}  f={r.f_base:.3f}  CV={r.f_cv:.3f}  {r['nome'][:50]}")

    # Boxplot da pegada — top-15 setores por f mediana
    top_idx = np.argsort(-p50)[:15]
    fig, ax = plt.subplots(figsize=(9.0, 6.0))
    data = [f_samples[:, i] for i in top_idx]
    labels = [str(sectors.loc[i, "codigo"]) for i in top_idx]
    bp = ax.boxplot(
        data, vert=False, tick_labels=labels, patch_artist=True,
        boxprops=dict(facecolor="#f0e8d8", edgecolor=INK, linewidth=0.6),
        medianprops=dict(color=OXBLOOD, linewidth=1.4),
        whiskerprops=dict(color=INK, linewidth=0.6),
        capprops=dict(color=INK, linewidth=0.6),
        flierprops=dict(marker="o", markersize=2, markerfacecolor=INK, markeredgecolor="none"),
    )
    ax.set_xlabel(r"Pegada $f_j$ (CATs / R\$ milhão de demanda final)", fontsize=11, style="italic")
    ax.set_ylabel("Setor (código IJSN)", fontsize=11, style="italic")
    ax.set_title(
        rf"Sensibilidade da pegada $f_j$ a perturbações em $a_j$ (Monte Carlo, N={N_ITER}, $\sigma_{{\log}}$={SIGMA_LOG})",
        pad=10, fontsize=11, color=INK,
    )
    ax.grid(axis="x", alpha=0.18, lw=0.4)
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[05_sens] boxplot    -> {OUT_FIG}")


if __name__ == "__main__":
    main()
