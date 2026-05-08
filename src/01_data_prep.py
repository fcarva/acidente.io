"""
Vetor satélite de acidentes (CATs) alinhado aos 35 setores da MIP-ES 2015.

Hierarquia:
    1. data/raw/aeat15_es_subsecao_a.csv  + data/raw/de_para_cnae_setores.csv
       → agregação CNAE-divisão (2-dig) e sub-divisão (3-dig) → MIP-35.
    2. data/processed/cats_es_proxy.csv   (calibração TD-60)
    3. fallback sintético

Coluna usada por padrão: com_cat_2015 (todas as CATs registradas em 2015,
incluindo motivos típico, trajeto e doença do trabalho). O CSV resultante
mantém também a separação por motivo para análise de robustez.

Saída: data/processed/vetor_acidentes_35.csv
       colunas: codigo, nome, vbp_milhoes_RS, acidentes,
                acidentes_tipico, acidentes_trajeto, acidentes_doenca
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


def _read_csv_robust(path: Path, str_cols: tuple[str, ...] = ()) -> pd.DataFrame:
    dtype_map = {c: str for c in str_cols}
    for sep in (",", ";", "\t"):
        try:
            df = pd.read_csv(path, sep=sep, dtype=dtype_map)
            if not df.empty and len(df.columns) > 1:
                return df
        except Exception:
            continue
    return pd.DataFrame()


def _match_de_para(cnae4: str, de_para_index: dict) -> tuple[str, float] | None:
    """Tenta casar pelo prefixo mais longo (3-dig, depois 2-dig)."""
    for length in (4, 3, 2):
        prefix = cnae4[:length]
        if prefix in de_para_index:
            return de_para_index[prefix]
    return None


def _build_from_aeat(sectors: pd.DataFrame) -> pd.DataFrame | None:
    if not (AEAT_RAW_PATH.exists() and AEAT_RAW_PATH.stat().st_size > 0):
        return None
    if not (DE_PARA_PATH.exists() and DE_PARA_PATH.stat().st_size > 0):
        return None

    aeat = _read_csv_robust(AEAT_RAW_PATH, str_cols=("cnae",))
    de_para = _read_csv_robust(DE_PARA_PATH, str_cols=("cnae", "codigo"))
    if aeat.empty or de_para.empty:
        return None

    aeat["cnae"] = aeat["cnae"].astype(str).str.strip().str.zfill(4)
    de_para["cnae"] = de_para["cnae"].astype(str).str.strip()
    de_para["codigo"] = de_para["codigo"].astype(str).str.zfill(4)
    de_para_index = {
        row["cnae"]: (row["codigo"], float(row.get("peso", 1.0) or 1.0))
        for _, row in de_para.iterrows()
    }

    motivos_cols = {
        "acidentes": "com_cat_2015",
        "acidentes_tipico": "tipico_2015",
        "acidentes_trajeto": "trajeto_2015",
        "acidentes_doenca": "doenca_2015",
    }
    base = sectors[["codigo", "nome", "vbp_milhoes_RS"]].copy()
    for out_col in motivos_cols:
        base[out_col] = 0.0

    unmatched_cnae: list[tuple[str, int]] = []
    for _, r in aeat.iterrows():
        match = _match_de_para(r["cnae"], de_para_index)
        if match is None:
            unmatched_cnae.append((r["cnae"], int(r.get("com_cat_2015", 0) or 0)))
            continue
        codigo, peso = match
        mask = base["codigo"] == codigo
        for out_col, src_col in motivos_cols.items():
            base.loc[mask, out_col] += float(r.get(src_col, 0) or 0) * peso

    if unmatched_cnae:
        unmatched_total = sum(q for _, q in unmatched_cnae)
        print(f"[01_data_prep] aviso: {len(unmatched_cnae)} CNAEs sem de-para "
              f"({unmatched_total} CATs ignoradas).")
        for cnae, q in sorted(unmatched_cnae, key=lambda kv: -kv[1])[:5]:
            print(f"  CNAE {cnae}: {q} CATs")

    return base


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
    out["acidentes_tipico"] = out["acidentes"]
    out["acidentes_trajeto"] = 0.0
    out["acidentes_doenca"] = 0.0
    return out


def _build_synthetic(sectors: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(ACCIDENTS_FALLBACK_SEED)
    base = sectors[["codigo", "nome", "vbp_milhoes_RS"]].copy()
    base["acidentes"] = rng.integers(low=80, high=1800, size=N_SETORES).astype(float)
    base["acidentes_tipico"] = base["acidentes"]
    base["acidentes_trajeto"] = 0.0
    base["acidentes_doenca"] = 0.0
    return base


def main() -> None:
    ACCIDENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    sectors = load_sectors()

    aeat = _build_from_aeat(sectors)
    if aeat is not None:
        source = "AEAT-2015 oficial agregado via de_para CNAE→MIP-35"
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
    print(f"[01_data_prep] total CATs no ES (com CAT registrada): {total:,.0f}")
    if "acidentes_tipico" in out.columns:
        print(f"[01_data_prep]   típico:  {out['acidentes_tipico'].sum():,.0f}")
        print(f"[01_data_prep]   trajeto: {out['acidentes_trajeto'].sum():,.0f}")
        print(f"[01_data_prep]   doença:  {out['acidentes_doenca'].sum():,.0f}")
    print(f"[01_data_prep] vetor salvo em: {ACCIDENTS_PATH}")


if __name__ == "__main__":
    main()
