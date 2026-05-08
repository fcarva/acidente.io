"""
Carregamento centralizado dos artefatos da MIP-ES 2015.

Fonte primária:
    IJSN — Texto para Discussão nº 60 / Dados Abertos ES.
    Arquivo "Matriz_Insumo-Produto_MIP.xlsx" (35 setores).

Hierarquia de carregamento (mais consolidado primeiro):
    1. data/processed/mip_es_L.csv             ← L oficial IJSN (publicada)
    2. data/raw/Matriz_Insumo-Produto_MIP*.xlsx ← XLSX oficial IJSN
    3. data/processed/mip_es_Z.csv             ← Z reconstruída do TD-60
    4. fallback sintético reprodutível

Vetor satélite (CATs):
    1. data/processed/vetor_acidentes_35.csv   ← gerado por 01_data_prep
    2. data/processed/cats_es_proxy.csv        ← proxy do TD-60
    3. fallback sintético

A = I − L^{-1}   quando L é a fonte primária
A = Z · diag(X)^{-1}  quando Z é a fonte primária
Z = A · diag(X)  é sempre derivável internamente para HEM.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

N_SETORES = 35
ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"

SETORES_PATH = DATA_PROC / "mip_es_setores.csv"
L_CSV_PATH = DATA_PROC / "mip_es_L.csv"
Z_CSV_PATH = DATA_PROC / "mip_es_Z.csv"
A_CSV_PATH = DATA_PROC / "mip_es_A.csv"
CATS_PROXY_PATH = DATA_PROC / "cats_es_proxy.csv"
ACCIDENTS_PATH = DATA_PROC / "vetor_acidentes_35.csv"

SYNTHETIC_IO_SEED = 2024
ACCIDENTS_FALLBACK_SEED = 7
MIN_PRODUCTION_THRESHOLD = 1e-9
FROBENIUS_TOLERANCE = 1e-8


def safe_inverse(matrix: np.ndarray) -> np.ndarray:
    try:
        return np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(matrix)


def load_sectors() -> pd.DataFrame:
    if SETORES_PATH.exists() and SETORES_PATH.stat().st_size > 0:
        df = pd.read_csv(SETORES_PATH, dtype={"codigo": str})
        if len(df) == N_SETORES:
            return df
    return _synthetic_sectors()


def _synthetic_sectors() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "codigo": [f"S{i:02d}" for i in range(1, N_SETORES + 1)],
            "nome": [f"Setor sintético {i}" for i in range(1, N_SETORES + 1)],
            "vbp_milhoes_RS": np.full(N_SETORES, 1000.0),
            "ocupacoes": np.full(N_SETORES, 1000),
        }
    )


def _load_matrix_from_csv(path: Path) -> np.ndarray | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    df = pd.read_csv(path, index_col=0)
    if df.shape != (N_SETORES, N_SETORES):
        return None
    return df.to_numpy(dtype=float)


def _candidate_excel_files() -> list[Path]:
    if not DATA_RAW.exists():
        return []
    preferred = [
        DATA_RAW / "Matriz_Insumo-Produto_MIP_35x35.xlsx",
        DATA_RAW / "Matriz_Insumo-Produto_MIP.xlsx",
        DATA_RAW / "MIP_ES_2015.xlsm",
    ]
    discovered = sorted(DATA_RAW.glob("*.xlsx")) + sorted(DATA_RAW.glob("*.xlsm"))
    seen: set[Path] = set()
    ordered: list[Path] = []
    for p in preferred + discovered:
        if p.exists() and p.stat().st_size > 0 and p not in seen:
            ordered.append(p)
            seen.add(p)
    return ordered


def _load_Z_from_xlsx() -> np.ndarray | None:
    for excel_path in _candidate_excel_files():
        try:
            xls = pd.ExcelFile(excel_path)
        except Exception:
            continue
        for sheet in xls.sheet_names:
            try:
                df = pd.read_excel(excel_path, sheet_name=sheet, header=None)
            except Exception:
                continue
            values = df.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
            for i in range(max(1, values.shape[0] - N_SETORES + 1)):
                for j in range(max(1, values.shape[1] - N_SETORES + 1)):
                    block = values[i : i + N_SETORES, j : j + N_SETORES]
                    if block.shape != (N_SETORES, N_SETORES):
                        continue
                    if np.isfinite(block).sum() < int(0.95 * block.size):
                        continue
                    if np.diag(block).max() > 1.5:  # heurística: matriz Z não-Leontief
                        continue
                    return np.nan_to_num(block, nan=0.0)
    return None


def _synthetic_io_data() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SYNTHETIC_IO_SEED)
    X = rng.uniform(1200.0, 6500.0, size=N_SETORES)
    A = rng.uniform(0.003, 0.04, size=(N_SETORES, N_SETORES))
    col_sum = A.sum(axis=0)
    scaling = np.where(col_sum > 0, np.minimum(0.7 / col_sum, 1.0), 1.0)
    A = A * scaling
    Z = A * X[np.newaxis, :]
    Y = X - Z.sum(axis=0)
    Y = np.where(Y <= 0, np.maximum(1.0, 0.1 * X), Y)
    L = safe_inverse(np.eye(N_SETORES) - A)
    return Z, A, L, X


def load_io_data() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, pd.DataFrame, str]:
    """Retorna (Z, A, L, X, Y, sectors, source)."""
    sectors = load_sectors()
    X = sectors["vbp_milhoes_RS"].to_numpy(dtype=float)
    I = np.eye(N_SETORES)

    L = _load_matrix_from_csv(L_CSV_PATH)
    if L is not None:
        A = I - safe_inverse(L)
        A = np.clip(A, 0.0, None)
        Z = A * X[np.newaxis, :]
        Y = np.maximum(X - Z.sum(axis=0), 0.0)
        return Z, A, L, X, Y, sectors, "csv_L_oficial_ijsn"

    Z = _load_Z_from_xlsx()
    if Z is not None:
        X_safe = np.where(X <= 0, MIN_PRODUCTION_THRESHOLD, X)
        A = Z / X_safe[np.newaxis, :]
        L = safe_inverse(I - A)
        Y = np.maximum(X - Z.sum(axis=0), 0.0)
        return Z, A, L, X, Y, sectors, "xlsx_ijsn_oficial"

    Z = _load_matrix_from_csv(Z_CSV_PATH)
    if Z is not None:
        X_safe = np.where(X <= 0, MIN_PRODUCTION_THRESHOLD, X)
        A = Z / X_safe[np.newaxis, :]
        L = safe_inverse(I - A)
        Y = np.maximum(X - Z.sum(axis=0), 0.0)
        return Z, A, L, X, Y, sectors, "csv_Z_td60_reconstruida"

    Z, A, L, X = _synthetic_io_data()
    Y = np.maximum(X - Z.sum(axis=0), 0.0)
    return Z, A, L, X, Y, _synthetic_sectors(), "synthetic_fallback"


def _load_accidents_from_processed() -> np.ndarray | None:
    if ACCIDENTS_PATH.exists() and ACCIDENTS_PATH.stat().st_size > 0:
        df = pd.read_csv(ACCIDENTS_PATH, dtype={"codigo": str})
        if "acidentes" in df.columns and len(df) == N_SETORES:
            return df["acidentes"].to_numpy(dtype=float)
    return None


def _load_accidents_from_proxy() -> np.ndarray | None:
    if CATS_PROXY_PATH.exists() and CATS_PROXY_PATH.stat().st_size > 0:
        df = pd.read_csv(CATS_PROXY_PATH, dtype={"codigo": str})
        if "cats_2015" in df.columns and len(df) == N_SETORES:
            return df["cats_2015"].to_numpy(dtype=float)
    return None


def load_accidents() -> tuple[np.ndarray, str]:
    """Retorna o vetor de CATs (35,) e a etiqueta da fonte."""
    acc = _load_accidents_from_processed()
    if acc is not None:
        return acc, "processed_vetor_acidentes_35"

    acc = _load_accidents_from_proxy()
    if acc is not None:
        return acc, "cats_es_proxy_td60"

    rng = np.random.default_rng(ACCIDENTS_FALLBACK_SEED)
    return rng.uniform(100.0, 2000.0, size=N_SETORES), "synthetic_fallback"
