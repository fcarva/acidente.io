"""
Scatter de quadrantes de risco — plano (U_j, a_j) com cortes pelas médias.

- Eixo X: U_j (encadeamento para trás, Rasmussen-Hirschman backward)
- Eixo Y: a_j (intensidade direta de acidentes — CATs por R$ milhão)
- Cortes: média de U e média de a (4 quadrantes)
- Top-5 setores por pegada f recebem rótulo destacado via adjustText
- Saída: outputs/figures/quadrante_risco_es.pdf  (vetorial, alta qualidade)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from adjustText import adjust_text  # type: ignore

    HAS_ADJUSTTEXT = True
except ImportError:
    HAS_ADJUSTTEXT = False

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "outputs" / "tables" / "resultados_principais.csv"
OUTPUT_PDF = ROOT / "outputs" / "figures" / "quadrante_risco_es.pdf"
OUTPUT_PNG = ROOT / "outputs" / "figures" / "quadrante_risco_es.png"

OXBLOOD = "#6e1f1c"
INK = "#1a1612"
INK_SOFT = "#3a342c"
GRAY = "#6b6359"
HIGHLIGHT_BG = "#ebe2d0"


def main() -> None:
    if not INPUT_PATH.exists() or INPUT_PATH.stat().st_size == 0:
        raise FileNotFoundError(
            f"Arquivo de resultados não encontrado: {INPUT_PATH}. Execute 02_io_model.py antes."
        )

    df = pd.read_csv(INPUT_PATH, dtype={"codigo": str})
    required = {"codigo", "nome", "intensidade_direta_a", "encadeamento_tras_U", "pegada_estrutural_f"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes em {INPUT_PATH.name}: {sorted(missing)}")

    x = df["encadeamento_tras_U"].to_numpy(dtype=float)
    y = df["intensidade_direta_a"].to_numpy(dtype=float)
    f = df["pegada_estrutural_f"].to_numpy(dtype=float)
    codes = df["codigo"].astype(str).tolist()

    x_mean = float(x.mean())
    y_mean = float(y.mean())
    x_max = float(x.max()) * 1.10
    y_max = float(y.max()) * 1.15

    top5_idx = np.argsort(-f)[:5]
    is_top5 = np.zeros(len(df), dtype=bool)
    is_top5[top5_idx] = True

    is_chave = (x > x_mean) & (y > y_mean)
    is_propagador = (x > x_mean) & (y <= y_mean)
    is_localizado = (x <= x_mean) & (y > y_mean)

    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["DejaVu Serif", "Liberation Serif", "Times New Roman"],
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
        }
    )

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9.0, 6.5))

    # zona crítica (alta-alta) sombreada
    ax.add_patch(
        mpl.patches.Rectangle(
            (x_mean, y_mean),
            x_max - x_mean,
            y_max - y_mean,
            facecolor=HIGHLIGHT_BG,
            edgecolor="none",
            alpha=0.6,
            zorder=0,
        )
    )

    ax.axvline(x_mean, color=OXBLOOD, lw=0.8, ls=(0, (3, 3)), alpha=0.8, zorder=1)
    ax.axhline(y_mean, color=OXBLOOD, lw=0.8, ls=(0, (3, 3)), alpha=0.8, zorder=1)

    ax.scatter(
        x[~is_chave & ~is_propagador & ~is_localizado],
        y[~is_chave & ~is_propagador & ~is_localizado],
        s=28, color=GRAY, alpha=0.75, edgecolors=INK, linewidths=0.4, zorder=2,
        label="Residual",
    )
    ax.scatter(
        x[is_propagador], y[is_propagador],
        s=42, color=INK_SOFT, alpha=0.85, edgecolors=INK, linewidths=0.5, zorder=3,
        label="Propagador estrutural",
    )
    ax.scatter(
        x[is_localizado], y[is_localizado],
        s=42, color=INK_SOFT, alpha=0.85, edgecolors=INK, linewidths=0.5,
        marker="s", zorder=3,
        label="Risco localizado",
    )
    ax.scatter(
        x[is_chave], y[is_chave],
        s=70, color=OXBLOOD, alpha=0.9, edgecolors=INK, linewidths=0.6, zorder=4,
        label="Setor-chave de risco",
    )

    texts = []
    for i, code in enumerate(codes):
        if is_top5[i] or is_chave[i]:
            label = code
            color = OXBLOOD if is_top5[i] else INK
            weight = "bold" if is_top5[i] else "normal"
            texts.append(
                ax.text(
                    x[i], y[i], label,
                    fontsize=8.5, color=color, weight=weight,
                    family="monospace", zorder=5,
                )
            )

    if HAS_ADJUSTTEXT and texts:
        adjust_text(
            texts,
            ax=ax,
            arrowprops=dict(arrowstyle="-", color=INK, lw=0.4, alpha=0.6),
            expand=(1.2, 1.4),
        )

    ax.text(x_mean, -0.03 * y_max, r"$\bar{U}$", ha="center", va="top",
            color=OXBLOOD, fontsize=10, fontstyle="italic")
    ax.text(-0.03 * x_max, y_mean, r"$\bar{a}$", ha="right", va="center",
            color=OXBLOOD, fontsize=10, fontstyle="italic")

    ax.set_xlabel(r"$U_j$  ·  encadeamento para trás (Rasmussen-Hirschman)",
                  fontsize=11, style="italic")
    ax.set_ylabel(r"$a_j$  ·  intensidade direta de acidentes  (CATs / R\$ milhão)",
                  fontsize=11, style="italic")
    ax.set_title(
        "Quadrantes de risco ocupacional — MIP-ES 2015",
        pad=12, color=INK, fontsize=12,
    )
    ax.set_xlim(0, x_max)
    ax.set_ylim(0, y_max)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    ax.grid(alpha=0.18, lw=0.4)

    fig.tight_layout()
    fig.savefig(OUTPUT_PDF, dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PNG, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"[04_viz] adjustText disponível: {HAS_ADJUSTTEXT}")
    print(f"[04_viz] PDF → {OUTPUT_PDF}")
    print(f"[04_viz] PNG → {OUTPUT_PNG}")


if __name__ == "__main__":
    main()
