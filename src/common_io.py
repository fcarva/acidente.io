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


def _load_AL_from_ijsn_xlsx() -> tuple[np.ndarray, np.ndarray] | None:
    """Lê A e L diretamente das Tabelas 11 e 12 do XLSX oficial IJSN.

    Layout esperado: cabeçalhos nas linhas 0-4, dados nas linhas 5-39
    (35 setores), colunas 2-36 (35 atividades). Aba "11" = matriz A
    (D.Bn), aba "12" = matriz L (Leontief).
    """
    for excel_path in _candidate_excel_files():
        try:
            xls = pd.ExcelFile(excel_path)
        except Exception:
            continue
        if "11" not in xls.sheet_names or "12" not in xls.sheet_names:
            continue
        try:
            A = pd.read_excel(excel_path, sheet_name="11", header=None).iloc[
                5 : 5 + N_SETORES, 2 : 2 + N_SETORES
            ].to_numpy(dtype=float)
            L = pd.read_excel(excel_path, sheet_name="12", header=None).iloc[
                5 : 5 + N_SETORES, 2 : 2 + N_SETORES
            ].to_numpy(dtype=float)
        except Exception:
            continue
        if A.shape == (N_SETORES, N_SETORES) and L.shape == (N_SETORES, N_SETORES):
            return A, L
    return None


def _load_Z_from_xlsx_legacy() -> np.ndarray | None:
    """Fallback heurístico para XLSX sem aba '11'/'12' nomeadas."""
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
                    if np.diag(block).max() > 1.5:  # heurística: não-Leontief
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

    pair = _load_AL_from_ijsn_xlsx()
    if pair is not None:
        A, L = pair
        Z = A * X[np.newaxis, :]
        Y = np.maximum(X - Z.sum(axis=0), 0.0)
        return Z, A, L, X, Y, sectors, "xlsx_ijsn_oficial_tab11_tab12"

    L = _load_matrix_from_csv(L_CSV_PATH)
    if L is not None:
        A = I - safe_inverse(L)
        A = np.clip(A, 0.0, None)
        Z = A * X[np.newaxis, :]
        Y = np.maximum(X - Z.sum(axis=0), 0.0)
        return Z, A, L, X, Y, sectors, "csv_L_oficial_ijsn"

    Z = _load_Z_from_xlsx_legacy()
    if Z is not None:
        X_safe = np.where(X <= 0, MIN_PRODUCTION_THRESHOLD, X)
        A = Z / X_safe[np.newaxis, :]
        L = safe_inverse(I - A)
        Y = np.maximum(X - Z.sum(axis=0), 0.0)
        return Z, A, L, X, Y, sectors, "xlsx_legacy"

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


Y_COMPONENTS_PATH = DATA_PROC / "y_components_by_sector.csv"

# Mapeamento posicional: cols 39..45 da Tabela 03 (XLSX IJSN, "Oferta e
# demanda de produtos DOMÉSTICOS"). T03 tem coluna extra "Valor da produção"
# na posição 2, deslocando a primeira atividade para a coluna 3 e os
# componentes de demanda final para cols 39..45.
Y_COMPONENT_COLS = [
    ("exp_exterior", 39),
    ("exp_brasil", 40),
    ("gov", 41),
    ("isflsf", 42),
    ("h_familias", 43),
    ("fbkf", 44),
    ("var_estoque", 45),
]


def _aggregate_products_to_sectors(
    df_demand: pd.DataFrame, D: np.ndarray, prod_codes_d: list[str]
) -> dict[str, np.ndarray]:
    """Para cada coluna de demanda em Tabela 03 (DOMÉSTICOS), retorna
    h_setor = D · h_produto.

    Tabela 03 tem produtos nas linhas 5..85 (nível 81). Tabela 10 tem
    81 produtos nas colunas; alguns códigos diferem por 1 dígito (55000
    vs 55001). Alinhamos por prefixo de 4 dígitos.
    """
    rows = df_demand.iloc[5 : 5 + 81].copy()
    rows.columns = list(range(df_demand.shape[1]))
    prod_codes_t = rows[0].astype(str).str.strip().tolist()

    idx_t = []
    for c in prod_codes_d:
        if c in prod_codes_t:
            idx_t.append(prod_codes_t.index(c))
        else:
            base = c[:4]
            matches = [i for i, p in enumerate(prod_codes_t) if p[:4] == base]
            idx_t.append(matches[0] if matches else -1)

    out: dict[str, np.ndarray] = {}
    for name, col in Y_COMPONENT_COLS:
        h_prod = np.zeros(len(prod_codes_d))
        for k, ti in enumerate(idx_t):
            if ti < 0:
                continue
            v = pd.to_numeric(rows.iloc[ti, col], errors="coerce")
            if pd.notna(v):
                h_prod[k] = float(v)
        out[name] = D @ h_prod
    return out


def load_y_components() -> pd.DataFrame | None:
    """Componentes de demanda final por setor (h, FBKF, gov, ISFLSF, exp).

    Cache automática em data/processed/y_components_by_sector.csv após
    a primeira extração do XLSX oficial.
    """
    if Y_COMPONENTS_PATH.exists() and Y_COMPONENTS_PATH.stat().st_size > 0:
        return pd.read_csv(Y_COMPONENTS_PATH, dtype={"codigo": str})

    sectors = load_sectors()
    for excel_path in _candidate_excel_files():
        try:
            xls = pd.ExcelFile(excel_path)
        except Exception:
            continue
        if "03" not in xls.sheet_names or "10" not in xls.sheet_names:
            continue

        df03 = pd.read_excel(excel_path, sheet_name="03", header=None)
        df10 = pd.read_excel(excel_path, sheet_name="10", header=None)

        # D matrix: rows 5..39 (35 sectors), cols 2..82 (81 products).
        D = df10.iloc[5:5 + N_SETORES, 2 : 2 + 81].to_numpy(dtype=float)
        prod_codes_d = []
        hdr = df10.iloc[3].fillna("").astype(str).tolist()
        for i in range(2, 2 + 81):
            tok = hdr[i].strip().split(maxsplit=1)
            prod_codes_d.append(tok[0] if tok else "")

        components = _aggregate_products_to_sectors(df03, D, prod_codes_d)

        out = sectors[["codigo", "nome"]].copy()
        for name, _ in Y_COMPONENT_COLS:
            out[name] = components[name]
        out["y_total"] = sum(out[name] for name, _ in Y_COMPONENT_COLS)
        Y_COMPONENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(Y_COMPONENTS_PATH, index=False)
        return out
    return None


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
