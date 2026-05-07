from pathlib import Path

import numpy as np
import pandas as pd

from common_io import N_SETORES, load_accidents, load_io_data, safe_inverse

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_TABLE = ROOT / "outputs" / "tables" / "resultados_principais.csv"


def main() -> None:
    OUTPUT_TABLE.parent.mkdir(parents=True, exist_ok=True)

    Z, Y, X = load_io_data()
    CAT = load_accidents()

    X_safe = np.where(X <= 0, 1e-9, X)
    A = Z / X_safe[np.newaxis, :]
    I = np.eye(N_SETORES)
    L = safe_inverse(I - A)

    a = CAT / X_safe
    f = a @ L

    total_L = L.sum()
    colsum_L = L.sum(axis=0)
    U = np.where(total_L != 0, N_SETORES * colsum_L / total_L, 0.0)

    resultados = pd.DataFrame(
        {
            "setor_id": np.arange(1, N_SETORES + 1),
            "producao_X": X,
            "demanda_final_Y": Y,
            "acidentes_CAT": CAT,
            "intensidade_direta": a,
            "pegada_estrutural": f,
            "encadeamento_tras": U,
        }
    )

    resultados.to_csv(OUTPUT_TABLE, index=False)
    print(f"Resultados principais salvos em: {OUTPUT_TABLE}")


if __name__ == "__main__":
    main()
