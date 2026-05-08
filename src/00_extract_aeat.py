"""
Extrai a Tabela 19.1 do AEAT-2015 (acidentes do trabalho por CNAE no
estado do Espírito Santo) e produz dois artefatos:

    data/raw/aeat15_es_subsecao_a.csv    (CNAE 4-dig + colunas por motivo/ano)
    data/processed/aeat15_es_resumo.csv  (resumo por divisão CNAE 2-dig, 2015)

Fonte: aeat15tab.zip (MPS/MTE) — capítulo 19, sub-tabela 19.1.
Use os arquivos descompactados em data/raw/aeat15tab/.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AEAT_XLS = ROOT / "data" / "raw" / "aeat15tab" / "15Act19_01.xls"
RAW_CSV = ROOT / "data" / "raw" / "aeat15_es_subsecao_a.csv"
SUMMARY_CSV = ROOT / "data" / "processed" / "aeat15_es_resumo.csv"

COL_NAMES = [
    "cnae",
    "total_2013", "total_2014", "total_2015",
    "com_cat_2013", "com_cat_2014", "com_cat_2015",
    "tipico_2013", "tipico_2014", "tipico_2015",
    "trajeto_2013", "trajeto_2014", "trajeto_2015",
    "doenca_2013", "doenca_2014", "doenca_2015",
    "sem_cat_2013", "sem_cat_2014", "sem_cat_2015",
]


def main() -> None:
    if not AEAT_XLS.exists():
        raise FileNotFoundError(
            f"Tabela AEAT não encontrada: {AEAT_XLS}. "
            "Descompacte aeat15tab.zip em data/raw/aeat15tab/ antes."
        )

    df = pd.read_excel(AEAT_XLS, sheet_name=0, header=None)
    rows = df.iloc[12:].copy()
    rows.columns = COL_NAMES + list(rows.columns[len(COL_NAMES):])
    rows = rows[rows["cnae"].astype(str).str.match(r"^\s*\d{4}\s*$", na=False)].copy()
    rows["cnae"] = rows["cnae"].astype(str).str.strip().str.zfill(4)

    numeric_cols = COL_NAMES[1:]
    for c in numeric_cols:
        rows[c] = pd.to_numeric(rows[c], errors="coerce").fillna(0).astype(int)

    rows = rows[COL_NAMES].reset_index(drop=True)
    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(RAW_CSV, index=False)

    rows["divisao"] = rows["cnae"].str[:2]
    summary = (
        rows.groupby("divisao")[
            ["com_cat_2015", "tipico_2015", "trajeto_2015", "doenca_2015"]
        ]
        .sum()
        .reset_index()
        .sort_values("com_cat_2015", ascending=False)
    )
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_CSV, index=False)

    print(f"[00_extract_aeat] CNAEs 4-dig: {len(rows)}")
    print(f"[00_extract_aeat] total ES 2015 com_cat: {rows['com_cat_2015'].sum():,}")
    print(f"[00_extract_aeat] total ES 2015 típico:  {rows['tipico_2015'].sum():,}")
    print(f"[00_extract_aeat] total ES 2015 trajeto: {rows['trajeto_2015'].sum():,}")
    print(f"[00_extract_aeat] total ES 2015 doença:  {rows['doenca_2015'].sum():,}")
    print(f"[00_extract_aeat] CSV bruto    -> {RAW_CSV}")
    print(f"[00_extract_aeat] resumo divisão -> {SUMMARY_CSV}")


if __name__ == "__main__":
    main()
