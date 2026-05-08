"""
Modelo de Leontief para a MIP-ES 2015 + extensão social de acidentes.

Operações (Miller & Blair, 2009):
    A = Z · diag(X)^{-1}
    L = (I − A)^{-1}
    a = CAT / X
    f' = a' · L                    (pegada estrutural — Leontief satellite)
    U_j = (Σ_i l_ij) / (Σ_ij l_ij / n)   (Rasmussen-Hirschman backward)
    m_j = Σ_i l_ij                 (multiplicador de produção)

Validações:
    || (I − A) · L − I ||_F  <  1e-8     (Frobenius)
    Não há divisão por X_j ≤ 0 sem proteção explícita.

Saídas em outputs/tables/:
    resultados_principais.csv   (35 linhas, todos os indicadores)
    resultados_principais.xlsx  (mesmo conteúdo + abas Z, A, L)
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
)

ROOT = Path(__file__).resolve().parents[1]
OUT_TABLES = ROOT / "outputs" / "tables"
OUT_CSV = OUT_TABLES / "resultados_principais.csv"
OUT_XLSX = OUT_TABLES / "resultados_principais.xlsx"


def main() -> None:
    OUT_TABLES.mkdir(parents=True, exist_ok=True)

    Z, A, L, X, Y, sectors, source_io = load_io_data()
    CAT, source_cat = load_accidents()

    print(f"[02_io_model] MIP-ES fonte: {source_io}")
    print(f"[02_io_model] CAT fonte:    {source_cat}")

    X_safe = np.where(X <= 0, MIN_PRODUCTION_THRESHOLD, X)
    I = np.eye(N_SETORES)

    frobenius_err = np.linalg.norm((I - A) @ L - I, "fro")
    print(f"[02_io_model] || (I−A)·L − I ||_F = {frobenius_err:.2e}")
    if frobenius_err > FROBENIUS_TOLERANCE:
        raise RuntimeError(
            f"Erro Frobenius {frobenius_err:.2e} excede tolerância {FROBENIUS_TOLERANCE:.0e}."
        )

    a = CAT / X_safe                                 # intensidade direta
    f = a @ L                                        # pegada estrutural
    indireto = f - a
    with np.errstate(divide="ignore", invalid="ignore"):
        amplif = np.where(a > 0, f / np.where(a > 0, a, 1.0), np.nan)
        share_indireto = np.where(f > 0, indireto / np.where(f > 0, f, 1.0), 0.0)

    L_grand_mean = L.mean()
    if L_grand_mean == 0:
        raise RuntimeError("Média de L é zero — matriz Leontief degenerada.")
    U_backward = L.sum(axis=0) / N_SETORES / L_grand_mean
    U_forward = L.sum(axis=1) / N_SETORES / L_grand_mean
    m_producao = L.sum(axis=0)                       # multiplicador de produção

    # Multiplicador de emprego (Type I) e taxa CAT por trabalhador
    ocupacoes = sectors["ocupacoes"].to_numpy(dtype=float)
    e = ocupacoes / X_safe                           # coeficiente direto de emprego
    m_emprego = e @ L                                # multiplicador de emprego (Type I)
    a_per_trab = np.where(ocupacoes > 0, CAT / np.where(ocupacoes > 0, ocupacoes, 1.0), 0.0)
    f_per_trab = a_per_trab @ L                      # pegada por trabalhador exposto

    a_med = float(np.mean(a))
    U_med = float(np.mean(U_backward))

    def _quadrante(a_j: float, U_j: float) -> str:
        if a_j > a_med and U_j > U_med:
            return "Setor-chave de risco"
        if a_j <= a_med and U_j > U_med:
            return "Propagador estrutural"
        if a_j > a_med and U_j <= U_med:
            return "Risco localizado"
        return "Residual"

    df = sectors.copy()
    df["producao_X"] = X
    df["demanda_final_Y"] = Y
    df["acidentes_CAT"] = CAT
    df["intensidade_direta_a"] = a
    df["pegada_estrutural_f"] = f
    df["indireto_f_minus_a"] = indireto
    df["amplificacao_f_sobre_a"] = amplif
    df["share_indireto"] = share_indireto
    df["encadeamento_tras_U"] = U_backward
    df["encadeamento_frente_Uf"] = U_forward
    df["multiplicador_producao_m"] = m_producao
    df["intensidade_per_trab_a_tilde"] = a_per_trab
    df["pegada_per_trab_f_tilde"] = f_per_trab
    df["coef_emprego_e"] = e
    df["multiplicador_emprego_me"] = m_emprego
    df["quadrante"] = [
        _quadrante(a[i], U_backward[i]) for i in range(N_SETORES)
    ]

    df.to_csv(OUT_CSV, index=False)

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="resultados", index=False)
        pd.DataFrame(Z, index=sectors["codigo"], columns=sectors["codigo"]).to_excel(
            writer, sheet_name="Z"
        )
        pd.DataFrame(A, index=sectors["codigo"], columns=sectors["codigo"]).to_excel(
            writer, sheet_name="A"
        )
        pd.DataFrame(L, index=sectors["codigo"], columns=sectors["codigo"]).to_excel(
            writer, sheet_name="L"
        )

    print(f"[02_io_model] CSV  → {OUT_CSV}")
    print(f"[02_io_model] XLSX → {OUT_XLSX}")
    print(f"[02_io_model] médias para corte: ā={a_med:.4f}  Ū={U_med:.4f}")
    print(f"[02_io_model] CATs total:        {CAT.sum():,.0f}")
    print(f"[02_io_model] amplificação média f/a: {np.nanmean(amplif):.2f}")


if __name__ == "__main__":
    main()
