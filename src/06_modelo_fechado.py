"""
Modelo de Leontief fechado (Type II) — endogeniza o consumo das famílias.

Formulação:
    A_bar = [[ A      h ]]   onde
            [[ w'     0 ]]
        h_i = consumo das famílias do setor i / Σ_j (w_j · X_j)
        w_j = remunerações pagas pelo setor j / X_j  ≈ VA_j / X_j (proxy)

    L_bar = (I_(n+1) − A_bar)^{-1}        # (36×36)
    f_typeII = a_aug' L_bar               # com a_aug = [a, 0]

Decomposição da pegada estrutural:
    direto    = a
    indireto  = (a' L) − a              (Type I − direto)
    induzido  = f_typeII − (a' L)       (Type II − Type I)

⚠ Aproximação:
    Sem dados explícitos de remunerações no XLSX IJSN, usamos VA/X como
    proxy do coeficiente w_j (VA_j = X_j − Σ_i Z[i,j]). Isso superestima
    o efeito induzido pois inclui Excedente Operacional Bruto e impostos
    sobre produção que não retornam às famílias na mesma proporção.

Saídas:
    outputs/tables/modelo_fechado.csv   (35 linhas, decomposição por setor)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from common_io import (
    MIN_PRODUCTION_THRESHOLD,
    N_SETORES,
    load_accidents,
    load_io_data,
    load_y_components,
    safe_inverse,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_TABLE = ROOT / "outputs" / "tables" / "modelo_fechado.csv"


def main() -> None:
    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)

    Z, A, L, X, Y, sectors, source_io = load_io_data()
    CAT, source_cat = load_accidents()
    y_comp = load_y_components()

    if y_comp is None:
        raise RuntimeError(
            "Componentes de Y não disponíveis. Necessário XLSX oficial IJSN com "
            "Tabelas 03 (DOMÉSTICOS) e 10 (D matrix)."
        )

    print(f"[06_typeII] MIP-ES fonte: {source_io}")
    print(f"[06_typeII] CAT fonte:    {source_cat}")

    X_safe = np.where(X <= 0, MIN_PRODUCTION_THRESHOLD, X)
    a = CAT / X_safe
    f_typeI = a @ L                 # pegada Type I (modelo aberto)

    # Coeficiente direto de consumo das famílias por setor
    h_setor = y_comp["h_familias"].to_numpy(dtype=float)
    h_setor_total = float(h_setor.sum())
    if h_setor_total <= 0:
        raise RuntimeError("Soma de h_familias <= 0; verificar extração de Y.")

    # Coluna de consumo: h_i / Σ w·X (renda total das famílias).
    # Aproximação: renda das famílias = soma das remunerações ≈ VA total
    VA = X - Z.sum(axis=0)              # valor adicionado por setor (proxy)
    VA = np.maximum(VA, 0.0)
    renda_total = float(VA.sum())
    if renda_total <= 0:
        raise RuntimeError("VA total <= 0; modelo Type II não estimável.")

    # Linha de remunerações: w_j = VA_j / X_j (fração da renda que vai às famílias)
    w = VA / X_safe                       # ω_j em [0,1]
    h_col = h_setor / renda_total         # vetor consumo normalizado

    # Construir A_bar (36×36)
    n = N_SETORES
    A_bar = np.zeros((n + 1, n + 1))
    A_bar[:n, :n] = A
    A_bar[:n, n] = h_col           # coluna n+1 = consumo das famílias
    A_bar[n, :n] = w                # linha n+1 = coeficientes de renda
    # A_bar[n, n] = 0  (já zero)

    # Verificar invertibilidade (raio espectral < 1 para convergência)
    eigvals = np.linalg.eigvals(A_bar)
    rho = float(np.max(np.abs(eigvals)))
    if rho >= 1.0:
        raise RuntimeError(
            f"A_bar com raio espectral {rho:.4f} >= 1 — modelo Type II não convergente. "
            "Possível: w (proxy VA/X) supera a fração efetiva da renda; usar dados de "
            "remunerações da RAIS para refinar."
        )
    print(f"[06_typeII] raio espectral A_bar = {rho:.4f} (deve < 1)")

    L_bar = np.linalg.inv(np.eye(n + 1) - A_bar)
    a_aug = np.concatenate([a, [0.0]])
    f_typeII_aug = a_aug @ L_bar
    f_typeII = f_typeII_aug[:n]    # apenas componentes setoriais

    direto = a
    indireto = f_typeI - a
    induzido = f_typeII - f_typeI

    # Multiplicador de produção Type II
    e_aug_col = np.concatenate([np.zeros(n), [0.0]])  # not used for output
    m_prod_II = L_bar[:n, :n].sum(axis=0)

    df = sectors[["codigo", "nome"]].copy()
    df["X_i"] = X
    df["a_direto"] = direto
    df["f_typeI_aberto"] = f_typeI
    df["f_typeII_fechado"] = f_typeII
    df["amplif_typeII_sobre_typeI"] = np.where(f_typeI > 0, f_typeII / np.where(f_typeI > 0, f_typeI, 1.0), np.nan)
    df["componente_direto"] = direto
    df["componente_indireto"] = indireto
    df["componente_induzido"] = induzido
    df["share_induzido"] = np.where(f_typeII > 0, induzido / np.where(f_typeII > 0, f_typeII, 1.0), 0.0)
    df["multiplicador_prod_typeII"] = m_prod_II

    df_sorted = df.sort_values("f_typeII_fechado", ascending=False)
    df_sorted.to_csv(OUT_TABLE, index=False)

    print(f"[06_typeII] tabela -> {OUT_TABLE}")
    print(f"[06_typeII] médias: f_typeI={f_typeI.mean():.4f}  f_typeII={f_typeII.mean():.4f}  "
          f"amplificação Type II/Type I = {(f_typeII/np.where(f_typeI>0,f_typeI,1)).mean():.2f}")
    print(f"[06_typeII] indireto/total médio:  {((f_typeI-a)/np.where(f_typeII>0,f_typeII,1)).mean()*100:.1f}%")
    print(f"[06_typeII] induzido/total médio:  {(induzido/np.where(f_typeII>0,f_typeII,1)).mean()*100:.1f}%")


if __name__ == "__main__":
    main()
