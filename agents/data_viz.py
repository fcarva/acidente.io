"""
Agent 3: Data Viz
=================
Produces the analytical outputs: sector-risk quadrant scatter plot and
formatted Excel tables.

Subtasks
--------
3.1 – Build the consolidated results DataFrame and assign quadrant profiles.
3.2 – Generate the risk-quadrant scatter plot (PDF, 300 dpi).
3.3 – Export results to a multi-sheet Excel workbook.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for headless environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Subtask 3.1 – Results DataFrame + quadrant classification
# ---------------------------------------------------------------------------

def build_results_dataframe(
    cat_35: np.ndarray,
    a: np.ndarray,
    U_j: np.ndarray,
    f: np.ndarray,
    delta_CAT: np.ndarray,
    sector_names: list[str],
) -> pd.DataFrame:
    """Build the consolidated results DataFrame with quadrant classification.

    Quadrant profiles (based on sector means of a and U_j):

    +-------------------+-------------------+-----------------------------+
    | a > ā             | U_j > Ū_j         | "Setor-chave de Risco"      |
    | a ≤ ā             | U_j > Ū_j         | "Propagador Estrutural"     |
    | a > ā             | U_j ≤ Ū_j         | "Risco Localizado"          |
    | a ≤ ā             | U_j ≤ Ū_j         | "Residual"                  |
    +-------------------+-------------------+-----------------------------+

    Parameters
    ----------
    cat_35:
        Raw accident counts, shape (35,).
    a:
        Direct intensity vector, shape (35,).
    U_j:
        Rasmussen-Hirschman backward linkage, shape (35,).
    f:
        Footprint multiplier, shape (35,).
    delta_CAT:
        HEM accident impact, shape (35,).
    sector_names:
        List of 35 sector names aligned with matrix rows.

    Returns
    -------
    pd.DataFrame
        Columns: setor_nome, cat_count, a, U_j, f, delta_CAT, Perfil.
    """
    df = pd.DataFrame({
        "setor_nome": sector_names,
        "cat_count": cat_35,
        "a": a,
        "U_j": U_j,
        "f": f,
        "delta_CAT": delta_CAT,
    })

    a_mean = df["a"].mean()
    uj_mean = df["U_j"].mean()

    def _classify(row: pd.Series) -> str:
        high_a = row["a"] > a_mean
        high_uj = row["U_j"] > uj_mean
        if high_a and high_uj:
            return "Setor-chave de Risco"
        if not high_a and high_uj:
            return "Propagador Estrutural"
        if high_a and not high_uj:
            return "Risco Localizado"
        return "Residual"

    df["Perfil"] = df.apply(_classify, axis=1)

    return df


# ---------------------------------------------------------------------------
# Subtask 3.2 – Scatter plot
# ---------------------------------------------------------------------------

_PROFILE_COLORS: dict[str, str] = {
    "Setor-chave de Risco": "#d62728",
    "Propagador Estrutural": "#ff7f0e",
    "Risco Localizado": "#1f77b4",
    "Residual": "#aec7e8",
}

_OUTPUT_FIGURE = "outputs/figures/quadrante_risco_es.pdf"


def generate_scatter_plot(
    df: pd.DataFrame,
    dpi: int = 300,
    fmt: str = "pdf",
) -> None:
    """Generate and save the risk-quadrant scatter plot.

    Axes
    ----
    X-axis : U_j (Rasmussen-Hirschman backward linkage)
    Y-axis : a   (direct accident intensity)

    Dashed reference lines mark the mean of each axis.
    The top 5 sectors by *a* and top 5 by *U_j* are labelled (union).

    Parameters
    ----------
    df:
        Output of :func:`build_results_dataframe`.
    dpi:
        Resolution in dots per inch (default 300).
    fmt:
        Output file format (default ``"pdf"``).
    """
    os.makedirs(os.path.dirname(_OUTPUT_FIGURE), exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 8))

    a_mean = df["a"].mean()
    uj_mean = df["U_j"].mean()

    for profile, group in df.groupby("Perfil"):
        color = _PROFILE_COLORS.get(str(profile), "#7f7f7f")
        ax.scatter(
            group["U_j"],
            group["a"],
            c=color,
            label=str(profile),
            s=80,
            alpha=0.85,
            edgecolors="white",
            linewidths=0.5,
        )

    ax.axvline(uj_mean, color="grey", linestyle="--", linewidth=0.9, alpha=0.7)
    ax.axhline(a_mean, color="grey", linestyle="--", linewidth=0.9, alpha=0.7)

    # Label outliers: union of top-5 by a and top-5 by U_j
    top_a = set(df.nlargest(5, "a").index)
    top_uj = set(df.nlargest(5, "U_j").index)
    to_label = top_a | top_uj

    for idx in to_label:
        row = df.loc[idx]
        ax.annotate(
            row["setor_nome"],
            xy=(row["U_j"], row["a"]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=6.5,
            alpha=0.9,
        )

    ax.set_xlabel("Encadeamento Retroativo $U_j$ (Rasmussen-Hirschman)", fontsize=11)
    ax.set_ylabel("Intensidade Direta de Acidentes $a_i$", fontsize=11)
    ax.set_title(
        "Quadrante de Risco Ocupacional — Espírito Santo, 2015",
        fontsize=13,
        pad=12,
    )
    ax.legend(title="Perfil Setorial", fontsize=9, title_fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.4)

    fig.tight_layout()
    output_path = f"{os.path.splitext(_OUTPUT_FIGURE)[0]}.{fmt}"
    fig.savefig(output_path, dpi=dpi, format=fmt)
    plt.close(fig)
    print(f"[DataViz] Figura salva em {output_path}")


# ---------------------------------------------------------------------------
# Subtask 3.3 – Excel export
# ---------------------------------------------------------------------------

_OUTPUT_EXCEL = "outputs/tables/tabelas_resultados.xlsx"


def _format_pt_decimal(value: float) -> str:
    """Format a float using Brazilian convention: comma as decimal separator,
    period as thousands separator (e.g. 1.234,567890).

    Returns empty string for missing values.
    """
    if not pd.notna(value):
        return ""
    # Build standard English-locale string, then swap separators
    en_str = f"{value:,.6f}"          # e.g. "1,234.567890"
    # Split on '.' to isolate integer and decimal parts, then rejoin
    integer_part, decimal_part = en_str.split(".")
    pt_str = integer_part.replace(",", ".") + "," + decimal_part
    return pt_str                      # e.g. "1.234,567890"


def export_excel(df: pd.DataFrame) -> None:
    """Export results to a multi-sheet Excel workbook.

    Sheets
    ------
    Resultados
        Main results sorted by *f* descending.
    PT_formatted
        Same data with Brazilian decimal-comma string formatting.
    Dados_Brutos
        Unsorted raw data.

    Parameters
    ----------
    df:
        Output of :func:`build_results_dataframe`.
    """
    os.makedirs(os.path.dirname(_OUTPUT_EXCEL), exist_ok=True)

    df_sorted = df.sort_values("f", ascending=False).reset_index(drop=True)

    # PT-formatted sheet: numeric columns as strings with comma decimals
    numeric_cols = ["cat_count", "a", "U_j", "f", "delta_CAT"]
    df_pt = df_sorted.copy()
    for col in numeric_cols:
        df_pt[col] = df_pt[col].apply(_format_pt_decimal)

    with pd.ExcelWriter(_OUTPUT_EXCEL, engine="openpyxl") as writer:
        df_sorted.to_excel(writer, sheet_name="Resultados", index=False)
        df_pt.to_excel(writer, sheet_name="PT_formatted", index=False)
        df.to_excel(writer, sheet_name="Dados_Brutos", index=False)

    print(f"[DataViz] Tabela Excel salva em {_OUTPUT_EXCEL}")
