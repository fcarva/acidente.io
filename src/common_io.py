from pathlib import Path

import numpy as np
import pandas as pd

N_SETORES = 35
ROOT = Path(__file__).resolve().parents[1]
ACCIDENTS_PATH = ROOT / "data" / "processed" / "vetor_acidentes_35.csv"
SYNTHETIC_IO_SEED = 2024
ACCIDENTS_FALLBACK_SEED = 7
MIN_VALID_BLOCK_RATIO = 0.95
MIN_VALID_Y_RATIO = 0.8


def safe_inverse(matrix: np.ndarray) -> np.ndarray:
    try:
        return np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(matrix)


def synthetic_io_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SYNTHETIC_IO_SEED)
    X = rng.uniform(1200, 6500, size=N_SETORES)
    A = rng.uniform(0.003, 0.04, size=(N_SETORES, N_SETORES))
    col_sum = A.sum(axis=0)
    scaling = np.where(col_sum > 0, np.minimum(0.7 / col_sum, 1.0), 1.0)
    A = A * scaling
    Z = A * X[np.newaxis, :]
    Y = X - Z.sum(axis=0)
    Y = np.where(Y <= 0, np.maximum(1.0, 0.1 * X), Y)
    return Z, Y, X


def _extract_numeric_block(df: pd.DataFrame) -> np.ndarray | None:
    numeric_df = df.apply(pd.to_numeric, errors="coerce")
    values = numeric_df.to_numpy(dtype=float)
    if values.size == 0:
        return None

    for i in range(max(1, values.shape[0] - N_SETORES + 1)):
        for j in range(max(1, values.shape[1] - N_SETORES + 1)):
            block = values[i : i + N_SETORES, j : j + N_SETORES]
            if block.shape == (N_SETORES, N_SETORES) and np.isfinite(block).sum() >= int(MIN_VALID_BLOCK_RATIO * block.size):
                return np.nan_to_num(block, nan=0.0)
    return None


def candidate_excel_files() -> list[Path]:
    raw_dir = ROOT / "data" / "raw"
    preferred = [
        raw_dir / "Cópia de ESPÍRITO SANTO (2015).xlsm",
        raw_dir / "MIP_ES_2015.xlsm",
    ]
    discovered = sorted(raw_dir.glob("*.xlsm")) + sorted(raw_dir.glob("*.xlsx"))
    seen = set()
    ordered = []
    for p in preferred + discovered:
        if p not in seen:
            ordered.append(p)
            seen.add(p)
    return ordered


def load_io_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    for excel_path in candidate_excel_files():
        if not excel_path.exists() or excel_path.stat().st_size == 0:
            continue
        try:
            xls = pd.ExcelFile(excel_path)
        except Exception:
            continue

        for sheet in xls.sheet_names:
            try:
                df = pd.read_excel(excel_path, sheet_name=sheet, header=None)
            except Exception:
                continue

            Z = _extract_numeric_block(df)
            if Z is None:
                continue

            values = df.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
            x_from_z = Z.sum(axis=0)
            y_from_residual = np.maximum(1.0, 0.4 * x_from_z)
            X = x_from_z + y_from_residual
            Y = y_from_residual

            if values.shape[1] >= N_SETORES + 1:
                y_candidate = values[:N_SETORES, N_SETORES]
                if np.isfinite(y_candidate).sum() >= int(MIN_VALID_Y_RATIO * N_SETORES):
                    Y = np.nan_to_num(y_candidate, nan=0.0)
                    X = Z.sum(axis=0) + Y

            if np.any(X <= 0):
                continue
            return Z, Y, X

    return synthetic_io_data()


def load_accidents() -> np.ndarray:
    if not ACCIDENTS_PATH.exists() or ACCIDENTS_PATH.stat().st_size == 0:
        rng = np.random.default_rng(ACCIDENTS_FALLBACK_SEED)
        return rng.uniform(100, 2000, size=N_SETORES)

    try:
        df = pd.read_csv(ACCIDENTS_PATH)
    except Exception:
        rng = np.random.default_rng(ACCIDENTS_FALLBACK_SEED)
        return rng.uniform(100, 2000, size=N_SETORES)

    cols = {c.lower().strip(): c for c in df.columns}
    acc_col = cols.get("acidentes")
    sector_col = cols.get("setor_id")

    if acc_col is None:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not numeric_cols:
            rng = np.random.default_rng(ACCIDENTS_FALLBACK_SEED)
            return rng.uniform(100, 2000, size=N_SETORES)
        acc_col = numeric_cols[-1]

    if sector_col is not None:
        df = df[[sector_col, acc_col]].copy()
        df[sector_col] = pd.to_numeric(df[sector_col], errors="coerce")
        df[acc_col] = pd.to_numeric(df[acc_col], errors="coerce")
        full = pd.DataFrame({"setor_id": np.arange(1, N_SETORES + 1)})
        merged = full.merge(
            df.rename(columns={sector_col: "setor_id", acc_col: "acidentes"}),
            on="setor_id",
            how="left",
        )
        return merged["acidentes"].fillna(0.0).to_numpy(dtype=float)

    vals = pd.to_numeric(df[acc_col], errors="coerce").dropna().to_numpy(dtype=float)
    if vals.size < N_SETORES:
        vals = np.pad(vals, (0, N_SETORES - vals.size), constant_values=0.0)
    return vals[:N_SETORES]
