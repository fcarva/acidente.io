from pathlib import Path

import numpy as np
import pandas as pd

from common_io import ACCIDENTS_FALLBACK_SEED, N_SETORES

ROOT = Path(__file__).resolve().parents[1]
RAW_SMARTLAB = ROOT / "data" / "raw" / "smartlab_cat_2015.csv"
DE_PARA_PATH = ROOT / "data" / "processed" / "de_para_cnae_mip.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "vetor_acidentes_35.csv"


def _read_csv_with_fallback(path: Path) -> pd.DataFrame:
    for sep in (",", ";", "\t"):
        try:
            df = pd.read_csv(path, sep=sep)
            if not df.empty and len(df.columns) > 1:
                return df
        except Exception:
            continue
    return pd.DataFrame()


def _build_synthetic_vector() -> pd.DataFrame:
    rng = np.random.default_rng(ACCIDENTS_FALLBACK_SEED)
    acidentes = rng.integers(low=80, high=1800, size=N_SETORES)
    return pd.DataFrame({"setor_id": np.arange(1, N_SETORES + 1), "acidentes": acidentes})


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not RAW_SMARTLAB.exists() or RAW_SMARTLAB.stat().st_size == 0:
        result = _build_synthetic_vector()
        result.to_csv(OUTPUT_PATH, index=False)
        print(f"Arquivo SmartLab ausente/vazio. Vetor fictício salvo em: {OUTPUT_PATH}")
        return

    raw_df = _read_csv_with_fallback(RAW_SMARTLAB)
    if raw_df.empty:
        result = _build_synthetic_vector()
        result.to_csv(OUTPUT_PATH, index=False)
        print(f"Não foi possível ler SmartLab. Vetor fictício salvo em: {OUTPUT_PATH}")
        return

    col_lower = {c.lower().strip(): c for c in raw_df.columns}
    acc_candidates = ["acidentes", "cat", "total_cat", "qtde_cat", "quantidade", "valor"]
    sector_candidates = ["setor_35", "setor", "setor_id", "setor_mip"]
    cnae_candidates = ["cnae", "cnae_2", "cnae20", "cnae_divisao"]

    acc_col = next((col_lower[c] for c in acc_candidates if c in col_lower), None)
    sector_col = next((col_lower[c] for c in sector_candidates if c in col_lower), None)
    cnae_col = next((col_lower[c] for c in cnae_candidates if c in col_lower), None)

    if acc_col is None:
        numeric_cols = raw_df.select_dtypes(include=["number"]).columns.tolist()
        acc_col = numeric_cols[-1] if numeric_cols else None

    result = None
    if acc_col is not None and sector_col is not None:
        grouped = (
            raw_df[[sector_col, acc_col]]
            .dropna()
            .assign(**{acc_col: pd.to_numeric(raw_df[acc_col], errors="coerce")})
            .dropna()
            .groupby(sector_col, as_index=False)[acc_col]
            .sum()
        )
        grouped = grouped.rename(columns={sector_col: "setor_id", acc_col: "acidentes"})
        grouped["setor_id"] = pd.to_numeric(grouped["setor_id"], errors="coerce")
        result = grouped.dropna().copy()

    elif acc_col is not None and cnae_col is not None and DE_PARA_PATH.exists() and DE_PARA_PATH.stat().st_size > 0:
        de_para = _read_csv_with_fallback(DE_PARA_PATH)
        de_para_cols = {c.lower().strip(): c for c in de_para.columns}
        de_para_cnae = de_para_cols.get("cnae") or de_para.columns[0]
        de_para_setor = de_para_cols.get("setor_id") or de_para_cols.get("setor_35") or de_para.columns[-1]

        merged = raw_df[[cnae_col, acc_col]].merge(
            de_para[[de_para_cnae, de_para_setor]],
            left_on=cnae_col,
            right_on=de_para_cnae,
            how="left",
        )
        merged[acc_col] = pd.to_numeric(merged[acc_col], errors="coerce")
        merged[de_para_setor] = pd.to_numeric(merged[de_para_setor], errors="coerce")
        result = (
            merged.dropna(subset=[acc_col, de_para_setor])
            .groupby(de_para_setor, as_index=False)[acc_col]
            .sum()
            .rename(columns={de_para_setor: "setor_id", acc_col: "acidentes"})
        )

    if result is None or result.empty:
        result = _build_synthetic_vector()
    else:
        result = result[(result["setor_id"] >= 1) & (result["setor_id"] <= N_SETORES)]
        full = pd.DataFrame({"setor_id": np.arange(1, N_SETORES + 1)})
        result = full.merge(result, on="setor_id", how="left").fillna({"acidentes": 0.0})

    result["acidentes"] = pd.to_numeric(result["acidentes"], errors="coerce").fillna(0.0)
    result.to_csv(OUTPUT_PATH, index=False)
    print(f"Vetor de acidentes (35 setores) salvo em: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
