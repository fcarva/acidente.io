"""
Agent 2: IO Specialist
======================
Performs the Leontief Input-Output algebra and derived social-extension
computations for the workplace-accident analysis.

Subtasks
--------
2.1 – Technical coefficients matrix A and Leontief inverse L.
2.2 – Direct intensity vector a and footprint multiplier f.
2.3 – Rasmussen-Hirschman backward linkage index U_j.
2.4 – Hypothetical Extraction Method (HEM) impact delta_CAT.
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def _safe_divide(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """Element-wise division that replaces inf/nan with 0 (handles zero denominators)."""
    denom_safe = np.where(denominator == 0, np.nan, denominator)
    result = numerator / denom_safe
    return np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)


# ---------------------------------------------------------------------------
# Subtask 2.1 – Leontief model
# ---------------------------------------------------------------------------

def leontief_model(
    Z: np.ndarray,
    X: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute the technical coefficients matrix A and the Leontief inverse L.

    A = Z · X̂⁻¹   (element-wise column normalisation)
    L = (I − A)⁻¹

    Division by zero is handled by replacing ``inf``/``nan`` with 0.

    Parameters
    ----------
    Z:
        Intermediate consumption matrix, shape (35, 35).
    X:
        Gross output vector, shape (35,).

    Returns
    -------
    A : np.ndarray, shape (35, 35)
    L : np.ndarray, shape (35, 35)
    """
    n = Z.shape[0]

    # Divide each column j of Z by X[j]; _safe_divide handles X[j]==0
    A = _safe_divide(Z, X[np.newaxis, :])

    I = np.eye(n)
    L = np.linalg.inv(I - A)

    return A, L


# ---------------------------------------------------------------------------
# Subtask 2.2 – Social extension (accident intensity & footprint multiplier)
# ---------------------------------------------------------------------------

def social_extension(
    cat_35: np.ndarray,
    X: np.ndarray,
    L: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute the direct intensity vector a and the footprint multiplier f.

    a_i = CAT_i / X_i
    f'  = a' · L

    Parameters
    ----------
    cat_35:
        Sector accident counts, shape (35,).
    X:
        Gross output vector, shape (35,).
    L:
        Leontief inverse, shape (35, 35).

    Returns
    -------
    a : np.ndarray, shape (35,)
        Direct intensity (accidents per unit of gross output).
    f : np.ndarray, shape (35,)
        Footprint multiplier (row vector).
    """
    a = _safe_divide(cat_35, X)

    f = a @ L  # row vector times L → row vector

    return a, f


# ---------------------------------------------------------------------------
# Subtask 2.3 – Rasmussen-Hirschman backward linkage
# ---------------------------------------------------------------------------

def rasmussen_hirschman(L: np.ndarray) -> np.ndarray:
    """Compute the Rasmussen-Hirschman backward linkage index U_j.

    U_j = (Σ_i l_{ij}) / l̄

    where l̄ = mean of all elements of L.

    Parameters
    ----------
    L:
        Leontief inverse, shape (35, 35).

    Returns
    -------
    U_j : np.ndarray, shape (35,)
        Normalised backward linkage for each sector j.
    """
    col_sums = L.sum(axis=0)          # Σ_i l_{ij}
    l_bar = L.mean()                  # global mean of all elements

    if l_bar == 0:
        return np.zeros(L.shape[1])

    U_j = col_sums / l_bar

    return U_j


# ---------------------------------------------------------------------------
# Subtask 2.4 – Hypothetical Extraction Method
# ---------------------------------------------------------------------------

def hypothetical_extraction(
    A: np.ndarray,
    Y: np.ndarray,
    a: np.ndarray,
    X: np.ndarray,
) -> np.ndarray:
    """Estimate the accident impact of each sector via HEM.

    For each sector k:
      1. Build A* by zeroing row k and column k of A.
      2. Compute X* = (I − A*)⁻¹ · Y.
      3. ΔCATₖ = a' · X − a' · X*

    Parameters
    ----------
    A:
        Technical coefficients matrix, shape (35, 35).
    Y:
        Final demand vector, shape (35,).
    a:
        Direct intensity vector, shape (35,).
    X:
        Gross output vector, shape (35,) — used to compute baseline a'X.

    Returns
    -------
    delta_CAT : np.ndarray, shape (35,)
        Reduction in total accidents if sector k were hypothetically extracted.
    """
    n = A.shape[0]
    I = np.eye(n)
    baseline = a @ X

    delta_CAT = np.zeros(n)

    for k in range(n):
        A_star = A.copy()
        A_star[k, :] = 0.0
        A_star[:, k] = 0.0

        L_star = np.linalg.inv(I - A_star)
        X_star = L_star @ Y

        delta_CAT[k] = baseline - (a @ X_star)

    return delta_CAT
