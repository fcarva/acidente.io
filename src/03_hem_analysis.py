from pathlib import Path

import numpy as np
import pandas as pd

from common_io import N_SETORES, load_accidents, load_io_data, safe_inverse

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_TABLE = ROOT / "outputs" / "tables" / "extracao_hipotetica.csv"


def main() -> None:
    OUTPUT_TABLE.parent.mkdir(parents=True, exist_ok=True)

    Z, Y, X = load_io_data()
    CAT = load_accidents()

    X_safe = np.where(X <= 0, 1e-9, X)
    A = Z / X_safe[np.newaxis, :]
    I = np.eye(N_SETORES)

    a = CAT / X_safe
    acidentes_base = float(a @ X_safe)

    resultados = []
    for k in range(N_SETORES):
        A_star = A.copy()
        A_star[k, :] = 0.0
        A_star[:, k] = 0.0

        L_star = safe_inverse(I - A_star)
        X_star = L_star @ Y

        acidentes_star = float(a @ X_star)
        delta_cat = acidentes_base - acidentes_star

        resultados.append(
            {
                "setor_id": k + 1,
                "acidentes_base": acidentes_base,
                "acidentes_pos_extracao": acidentes_star,
                "reducao_sistemica_acidentes": delta_cat,
            }
        )

    pd.DataFrame(resultados).to_csv(OUTPUT_TABLE, index=False)
    print(f"Resultados de extração hipotética salvos em: {OUTPUT_TABLE}")


if __name__ == "__main__":
    main()
