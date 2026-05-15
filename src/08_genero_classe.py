"""
Bloco A — Pegada distributiva de acidentes de trabalho: dimensão gênero
=======================================================================
Metodologia (lado da oferta, supply-side):
  1. Para cada setor j, decompõe a_j em a_j^F e a_j^M usando a participação
     feminina no emprego formal φ_j^F (RAIS-ES 2015):
        a_j^g = a_j × φ_j^g     (g ∈ {F, M})
  2. Aplica a inversa de Leontief:
        f^g' = a^g' × L^ES
     → f_j^g = pegada total de acidentes atribuída ao gênero g por R$
               de demanda final ao setor j
  3. Computa encargos absolutos e relativos, decomposição por setor e
     análise de gaps de gênero na pegada.

Referência metodológica:
  MADE/USP (2025). "Pegada de Carbono e Distribuição de Renda". NPE 76.
  (adaptado de IO-extended environmental accounting para acidentes)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from data_rais_genero import RAIS_FEMALE_SHARE_ES_2015

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
OUT_FIG = ROOT / "outputs" / "figures"
OUT_TAB = ROOT / "outputs" / "tables"

# ─────────────────────────────────────────────────────────────────────────────
def load_base() -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    setores = pd.read_csv(PROC / "mip_es_setores.csv", dtype={"codigo": str})
    vetor   = pd.read_csv(PROC / "vetor_acidentes_35.csv", dtype={"codigo": str})
    L_df    = pd.read_csv(PROC / "mip_es_L.csv", index_col=0)
    L_df.index = L_df.index.astype(str)
    return setores, vetor, L_df


def build_gender_vectors(
    vetor: pd.DataFrame,
    setores: pd.DataFrame,
    L_df: pd.DataFrame,
) -> pd.DataFrame:
    """Constrói a_j^F, a_j^M e f_j^F, f_j^M para todos os setores."""
    df = (
        setores[["codigo", "nome", "vbp_milhoes_RS", "ocupacoes"]]
        .merge(vetor[["codigo", "acidentes"]], on="codigo", how="left")
    )
    df["a_j"] = df["acidentes"] / df["vbp_milhoes_RS"]

    # Participação feminina por setor
    df["codigo"] = df["codigo"].str.zfill(4)
    df["phi_F"] = df["codigo"].map(
        {k: v for k, (v, _) in RAIS_FEMALE_SHARE_ES_2015.items()}
    ).fillna(0.322)  # fallback = share feminino nacional 2015
    df["phi_M"] = 1.0 - df["phi_F"]

    # Satélites por gênero (acidentes atribuídos ao gênero, por R$M de VBP)
    df["a_F"] = df["a_j"] * df["phi_F"]
    df["a_M"] = df["a_j"] * df["phi_M"]

    # Pegadas via Leontief
    L_df.index = L_df.index.astype(str).str.zfill(4)
    order = L_df.index.tolist()
    df_idx = df.set_index("codigo").reindex(order)
    L = L_df.values

    a_F = df_idx["a_F"].fillna(0.0).values
    a_M = df_idx["a_M"].fillna(0.0).values

    f_F = a_F @ L  # vetor linha: f_j^F
    f_M = a_M @ L

    df_idx["f_F"] = f_F
    df_idx["f_M"] = f_M
    df_idx["f_total"] = f_F + f_M
    df_idx["share_F_na_pegada"] = f_F / (f_F + f_M)
    df_idx["gap_f_pegada"] = f_F - f_M  # positivo = mulheres têm maior pegada

    # Encargo absoluto (acidentes indiretos gerados por demanda proporcional ao VBP)
    vbp_total = df_idx["vbp_milhoes_RS"].sum()
    df_idx["encargo_F"] = f_F * df_idx["vbp_milhoes_RS"] / vbp_total
    df_idx["encargo_M"] = f_M * df_idx["vbp_milhoes_RS"] / vbp_total

    return df_idx.reset_index()


def summary_stats(df: pd.DataFrame) -> dict:
    agg_F = (df["f_F"] * df["vbp_milhoes_RS"]).sum() / df["vbp_milhoes_RS"].sum()
    agg_M = (df["f_M"] * df["vbp_milhoes_RS"]).sum() / df["vbp_milhoes_RS"].sum()
    return {
        "f_agg_feminino":  agg_F,
        "f_agg_masculino": agg_M,
        "razao_F_M": agg_F / agg_M if agg_M else float("nan"),
        "share_feminino_nacional_proxy": 0.322,
        "share_feminino_pegada": (df["f_F"] * df["vbp_milhoes_RS"]).sum()
                                 / (df["f_total"] * df["vbp_milhoes_RS"]).sum(),
    }


def plot_gender_footprint(df: pd.DataFrame, out: Path) -> None:
    top = df.nlargest(15, "f_total")[["nome", "f_F", "f_M"]].copy()
    top["nome_curto"] = top["nome"].str[:35]
    fig, ax = plt.subplots(figsize=(9, 6))
    x = range(len(top))
    ax.barh(list(x), top["f_M"].values, label="Masculino", color="#2E86AB", alpha=0.85)
    ax.barh(list(x), top["f_F"].values, left=top["f_M"].values,
            label="Feminino", color="#E84855", alpha=0.85)
    ax.set_yticks(list(x))
    ax.set_yticklabels(top["nome_curto"].tolist(), fontsize=8)
    ax.set_xlabel("Pegada de acidentes por R$ M de demanda final (CATs/R$M)")
    ax.set_title("Pegada de acidentes por gênero — 15 setores de maior pegada\nMIP-ES 2015 × AEAT-ES 2015 × RAIS-ES 2015")
    ax.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Figura salva: {out}")


def plot_gender_gap(df: pd.DataFrame, out: Path) -> None:
    """Gráfico de dispersão phi_F vs a_j — identifica setores de maior risco feminino."""
    fig, ax = plt.subplots(figsize=(8, 6))
    sc = ax.scatter(
        df["phi_F"] * 100, df["a_j"],
        c=df["f_F"], cmap="RdYlGn_r",
        s=df["vbp_milhoes_RS"] / df["vbp_milhoes_RS"].max() * 800 + 30,
        alpha=0.75, edgecolors="grey", linewidths=0.4,
    )
    cb = plt.colorbar(sc, ax=ax)
    cb.set_label("$f_j^F$ (pegada feminina, CATs/R$M)", fontsize=8)
    ax.set_xlabel("Participação feminina no emprego formal (%)")
    ax.set_ylabel("Intensidade direta total $a_j$ (CATs/R$M de VBP)")
    ax.set_title("Gap de gênero na pegada de acidentes\nTamanho = VBP setorial")
    # Label outliers
    thresh_a = df["a_j"].quantile(0.80)
    thresh_phi = df["phi_F"].quantile(0.80)
    for _, row in df[
        (df["a_j"] > thresh_a) | (df["phi_F"] > thresh_phi)
    ].iterrows():
        ax.annotate(
            row["nome"][:20], (row["phi_F"] * 100, row["a_j"]),
            fontsize=6, alpha=0.8, xytext=(4, 2), textcoords="offset points",
        )
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Figura salva: {out}")


def main() -> None:
    print("=== Bloco A: Pegada de acidentes por gênero (lado da oferta) ===")
    setores, vetor, L_df = load_base()
    df = build_gender_vectors(vetor, setores, L_df)

    stats = summary_stats(df)
    print("\nAgregados:")
    print(f"  f agregado feminino  = {stats['f_agg_feminino']:.4f} CATs/R$M")
    print(f"  f agregado masculino = {stats['f_agg_masculino']:.4f} CATs/R$M")
    print(f"  Razão F/M            = {stats['razao_F_M']:.3f}")
    print(f"  Share feminino na pegada = {stats['share_feminino_pegada']*100:.1f}%")
    print(f"  (Share feminino no emprego nacional = {stats['share_feminino_nacional_proxy']*100:.1f}%)")

    print("\nTop-10 setores por pegada feminina f_j^F:")
    top = df.nlargest(10, "f_F")[
        ["codigo", "nome", "phi_F", "a_j", "f_F", "f_M", "share_F_na_pegada"]
    ]
    print(top.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    print("\nTop-10 setores por gap (f_j^F − f_j^M):")
    gap = df.nlargest(10, "gap_f_pegada")[
        ["codigo", "nome", "f_F", "f_M", "gap_f_pegada"]
    ]
    print(gap.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    # Salvar
    out_csv = PROC / "pegada_genero_es.csv"
    df.to_csv(out_csv, index=False, float_format="%.6f")
    print(f"\nSalvo: {out_csv}")

    pd.Series(stats).to_csv(PROC / "pegada_genero_summary.csv")

    # Figuras
    plot_gender_footprint(df, OUT_FIG / "pegada_genero_setores.pdf")
    plot_gender_gap(df, OUT_FIG / "gap_genero_phi_a.pdf")

    print("\n=== Concluído ===")


if __name__ == "__main__":
    main()
