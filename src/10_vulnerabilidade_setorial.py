"""
Bloco C — Vulnerabilidade socioeconômica dos trabalhadores por setor
=====================================================================
Cruza a pegada de acidentes f_j (MIP-ES 2015) com o Índice de
Vulnerabilidade Multidimensional Não-Monetário (IVM-NM) da POF 2017-2018
para identificar setores onde alto risco de acidente coincide com alta
vulnerabilidade socioeconômica dos trabalhadores.

Metodologia:
  1. Extrai IVM-NM por classe ocupacional (Tabela 1b) e por UF (Tabela 5b)
     da POF 2017-2018 (IBGE).
  2. Para cada setor MIP-ES, atribui um perfil de classe ocupacional proxy
     (composição estimada de Empregado Privado, Conta própria, Doméstico,
     Militar/público, Empregador) com base em RAIS-ES 2015 e PNAD-C.
  3. Calcula vulnerabilidade média setorial:
        V_j = Σ_k  w_{jk} × IVM_k    (k ∈ classes ocupacionais)
  4. Compõe indicador socialmente ponderado:
        C_j = f_j × V_j   (pegada × vulnerabilidade)
  5. Foco analítico: setores extrativistas (0580, 0680, 0791).

Limitação: os perfis ocupacionais são proxies baseadas em literatura e RAIS
agregada; revisão recomendada com microdados PNAD-C / RAIS-ES por setor.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT = Path(__file__).resolve().parent.parent
DATA_POF = ROOT / "data" / "raw" / "pof"
PROC = ROOT / "data" / "processed"
OUT_FIG = ROOT / "outputs" / "figures"
OUT_TAB = ROOT / "outputs" / "tables"

# ─── IVM-NM por classe ocupacional (Tabela 1b, POF 2017-2018, Brasil) ────────
IVM_CLASSE = {
    "empregado_privado":  6.17074325,
    "conta_propria":      9.39415872,
    "domestico":         11.35981865,
    "militar_publico":    4.12676005,
    "empregador":         2.81832447,
    "fora_pea":           9.07804070,
}

# IVM-NM Espírito Santo (Tabela 5b, POF 2017-2018)
IVM_ES = 5.85302246

# ─── Perfis ocupacionais proxy por setor MIP-ES 35 ───────────────────────────
# (empregado_privado, conta_propria, domestico, militar_publico, empregador)
# Fonte: RAIS-ES 2015 (CAGED), PNAD-C 2015 (tabulação por seção CNAE 2.0)
PERFIL_OCUPACIONAL = {
    "0191": (0.35, 0.60, 0.00, 0.00, 0.05),  # Agricultura — predomina conta própria
    "0192": (0.35, 0.60, 0.00, 0.00, 0.05),  # Pecuária
    "0280": (0.45, 0.50, 0.00, 0.00, 0.05),  # Florestal/pesca
    "0580": (0.85, 0.10, 0.00, 0.00, 0.05),  # Extração mineral não-metálica — formal
    "0680": (0.88, 0.05, 0.00, 0.05, 0.02),  # Petróleo e gás — altamente formal
    "0791": (0.85, 0.10, 0.00, 0.00, 0.05),  # Minério de ferro — formal
    "1000": (0.82, 0.12, 0.00, 0.00, 0.06),  # Alimentos e bebidas
    "1300": (0.78, 0.16, 0.00, 0.00, 0.06),  # Têxtil/vestuário/couro
    "1600": (0.68, 0.26, 0.00, 0.00, 0.06),  # Madeira/móveis
    "1700": (0.85, 0.09, 0.00, 0.00, 0.06),  # Celulose e papel
    "1900": (0.88, 0.06, 0.00, 0.00, 0.06),  # Refino de petróleo
    "2000": (0.84, 0.10, 0.00, 0.00, 0.06),  # Químicos/borracha/plástico
    "2300": (0.80, 0.14, 0.00, 0.00, 0.06),  # Minerais não-metálicos
    "2400": (0.88, 0.07, 0.00, 0.00, 0.05),  # Metalurgia
    "2500": (0.82, 0.12, 0.00, 0.00, 0.06),  # Prod. metal/máquinas
    "2900": (0.85, 0.09, 0.00, 0.00, 0.06),  # Automóveis/transporte
    "3500": (0.80, 0.10, 0.00, 0.08, 0.02),  # Energia/água/saneamento
    "4180": (0.60, 0.35, 0.00, 0.00, 0.05),  # Construção — alta informalidade
    "4500": (0.60, 0.30, 0.00, 0.00, 0.10),  # Comércio
    "4900": (0.55, 0.40, 0.00, 0.00, 0.05),  # Transporte — autônomos relevantes
    "5280": (0.75, 0.20, 0.00, 0.00, 0.05),  # Armazenamento/auxiliar
    "5500": (0.50, 0.40, 0.00, 0.00, 0.10),  # Alojamento/alimentação
    "5800": (0.70, 0.20, 0.00, 0.00, 0.10),  # Informação
    "6480": (0.80, 0.05, 0.00, 0.10, 0.05),  # Financeiro
    "6800": (0.40, 0.50, 0.00, 0.00, 0.10),  # Imobiliário
    "6900": (0.50, 0.40, 0.00, 0.00, 0.10),  # Profissional/técnico
    "7800": (0.85, 0.10, 0.00, 0.00, 0.05),  # Administrativo
    "8400": (0.15, 0.05, 0.00, 0.78, 0.02),  # Adm. pública
    "8591": (0.08, 0.03, 0.00, 0.87, 0.02),  # Educação pública
    "8592": (0.80, 0.10, 0.00, 0.05, 0.05),  # Educação privada
    "8691": (0.12, 0.03, 0.00, 0.83, 0.02),  # Saúde pública
    "8692": (0.76, 0.14, 0.00, 0.05, 0.05),  # Saúde privada
    "9080": (0.40, 0.50, 0.00, 0.00, 0.10),  # Artes/cultura
    "9480": (0.45, 0.45, 0.00, 0.00, 0.10),  # Serviços pessoais
    "9700": (0.05, 0.05, 0.88, 0.00, 0.02),  # Serviços domésticos
}

CLASSES = ["empregado_privado", "conta_propria", "domestico", "militar_publico", "empregador"]


# ─────────────────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    df = pd.read_csv(PROC / "pegada_genero_es.csv", dtype={"codigo": str})
    df["codigo"] = df["codigo"].str.zfill(4)
    return df


def extract_ivm_classes() -> pd.DataFrame:
    """Extrai IVM-NM por classe ocupacional da Tabela 1b (POF 2017-2018)."""
    try:
        raw = pd.read_excel(DATA_POF / "Tabela 1b.xlsx", header=None)
        row_map = {
            "Empregado doméstico": "domestico",
            "Empregado Privado": "empregado_privado",
            "Militar e empregado do setor público": "militar_publico",
            "Conta própria": "conta_propria",
            "Empregador": "empregador",
        }
        out = {}
        for _, row in raw.iterrows():
            label = str(row[0]).strip()
            if label in row_map and pd.notna(row[3]):
                out[row_map[label]] = float(row[3])
        if len(out) == 5:
            return pd.Series(out, name="ivm_nm")
    except Exception:
        pass
    return pd.Series(IVM_CLASSE, name="ivm_nm")


def extract_ivm_decis() -> pd.DataFrame:
    """Extrai IVM-NM por décimo de renda da Tabela 1b."""
    try:
        raw = pd.read_excel(DATA_POF / "Tabela 1b.xlsx", header=None)
        decis = []
        for _, row in raw.iterrows():
            label = str(row[0]).strip()
            if label.endswith("º") and pd.notna(row[3]):
                decis.append({"decil": label, "ivm_nm": float(row[3])})
        if len(decis) == 10:
            return pd.DataFrame(decis)
    except Exception:
        pass
    return pd.DataFrame({
        "decil": [f"{i}º" for i in range(1, 11)],
        "ivm_nm": [17.95, 13.24, 10.95, 9.10, 7.55, 6.30, 5.01, 3.57, 2.45, 0.83],
    })


def compute_sector_vulnerability(df: pd.DataFrame, ivm_series: pd.Series) -> pd.DataFrame:
    """Calcula V_j = Σ_k w_{jk} × IVM_k para cada setor."""
    records = []
    for _, row in df.iterrows():
        cod = row["codigo"]
        weights = PERFIL_OCUPACIONAL.get(cod, (0.70, 0.20, 0.00, 0.05, 0.05))
        w = dict(zip(CLASSES, weights))
        v_j = sum(w[c] * ivm_series.get(c, IVM_CLASSE[c]) for c in CLASSES)
        records.append({
            "codigo": cod,
            "V_j": v_j,
            "w_emp_privado": w["empregado_privado"],
            "w_conta_propria": w["conta_propria"],
            "w_domestico": w["domestico"],
            "w_militar_pub": w["militar_publico"],
            "w_empregador": w["empregador"],
        })
    return pd.DataFrame(records)


def build_composite(df: pd.DataFrame, vuln: pd.DataFrame) -> pd.DataFrame:
    """Mescla pegada e vulnerabilidade; compõe C_j = f_total × V_j."""
    merged = df.merge(vuln, on="codigo", how="left")
    merged["C_j"] = merged["f_total"] * merged["V_j"]
    merged["C_j_F"] = merged["f_F"] * merged["V_j"]
    merged["C_j_M"] = merged["f_M"] * merged["V_j"]
    return merged


# ─── Gráficos ────────────────────────────────────────────────────────────────

def plot_composite_ranking(df: pd.DataFrame, out: Path) -> None:
    """Ranking top-20 setores pelo indicador composto C_j."""
    top = df.nlargest(20, "C_j").copy()
    top["nome_curto"] = top["nome"].str[:38]

    EXTR = {"0580", "0680", "0791", "0191", "0192", "0280"}
    colors = ["#C0392B" if c in EXTR else "#2980B9" for c in top["codigo"]]

    fig, ax = plt.subplots(figsize=(10, 7))
    y = range(len(top))
    bars = ax.barh(list(y), top["C_j"].values, color=colors, alpha=0.85)
    ax.set_yticks(list(y))
    ax.set_yticklabels(top["nome_curto"].tolist(), fontsize=8)
    ax.set_xlabel("$C_j = f_j \\times V_j$  (pegada × vulnerabilidade IVM-NM)", fontsize=9)
    ax.set_title(
        "Indicador composto: pegada de acidentes × vulnerabilidade socioeconômica\n"
        "MIP-ES 2015 × POF 2017-2018 (IVM-NM Brasil)",
        fontsize=10,
    )
    patch_extr = mpatches.Patch(color="#C0392B", alpha=0.85, label="Setor extrativista/primário")
    patch_rest = mpatches.Patch(color="#2980B9", alpha=0.85, label="Demais setores")
    ax.legend(handles=[patch_extr, patch_rest], fontsize=8)
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Figura salva: {out}")


def plot_footprint_vs_vulnerability(df: pd.DataFrame, out: Path) -> None:
    """Dispersão f_j × V_j com quadrantes e destaque extrativistas."""
    EXTR = {"0580", "0680", "0791"}
    PRIMARIO = {"0191", "0192", "0280"}

    fig, ax = plt.subplots(figsize=(9, 7))

    mask_extr = df["codigo"].isin(EXTR)
    mask_prim = df["codigo"].isin(PRIMARIO)
    mask_rest = ~(mask_extr | mask_prim)

    ax.scatter(
        df.loc[mask_rest, "V_j"], df.loc[mask_rest, "f_total"],
        s=df.loc[mask_rest, "vbp_milhoes_RS"] / df["vbp_milhoes_RS"].max() * 600 + 20,
        color="#7FB3D3", alpha=0.6, edgecolors="grey", linewidths=0.4, label="Outros setores",
    )
    ax.scatter(
        df.loc[mask_prim, "V_j"], df.loc[mask_prim, "f_total"],
        s=df.loc[mask_prim, "vbp_milhoes_RS"] / df["vbp_milhoes_RS"].max() * 600 + 40,
        color="#F39C12", alpha=0.85, edgecolors="grey", linewidths=0.6, label="Primário (agro/floresta)",
        marker="D",
    )
    ax.scatter(
        df.loc[mask_extr, "V_j"], df.loc[mask_extr, "f_total"],
        s=df.loc[mask_extr, "vbp_milhoes_RS"] / df["vbp_milhoes_RS"].max() * 600 + 60,
        color="#C0392B", alpha=0.9, edgecolors="black", linewidths=0.8, label="Extrativismo mineral/petróleo",
        marker="^", zorder=5,
    )

    # Linhas de referência nas medianas
    med_v = df["V_j"].median()
    med_f = df["f_total"].median()
    ax.axvline(med_v, color="grey", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.axhline(med_f, color="grey", linestyle="--", linewidth=0.8, alpha=0.6)

    # Rótulos para extrativistas e outliers
    thresh_f = df["f_total"].quantile(0.75)
    thresh_v = df["V_j"].quantile(0.75)
    label_mask = (df["f_total"] > thresh_f) | (df["V_j"] > thresh_v) | mask_extr | mask_prim
    for _, row in df[label_mask].iterrows():
        ax.annotate(
            row["nome"][:22], (row["V_j"], row["f_total"]),
            fontsize=6, alpha=0.85, xytext=(4, 3), textcoords="offset points",
        )

    # Anotações de quadrante
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    ax.text(xmin + 0.1, ymax - 0.02 * (ymax - ymin), "Alto risco,\nbaixa vulner.",
            fontsize=7, color="grey", va="top")
    ax.text(xmax - 0.3 * (xmax - xmin), ymax - 0.02 * (ymax - ymin), "Alto risco,\nalta vulner.",
            fontsize=7, color="#C0392B", va="top", fontweight="bold")
    ax.text(xmin + 0.1, ymin + 0.02 * (ymax - ymin), "Baixo risco,\nbaixa vulner.",
            fontsize=7, color="grey")
    ax.text(xmax - 0.3 * (xmax - xmin), ymin + 0.02 * (ymax - ymin), "Baixo risco,\nalta vulner.",
            fontsize=7, color="#7F8C8D")

    ax.set_xlabel("Vulnerabilidade média dos trabalhadores $V_j$ (IVM-NM)", fontsize=9)
    ax.set_ylabel("Pegada de acidentes $f_j$ (CATs / R\\$M demanda final)", fontsize=9)
    ax.set_title(
        "Mapa de risco: pegada de acidentes × vulnerabilidade socioeconômica\n"
        "Tamanho = VBP setorial — MIP-ES 2015 × POF 2017-2018",
        fontsize=10,
    )
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Figura salva: {out}")


def plot_ivm_decil(decis: pd.DataFrame, out: Path) -> None:
    """IVM-NM por décimo de renda — contexto distributivo."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(decis["decil"], decis["ivm_nm"], color="#8E44AD", alpha=0.80)
    ax.set_xlabel("Décimo de renda familiar per capita", fontsize=9)
    ax.set_ylabel("IVM-NM", fontsize=9)
    ax.set_title(
        "Índice de Vulnerabilidade Multidimensional por décimo de renda\n"
        "POF 2017-2018, Brasil",
        fontsize=10,
    )
    ax.axhline(decis["ivm_nm"].mean(), color="grey", linestyle="--", linewidth=0.8,
               label=f"Média = {decis['ivm_nm'].mean():.2f}")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Figura salva: {out}")


