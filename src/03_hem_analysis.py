"""
Método de Extração Hipotética (HEM) — Dietzenbacher & Lahr (2013) /
Cella (1984), variante "complete extraction".

Para cada setor k = 1..35:
    A*_k tem linha k e coluna k zeradas
    L*_k = (I − A*_k)^{-1}
    X*_k = L*_k · Y                          (versão baseline)
    ΔCAT_k = a' · X − a' · X*_k

Variante de robustez (documentada como coluna adicional):
    Ŷ_k = Y com Y[k] = 0          → extração completa (Miller-Lahr)
    X̂*_k = L*_k · Ŷ_k
    ΔCAT_k_completo = a' · X − a' · X̂*_k

Saída: outputs/tables/extracao_hipotetica.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from common_io import (
    FROBENIUS_TOLERANCE,
    MIN_PRODUCTION_THRESHOLD,
    N_SETORES,
    load_accidents,
    load_io_data,
    safe_inverse,
)  # safe_inverse is reused for the per-k extraction

ROOT = Path(__file__).resolve().parents[1]
OUT_TABLE = ROOT / "outputs" / "tables" / "extracao_hipotetica.csv"


def main() -> None:
    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)

    Z, A, L, X, Y, sectors, source_io = load_io_data()
    CAT, source_cat = load_accidents()

    print(f"[03_hem] MIP-ES fonte: {source_io}")
    print(f"[03_hem] CAT fonte:    {source_cat}")

    X_safe = np.where(X <= 0, MIN_PRODUCTION_THRESHOLD, X)
    I = np.eye(N_SETORES)

    frob = np.linalg.norm((I - A) @ L - I, "fro")
    if frob > FROBENIUS_TOLERANCE:
        raise RuntimeError(f"Erro Frobenius da Leontief base = {frob:.2e}")

    a = CAT / X_safe
    cat_baseline = float(a @ X)

    rows: list[dict] = []
    for k in range(N_SETORES):
        A_star = A.copy()
        A_star[k, :] = 0.0
        A_star[:, k] = 0.0
        L_star = safe_inverse(I - A_star)

        # Variante baseline (mantém Y[k]) — exatamente o que o prompt pede.
        X_star = L_star @ Y
        cat_star = float(a @ X_star)
        delta_cat = cat_baseline - cat_star

        # Variante "complete extraction" (zera Y[k] também) — Miller & Lahr.
        Y_complete = Y.copy()
        Y_complete[k] = 0.0
        X_complete = L_star @ Y_complete
        cat_complete = float(a @ X_complete)
        delta_cat_complete = cat_baseline - cat_complete

        rows.append(
            {
                "codigo": sectors.loc[k, "codigo"],
                "nome": sectors.loc[k, "nome"],
                "acidentes_base": cat_baseline,
                "acidentes_pos_extracao": cat_star,
                "delta_cat": delta_cat,
                "delta_cat_pct": 100.0 * delta_cat / cat_baseline if cat_baseline else 0.0,
                "acidentes_pos_extracao_completa": cat_complete,
                "delta_cat_completa": delta_cat_complete,
                "delta_cat_completa_pct": 100.0 * delta_cat_complete / cat_baseline if cat_baseline else 0.0,
            }
        )

    df = pd.DataFrame(rows).sort_values("delta_cat_completa", ascending=False)
    df.to_csv(OUT_TABLE, index=False)

    print(f"[03_hem] resultados salvos em {OUT_TABLE}")
    print(f"[03_hem] total CAT base: {cat_baseline:,.0f}")
    print("[03_hem] top 5 por ΔCAT (extração completa):")
    for _, r in df.head(5).iterrows():
        print(f"  {r.codigo}  Δ={r.delta_cat_completa:>9.1f}  ({r.delta_cat_completa_pct:>5.1f}%)  {r.nome[:55]}")


if __name__ == "__main__":
    main()
