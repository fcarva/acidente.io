"""
Agent 1: Data Engineer
======================
Responsible for extracting, cleaning, and aligning all input data required
for the Input-Output analysis of workplace accidents in Espírito Santo.

Subtasks
--------
1.1 – Extract MIP matrices (Z, Y, X) from the Excel workbook.
1.2 – Ingest SmartLab CAT microdata and compute sector accident counts.
1.3 – Compatibilise CNAE 2.0 codes to the 35-sector MIP classification.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Subtask 1.1 – MIP extraction
# ---------------------------------------------------------------------------

def extract_mip(path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Read the MIP workbook and return (Z, Y, X) as numpy arrays.

    Parameters
    ----------
    path:
        File path to ``MIP_ES_2015.xlsm``.

    Returns
    -------
    Z : np.ndarray, shape (35, 35)
        Intermediate consumption matrix.
    Y : np.ndarray, shape (35,)
        Final demand vector.
    X : np.ndarray, shape (35,)
        Gross output vector.
    """
    z_df = pd.read_excel(path, sheet_name="Z", header=None, engine="openpyxl")
    y_df = pd.read_excel(path, sheet_name="Y", header=None, engine="openpyxl")
    x_df = pd.read_excel(path, sheet_name="X", header=None, engine="openpyxl")

    Z = z_df.values.astype(float)
    Y = y_df.values.flatten().astype(float)
    X = x_df.values.flatten().astype(float)

    return Z, Y, X


# ---------------------------------------------------------------------------
# Subtask 1.2 – SmartLab CAT ingestion
# ---------------------------------------------------------------------------

def ingest_smartlab(path: str) -> pd.DataFrame:
    """Read SmartLab CAT microdata and return aggregated accident counts.

    Filters for:
    - ``ano == 2015`` (column ``ano`` or ``Ano``)
    - ``uf == 'ES'`` (case-insensitive)
    - ``tipo_acidente == 'Típico'``

    Parameters
    ----------
    path:
        File path to ``smartlab_cat_2015.csv``.

    Returns
    -------
    pd.DataFrame
        Columns: ``['cnae20', 'cat_count']``.
    """
    df = pd.read_csv(path, dtype=str, low_memory=False)

    # Normalise column names to lowercase for robustness
    df.columns = [c.strip().lower() for c in df.columns]

    # Year filter
    if "ano" in df.columns:
        df = df[df["ano"].str.strip() == "2015"]

    # UF filter
    df = df[df["uf"].str.strip().str.upper() == "ES"]

    # Accident type filter
    df = df[df["tipo_acidente"].str.strip() == "Típico"]

    # Count by CNAE 2.0
    cat_counts = (
        df.groupby("cnae20")
        .size()
        .reset_index(name="cat_count")
    )
    cat_counts["cnae20"] = cat_counts["cnae20"].astype(str).str.strip()

    return cat_counts


# ---------------------------------------------------------------------------
# Subtask 1.3 – CNAE → MIP sector compatibilisation
# ---------------------------------------------------------------------------

def compatibilize_sectors(cat_raw: pd.DataFrame, de_para_path: str) -> np.ndarray:
    """Aggregate CNAE-level CAT counts into the 35 MIP sectors.

    Parameters
    ----------
    cat_raw:
        Output of :func:`ingest_smartlab`.
    de_para_path:
        Path to ``de_para_cnae_setores.csv`` with columns
        ``['cnae20', 'setor_id', 'setor_nome']``.

    Returns
    -------
    cat_35 : np.ndarray, shape (35,)
        CAT counts aligned with the 35 MIP row indices (missing → 0).
    """
    de_para = pd.read_csv(de_para_path, dtype={"cnae20": str, "setor_id": int})
    de_para["cnae20"] = de_para["cnae20"].str.strip()

    merged = de_para.merge(cat_raw, on="cnae20", how="left")
    merged["cat_count"] = merged["cat_count"].fillna(0).astype(float)

    aggregated = (
        merged.groupby("setor_id")["cat_count"]
        .sum()
        .reindex(range(35), fill_value=0.0)
    )

    return aggregated.values.astype(float)


# ---------------------------------------------------------------------------
# Validation gate
# ---------------------------------------------------------------------------

def validate_dimensions(
    Z: np.ndarray,
    Y: np.ndarray,
    X: np.ndarray,
    cat_35: np.ndarray,
) -> None:
    """Raise ``ValueError`` if any input does not conform to the 35-sector spec.

    Parameters
    ----------
    Z:
        Intermediate consumption matrix — must be (35, 35).
    Y:
        Final demand vector — must have length 35.
    X:
        Gross output vector — must have length 35.
    cat_35:
        Sector-level accident counts — must have length 35.
    """
    errors: list[str] = []

    if Z.shape != (35, 35):
        errors.append(f"Z must be (35, 35), got {Z.shape}")
    if Y.shape[0] != 35:
        errors.append(f"Y must have 35 elements, got {Y.shape[0]}")
    if X.shape[0] != 35:
        errors.append(f"X must have 35 elements, got {X.shape[0]}")
    if cat_35.shape[0] != 35:
        errors.append(f"cat_35 must have 35 elements, got {cat_35.shape[0]}")

    if errors:
        raise ValueError("Dimension validation failed:\n" + "\n".join(errors))