def plot_extractive_profile(df: pd.DataFrame, out: Path) -> None:
    """Perfil comparativo: extrativistas × média da economia."""
    EXTR_CODES = ["0580", "0680", "0791"]
    extr = df[df["codigo"].isin(EXTR_CODES)].set_index("codigo")
    media = df[["f_total", "V_j", "C_j", "a_j"]].mean()

    metrics = ["a_j", "f_total", "V_j", "C_j"]
    labels = ["$a_j$ (intens. direta)", "$f_j$ (pegada IO)", "$V_j$ (vulnerab.)", "$C_j$ (composto)"]
    nomes = {
        "0580": "Extração\nmineral",
        "0680": "Petróleo\ne gás",
        "0791": "Minério\nde ferro",
    }
    colors_extr = ["#C0392B", "#E67E22", "#8E44AD"]

    x = np.arange(len(metrics))
    width = 0.20

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, (cod, cor) in enumerate(zip(EXTR_CODES, colors_extr)):
        if cod not in extr.index:
            continue
        vals = [extr.loc[cod, m] / media[m] for m in metrics]
        ax.bar(x + i * width, vals, width, label=nomes[cod], color=cor, alpha=0.85)

    ax.axhline(1.0, color="grey", linestyle="--", linewidth=0.9, label="Média da economia = 1")
    ax.set_xticks(x + width)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Razão em relação à média da economia", fontsize=9)
    ax.set_title(
        "Setores extrativistas: indicadores relativos à média — ES 2015\n"
        "Fonte: MIP-ES 2015 / POF 2017-2018 / AEAT-ES 2015",
        fontsize=10,
    )
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Figura salva: {out}")


# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=== Bloco C: Vulnerabilidade socioeconômica dos trabalhadores por setor ===")

    df = load_data()
    ivm_classes = extract_ivm_classes()
    ivm_decis = extract_ivm_decis()

    print("\nIVM-NM por classe ocupacional (POF 2017-2018, Brasil):")
    for k, v in ivm_classes.items():
        print(f"  {k:<25} = {v:.4f}")
    print(f"\nIVM-NM Espírito Santo = {IVM_ES:.4f}  (Brasil = 7.6963)")

    vuln = compute_sector_vulnerability(df, ivm_classes)
    comp = build_composite(df, vuln)

    print(f"\nVulnerabilidade média setorial V_j:")
    print(f"  Média ponderada (VBP) = "
          f"{(comp['V_j'] * comp['vbp_milhoes_RS']).sum() / comp['vbp_milhoes_RS'].sum():.4f}")
    print(f"  Mín = {comp['V_j'].min():.4f}  ({comp.loc[comp['V_j'].idxmin(), 'nome'][:40]})")
    print(f"  Máx = {comp['V_j'].max():.4f}  ({comp.loc[comp['V_j'].idxmax(), 'nome'][:40]})")

    print("\n--- Setores extrativistas ---")
    EXTR_CODES = ["0580", "0680", "0791"]
    media_f = comp["f_total"].mean()
    media_v = comp["V_j"].mean()
    media_c = comp["C_j"].mean()
    for cod in EXTR_CODES:
        row = comp[comp["codigo"] == cod]
        if row.empty:
            continue
        row = row.iloc[0]
        print(f"\n  {row['nome'][:55]}")
        print(f"    a_j={row['a_j']:.4f}  f_j={row['f_total']:.4f} ({row['f_total']/media_f:.1f}× média)")
        print(f"    V_j={row['V_j']:.4f} ({row['V_j']/media_v:.2f}× média)  "
              f"C_j={row['C_j']:.4f} ({row['C_j']/media_c:.2f}× média)")
        wep = row["w_emp_privado"] * 100
        wcp = row["w_conta_propria"] * 100
        print(f"    Perfil ocup.: emp.privado={wep:.0f}%, conta-própria={wcp:.0f}%")

    print("\nTop-15 setores pelo indicador composto C_j:")
    top15 = comp.nlargest(15, "C_j")[
        ["codigo", "nome", "a_j", "f_total", "V_j", "C_j"]
    ].copy()
    top15["nome"] = top15["nome"].str[:40]
    print(top15.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    # Salvar
    out_csv = PROC / "vulnerabilidade_setorial.csv"
    comp.to_csv(out_csv, index=False, float_format="%.6f")
    print(f"\nSalvo: {out_csv}")

    ivm_decis.to_csv(PROC / "ivm_decis_pof.csv", index=False, float_format="%.6f")

    # Figuras
    plot_composite_ranking(comp, OUT_FIG / "composite_risco_vulnerabilidade.pdf")
    plot_footprint_vs_vulnerability(comp, OUT_FIG / "mapa_risco_vulnerabilidade.pdf")
    plot_ivm_decil(ivm_decis, OUT_FIG / "ivm_decil_pof.pdf")
    plot_extractive_profile(comp, OUT_FIG / "extrativistas_perfil_comparativo.pdf")

    print("\n=== Concluído ===")


if __name__ == "__main__":
    main()
