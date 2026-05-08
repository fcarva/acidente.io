"""
Preparação do vetor satélite de acidentes (CATs) alinhado aos 35 setores
da MIP-ES 2015.

Hierarquia de fontes (ver detalhes em README.md):
    1. data/raw/aeat15_es_subsecao_a.csv  → CAT por CNAE 2.0 do AEAT-2015
       agregada via data/raw/de_para_cnae_setores.csv (CNAE→MIP-35).
    2. data/processed/cats_es_proxy.csv → calibração proxy do TD-60 IJSN
       (preenchida quando o AEAT oficial não está disponível).
    3. fallback sintético reprodutível (smoke-test apenas).

Saída:
    data/processed/vetor_acidentes_35.csv  com colunas
        codigo, nome, vbp_milhoes_RS, acidentes
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from common_io import (
    ACCIDENTS_FALLBACK_SEED,
    ACCIDENTS_PATH,
    CATS_PROXY_PATH,
    DATA_RAW,
    N_SETORES,
    load_sectors,
)

AEAT_RAW_PATH = DATA_RAW / "aeat15_es_subsecao_a.csv"
DE_PARA_PATH = DATA_RAW / "de_para_cnae_setores.csv"


def _read_csv_robust(path: Path) -> pd.DataFrame:
    for sep in (",", ";", "\t"):
        try:
            df = pd.read_csv(path, sep=sep)
            if not df.empty and len(df.columns) > 1:
                return df
        except Exception:
            continue
    return pd.DataFrame()


def _build_from_aeat(sectors: pd.DataFrame) -> pd.DataFrame | None:
    if not (AEAT_RAW_PATH.exists() and AEAT_RAW_PATH.stat().st_size > 0):
        return None
    if not (DE_PARA_PATH.exists() and DE_PARA_PATH.stat().st_size > 0):
        return None

    aeat = _read_csv_robust(AEAT_RAW_PATH)
    de_para = _read_csv_robust(DE_PARA_PATH)
    if aeat.empty or de_para.empty:
        return None

    aeat_cols = {c.lower().strip(): c for c in aeat.columns}
    cnae_col = aeat_cols.get("cnae") or aeat_cols.get("cnae_2")
    qtd_col = aeat_cols.get("acidentes") or aeat_cols.get("cat") or aeat_cols.get("quantidade")
    if cnae_col is None or qtd_col is None:
        return None

    dp_cols = {c.lower().strip(): c for c in de_para.columns}
    dp_cnae = dp_cols.get("cnae") or de_para.columns[0]
    dp_setor = dp_cols.get("setor_mip") or dp_cols.get("codigo")
    dp_peso = dp_cols.get("peso")
    if dp_setor is None:
        return None

    aeat_clean = aeat[[cnae_col, qtd_col]].copy()
    aeat_clean[qtd_col] = pd.to_numeric(aeat_clean[qtd_col], errors="coerce")
    aeat_clean = aeat_clean.dropna()

    cols = [dp_cnae, dp_setor] + ([dp_peso] if dp_peso else [])
    merged = aeat_clean.merge(de_para[cols], left_on=cnae_col, right_on=dp_cnae, how="left")
    merged["peso"] = merged[dp_peso] if dp_peso else 1.0
    merged["contrib"] = merged[qtd_col] * merged["peso"]
    agg = merged.dropna(subset=[dp_setor]).groupby(dp_setor, as_index=False)["contrib"].sum()
    agg = agg.rename(columns={dp_setor: "codigo", "contrib": "acidentes"})
    agg["codigo"] = agg["codigo"].astype(str).str.zfill(4)

    base = sectors[["codigo", "nome", "vbp_milhoes_RS"]].copy()
    out = base.merge(agg, on="codigo", how="left")
    out["acidentes"] = out["acidentes"].fillna(0.0)
    return out


def _build_from_proxy(sectors: pd.DataFrame) -> pd.DataFrame | None:
    if not (CATS_PROXY_PATH.exists() and CATS_PROXY_PATH.stat().st_size > 0):
        return None
    proxy = pd.read_csv(CATS_PROXY_PATH, dtype={"codigo": str})
    if "cats_2015" not in proxy.columns:
        return None
    base = sectors[["codigo", "nome", "vbp_milhoes_RS"]].copy()
    out = base.merge(proxy[["codigo", "cats_2015"]], on="codigo", how="left")
    out = out.rename(columns={"cats_2015": "acidentes"})
    out["acidentes"] = out["acidentes"].fillna(0.0)
    return out


def _build_synthetic(sectors: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(ACCIDENTS_FALLBACK_SEED)
    base = sectors[["codigo", "nome", "vbp_milhoes_RS"]].copy()
    base["acidentes"] = rng.integers(low=80, high=1800, size=N_SETORES).astype(float)
    return base


def main() -> None:
    ACCIDENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    sectors = load_sectors()

    aeat = _build_from_aeat(sectors)
    if aeat is not None:
        source = "aeat-2015 oficial agregado via de_para CNAE"
        out = aeat
    else:
        proxy = _build_from_proxy(sectors)
        if proxy is not None:
            source = "proxy TD-60 IJSN (cats_es_proxy.csv)"
            out = proxy
        else:
            source = "fallback sintético"
            out = _build_synthetic(sectors)

    out.to_csv(ACCIDENTS_PATH, index=False)
    total = out["acidentes"].sum()
    print(f"[01_data_prep] fonte: {source}")
    print(f"[01_data_prep] total CATs no ES: {total:,.0f}")
    print(f"[01_data_prep] vetor salvo em: {ACCIDENTS_PATH}")


if __name__ == "__main__":
    main()
