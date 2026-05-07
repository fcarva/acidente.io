"""
Orchestrator
============
Manager agent that drives the full multi-agent pipeline for the
Input-Output analysis of workplace accidents in Espírito Santo, Brazil.

Pipeline stages
---------------
1. Data Engineer  – extracts and aligns raw data (gate: dimension check).
2. IO Specialist  – runs Leontief algebra and social extensions.
3. Data Viz       – generates charts and exports Excel tables.
"""

from __future__ import annotations

import os

import pandas as pd

from agents.data_engineer import (
    compatibilize_sectors,
    extract_mip,
    ingest_smartlab,
    validate_dimensions,
)
from agents.io_specialist import (
    hypothetical_extraction,
    leontief_model,
    rasmussen_hirschman,
    social_extension,
)
from agents.data_viz import (
    build_results_dataframe,
    export_excel,
    generate_scatter_plot,
)


def _ensure_output_dirs() -> None:
    """Create all required output directories if they don't already exist."""
    for path in (
        "data/raw",
        "data/processed",
        "notebooks",
        "outputs/tables",
        "outputs/figures",
    ):
        os.makedirs(path, exist_ok=True)


def run_pipeline(
    mip_path: str,
    cat_path: str,
    de_para_path: str,
    sector_names: list[str],
) -> pd.DataFrame:
    """Execute the full multi-agent pipeline end-to-end.

    Parameters
    ----------
    mip_path:
        Path to ``MIP_ES_2015.xlsm``.
    cat_path:
        Path to ``smartlab_cat_2015.csv``.
    de_para_path:
        Path to ``de_para_cnae_setores.csv``.
    sector_names:
        Ordered list of 35 sector names aligned with matrix rows.

    Returns
    -------
    pd.DataFrame
        Consolidated results table with quadrant classification.
    """
    _ensure_output_dirs()

    # ------------------------------------------------------------------
    # Stage 1: Data Engineer
    # ------------------------------------------------------------------
    print("[Orchestrator] Etapa 1 — Data Engineer")

    print("  1.1 Extraindo matrizes MIP …")
    Z, Y, X = extract_mip(mip_path)

    print("  1.2 Ingerindo microdados SmartLab CAT …")
    cat_raw = ingest_smartlab(cat_path)

    print("  1.3 Compatibilizando setores CNAE → MIP …")
    cat_35 = compatibilize_sectors(cat_raw, de_para_path)

    print("  [Gate] Validando dimensões …")
    validate_dimensions(Z, Y, X, cat_35)
    print("  Dimensões OK (35×35 / 35).")

    # ------------------------------------------------------------------
    # Stage 2: IO Specialist
    # ------------------------------------------------------------------
    print("[Orchestrator] Etapa 2 — IO Specialist")

    print("  2.1 Calculando matriz A e inversa de Leontief L …")
    A, L = leontief_model(Z, X)

    print("  2.2 Extensão social: intensidade direta a e multiplicador f …")
    a, f = social_extension(cat_35, X, L)

    print("  2.3 Índice de Rasmussen-Hirschman U_j …")
    U_j = rasmussen_hirschman(L)

    print("  2.4 Método de Extração Hipotética (HEM) …")
    delta_CAT = hypothetical_extraction(A, Y, a, X)

    # ------------------------------------------------------------------
    # Stage 3: Data Viz
    # ------------------------------------------------------------------
    print("[Orchestrator] Etapa 3 — Data Viz")

    print("  3.1 Construindo DataFrame de resultados e classificando perfis …")
    df = build_results_dataframe(cat_35, a, U_j, f, delta_CAT, sector_names)

    print("  3.2 Gerando gráfico de dispersão por quadrante …")
    generate_scatter_plot(df)

    print("  3.3 Exportando tabela Excel …")
    export_excel(df)

    print("[Orchestrator] Pipeline concluído com sucesso.")
    return df


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result_df = run_pipeline(
        mip_path="data/raw/MIP_ES_2015.xlsm",
        cat_path="data/raw/smartlab_cat_2015.csv",
        de_para_path="data/raw/de_para_cnae_setores.csv",
        sector_names=[f"Setor {i + 1}" for i in range(35)],
    )
    print("\nTop 10 setores por multiplicador de pegada f:")
    print(result_df.nlargest(10, "f")[["setor_nome", "f", "U_j", "Perfil"]].to_string(index=False))
