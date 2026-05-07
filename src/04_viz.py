from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "outputs" / "tables" / "resultados_principais.csv"
OUTPUT_PATH = ROOT / "outputs" / "figures" / "quadrante_risco_es.pdf"


def main() -> None:
    if not INPUT_PATH.exists() or INPUT_PATH.stat().st_size == 0:
        raise FileNotFoundError(
            f"Arquivo de resultados não encontrado ou vazio: {INPUT_PATH}. Execute o 02_io_model.py antes."
        )

    df = pd.read_csv(INPUT_PATH)
    required = {"setor_id", "intensidade_direta", "encadeamento_tras"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes em resultados_principais.csv: {sorted(missing)}")

    x = pd.to_numeric(df["encadeamento_tras"], errors="coerce")
    y = pd.to_numeric(df["intensidade_direta"], errors="coerce")
    labels = df["setor_id"].astype(str)

    x_mean = x.mean()
    y_mean = y.mean()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 7))
    plt.scatter(x, y, alpha=0.8, s=50)

    for xi, yi, lbl in zip(x, y, labels):
        plt.annotate(lbl, (xi, yi), textcoords="offset points", xytext=(4, 4), fontsize=7)

    plt.axvline(x=x_mean, color="tab:red", linestyle="--", linewidth=1)
    plt.axhline(y=y_mean, color="tab:red", linestyle="--", linewidth=1)

    plt.title("Quadrantes de Risco: Intensidade Direta vs Encadeamento para Trás")
    plt.xlabel("Encadeamento para Trás (U_j)")
    plt.ylabel("Intensidade Direta de Acidentes")
    plt.grid(alpha=0.25)
    plt.tight_layout()

    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Figura salva em: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
