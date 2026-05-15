"""
Comparativo Brasil x Espírito Santo
- Lê MIP-Brasil 2015 (IBGE, 67 atividades) e AEAT-2015 nacional
- Agrega ao taxonomia da MIP-ES (35 setores)
- Computa a^BR, VBP^BR, taxa CAT/VBP
- Decompõe o diferencial ES/BR em efeito-composição e efeito-intensidade
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_BR = ROOT / "data" / "raw" / "br"
PROCESSED = ROOT / "data" / "processed"

# ─────────────────────────────────────────────────────────────────────
# Mapeamento BR-67 → ES-35 (códigos IBGE/SCN)
# ─────────────────────────────────────────────────────────────────────
BR67_TO_ES35 = {
    "0191": "0191", "0192": "0192", "0280": "0280", "0580": "0580",
    "0680": "0680", "0791": "0791", "0792": "0580",
    "1091": "1000", "1092": "1000", "1093": "1000",
    "1100": "1000", "1200": "1000",
    "1300": "1300", "1400": "1300", "1500": "1300",
    "1600": "1600", "1700": "1700", "1800": "1700",
    "1991": "1900", "1992": "1900",
    "2091": "2000", "2092": "2000", "2093": "2000",
    "2100": "2000", "2200": "2000",
    "2300": "2300",
    "2491": "2400", "2492": "2400",
    "2500": "2500", "2600": "2500", "2700": "2500", "2800": "2500",
    "2991": "2900", "2992": "2900", "3000": "2900",
    "3180": "1600", "3300": "2500",
    "3500": "3500", "3680": "3500",
    "4180": "4180", "4580": "4500", "4900": "4900",
    "5000": "4900", "5100": "4900", "5280": "5280",
    "5500": "5500", "5600": "5500",
    "5800": "5800", "5980": "5800", "6100": "5800", "6280": "5800",
    "6480": "6480", "6800": "6800",
    "6980": "6900", "7180": "6900", "7380": "6900", "7700": "6900",
    "7880": "7800", "8000": "7800",
    "8400": "8400", "8591": "8591", "8592": "8592",
    "8691": "8691", "8692": "8692",
    "9080": "9080", "9480": "9480", "9700": "9700",
}


def load_mip_br_vbp() -> pd.DataFrame:
    """Lê VBP por atividade da MIP-Brasil 2015 Tab 01 (linha 'Total')."""
    df = pd.read_excel(RAW_BR / "MIP_Brasil_2015_N67.xls", sheet_name="01", header=None)
    records = []
    for col in range(7, df.shape[1]):
        hdr = df.iloc[3, col]
        if pd.isna(hdr):
            continue
        code = str(hdr).split("\n")[0].strip()
        if not code or code.lower() == "total":
            continue
        vbp = df.iloc[133, col]
        records.append({"codigo_br67": code, "vbp_milhoes_BR": float(vbp)})
    return pd.DataFrame(records)


def load_aeat_br() -> pd.DataFrame:
    """Lê AEAT-2015 nacional Tab 1.1 — CATs com registro por CNAE, 2015.

    Usa coluna 6 (Com CAT Registrada 2015), consistente com o lado ES que
    também conta apenas acidentes com CAT emitida.
    Layout: col 0=CNAE; cols 1-3=Total (2013/14/15); cols 4-6=Com CAT (2013/14/15).
    """
    df = pd.read_excel(
        RAW_BR / "aeat15_br" / "15Act01_01.xls", sheet_name=0, header=None
    )
    records = []
    for r in range(12, df.shape[0]):
        cnae = df.iloc[r, 0]
        cat_reg = df.iloc[r, 6]  # col 6 = Com CAT Registrada 2015
        if pd.isna(cnae) or pd.isna(cat_reg):
            continue
        cnae_s = str(cnae).strip()
        if not cnae_s.isdigit() or len(cnae_s) != 4:
            continue
        records.append({"cnae4": cnae_s, "cat_total_2015": int(cat_reg)})
    return pd.DataFrame(records)


def cnae4_to_es35(cnae: str) -> str | None:
    """Mapeia CNAE 4-dig do AEAT para setor MIP-ES 35 via prefixos."""
    # Adapta a tabela de-para já existente; aqui usa o prefixo de 2 dígitos
    # alinhado com a estrutura SCN/MIP-ES.
    c2 = cnae[:2]
    c3 = cnae[:3] if len(cnae) >= 3 else cnae
    # CNAE 01 split: 011-013/016 = agricultura (0191); 014-015/017 = pecuária (0192)
    if c2 == "01":
        return "0191" if c3 in ("011", "012", "013", "016", "019") else "0192"
    table = {
        "02": "0280", "03": "0280",
        "05": "0580", "06": "0680",
        "07": "0791" if cnae.startswith("0710") else "0580",
        "08": "0580", "09": "0580",
        "10": "1000", "11": "1000", "12": "1000",
        "13": "1300", "14": "1300", "15": "1300",
        "16": "1600", "17": "1700", "18": "1700",
        "19": "1900",
        "20": "2000", "21": "2000", "22": "2000",
        "23": "2300", "24": "2400",
        "25": "2500", "26": "2500", "27": "2500", "28": "2500",
        "29": "2900", "30": "2900",
        "31": "1600", "32": "1600", "33": "2500",
        "35": "3500", "36": "3500", "37": "3500", "38": "3500", "39": "3500",
        "41": "4180", "42": "4180", "43": "4180",
        "45": "4500", "46": "4500", "47": "4500",
        "49": "4900", "50": "4900", "51": "4900",
        "52": "5280", "53": "5280",
        "55": "5500", "56": "5500",
        "58": "5800", "59": "5800", "60": "5800",
        "61": "5800", "62": "5800", "63": "5800",
        "64": "6480", "65": "6480", "66": "6480",
        "68": "6800",
        "69": "6900", "70": "6900", "71": "6900", "72": "6900",
        "73": "6900", "74": "6900", "75": "6900",
        "77": "7800", "78": "7800", "79": "7800", "80": "7800",
        "81": "7800", "82": "7800",
        "84": "8400", "85": "8591",  # default educação→pública, refina abaixo
        "86": "8691",  # default saúde→pública
        "87": "8691", "88": "8691",
        "90": "9080", "91": "9080", "92": "9080", "93": "9080",
        "94": "9480", "95": "9480", "96": "9480",
        "97": "9700", "98": "9700",
    }
    # Refinamento: CNAEs 85xx e 86xx
    if c2 == "85":
        # 8511..8520 = ensino fundamental/médio público; 8531..8550 = superior
        # Para simplificação: códigos terminados em ímpar=público em 8591/8691
        # já estão agregados no AEAT por CNAE 4-dig; não temos sublinhas.
        # Usamos 8592 (privado) como default razoável para AEAT (RGPS=privado).
        return "8592"
    if c2 == "86":
        return "8692"
    return table.get(c2)


def main() -> None:
    print("=== Carregando dados nacionais ===")
    vbp_br = load_mip_br_vbp()
    cat_br = load_aeat_br()
    setores_es = pd.read_csv(PROCESSED / "mip_es_setores.csv", dtype={"codigo": str})
    print(f"  MIP-BR: {len(vbp_br)} atividades, VBP total = R${vbp_br['vbp_milhoes_BR'].sum()/1e6:.2f} tri")
    print(f"  AEAT-BR: {len(cat_br)} CNAEs 4-dig, total CATs 2015 = {cat_br['cat_total_2015'].sum():,}")

    # 1) Agregar VBP BR-67 → ES-35
    vbp_br["codigo"] = vbp_br["codigo_br67"].map(BR67_TO_ES35)
    if vbp_br["codigo"].isna().any():
        print("AVISO: códigos sem mapeamento:", vbp_br[vbp_br["codigo"].isna()])
    vbp_br_es35 = (
        vbp_br.dropna(subset=["codigo"])
        .groupby("codigo", as_index=False)["vbp_milhoes_BR"].sum()
    )

    # 2) Agregar CAT BR (CNAE-4) → ES-35
    cat_br["codigo"] = cat_br["cnae4"].apply(cnae4_to_es35)
    if cat_br["codigo"].isna().any():
        sem = cat_br[cat_br["codigo"].isna()]["cnae4"].unique()
        print(f"AVISO: {len(sem)} CNAEs sem mapeamento, CATs perdidos: {cat_br[cat_br['codigo'].isna()]['cat_total_2015'].sum()}")
    cat_br_es35 = (
        cat_br.dropna(subset=["codigo"])
        .groupby("codigo", as_index=False)["cat_total_2015"].sum()
        .rename(columns={"cat_total_2015": "cat_BR"})
    )

    # 3) Vetor ES (do projeto)
    vetor_es = pd.read_csv(PROCESSED / "vetor_acidentes_35.csv", dtype={"codigo": str})
    print(f"  ES: {len(setores_es)} setores; CATs total = {vetor_es['acidentes'].sum():,.0f}")

    # 4) Construir tabela comparativa
    comp = (
        setores_es[["codigo", "nome", "vbp_milhoes_RS"]]
        .rename(columns={"vbp_milhoes_RS": "vbp_ES"})
        .merge(vbp_br_es35, on="codigo", how="left")
        .merge(cat_br_es35, on="codigo", how="left")
        .merge(vetor_es[["codigo", "acidentes"]].rename(columns={"acidentes": "cat_ES"}),
               on="codigo", how="left")
    )
    comp["a_ES"] = comp["cat_ES"] / comp["vbp_ES"]
    comp["a_BR"] = comp["cat_BR"] / comp["vbp_milhoes_BR"]
    comp["razao_a_ES_BR"] = comp["a_ES"] / comp["a_BR"]
    comp["share_VBP_ES"] = comp["vbp_ES"] / comp["vbp_ES"].sum()
    comp["share_VBP_BR"] = comp["vbp_milhoes_BR"] / comp["vbp_milhoes_BR"].sum()
    comp["diff_share_pp"] = (comp["share_VBP_ES"] - comp["share_VBP_BR"]) * 100

    # 5) Decomposição shift-share da taxa agregada
    # Sectores sem a_BR recebem cat_BR=0 → a_BR=0 (zero acidentes registrados naquele setor
    # no âmbito nacional após a agregação); recalcula shares sobre TODOS os 35 setores para
    # que os três componentes somem exatamente Δā = ā_ES − ā_BR.
    comp["a_BR"] = comp["a_BR"].fillna(0.0)
    comp["share_VBP_ES"] = comp["vbp_ES"] / comp["vbp_ES"].sum()
    comp["share_VBP_BR"] = comp["vbp_milhoes_BR"].fillna(0.0) / comp["vbp_milhoes_BR"].fillna(0.0).sum()
    a_es_agg = (comp["share_VBP_ES"] * comp["a_ES"].fillna(0.0)).sum()
    a_br_agg = (comp["share_VBP_BR"] * comp["a_BR"]).sum()
    ef_comp = ((comp["share_VBP_ES"] - comp["share_VBP_BR"]) * comp["a_BR"]).sum()
    ef_int = (comp["share_VBP_BR"] * (comp["a_ES"].fillna(0.0) - comp["a_BR"])).sum()
    ef_inter = (
        (comp["share_VBP_ES"] - comp["share_VBP_BR"])
        * (comp["a_ES"].fillna(0.0) - comp["a_BR"])
    ).sum()

    print("\n=== Decomposição shift-share da intensidade agregada CAT/VBP ===")
    print(f"  a^ES (agregado, CATs/R$M)   = {a_es_agg:.4f}")
    print(f"  a^BR (agregado, CATs/R$M)   = {a_br_agg:.4f}")
    print(f"  Diferença total              = {a_es_agg - a_br_agg:+.4f}")
    print(f"    Efeito-composição          = {ef_comp:+.4f}  ({ef_comp/(a_es_agg-a_br_agg)*100:+.1f}%)")
    print(f"    Efeito-intensidade         = {ef_int:+.4f}  ({ef_int/(a_es_agg-a_br_agg)*100:+.1f}%)")
    print(f"    Efeito-interação           = {ef_inter:+.4f}  ({ef_inter/(a_es_agg-a_br_agg)*100:+.1f}%)")

    # 6) Aplicar Leontief ES: f^ES = a^ES' * L^ES ; f^BR_counterf = a^BR' * L^ES
    L_es = pd.read_csv(PROCESSED / "mip_es_L.csv", index_col=0, dtype={0: str})
    L_es.index = L_es.index.astype(str)
    a_es = comp.set_index("codigo")["a_ES"].reindex(L_es.index).fillna(0.0).values
    a_br = comp.set_index("codigo")["a_BR"].reindex(L_es.index).fillna(0.0).values
    f_es = a_es @ L_es.values
    f_br_counterf = a_br @ L_es.values  # contrafactual: estrutura ES com intensidade BR
    comp = comp.set_index("codigo").reindex(L_es.index)
    comp["f_ES"] = f_es
    comp["f_BR_counterf"] = f_br_counterf
    comp["dif_f_pp"] = (f_es - f_br_counterf)
    comp.index.name = "codigo"
    comp = comp.reset_index()

    # 7) Salvar
    out = PROCESSED / "comparativo_br_es.csv"
    comp.to_csv(out, index=False, float_format="%.6f")
    print(f"\nSalvo: {out}")

    # 8) Resumo top-10
    print("\n=== Top-10 setores por |f^ES - f^BR_counterf| ===")
    top = comp.assign(abs_dif=comp["dif_f_pp"].abs()).nlargest(10, "abs_dif")[
        ["codigo", "nome", "a_ES", "a_BR", "razao_a_ES_BR", "f_ES", "f_BR_counterf", "dif_f_pp"]
    ]
    print(top.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    # Estatísticas agregadas para o LaTeX
    summary = {
        "cat_total_BR_2015": int(cat_br["cat_total_2015"].sum()),
        "cat_total_ES_2015": int(vetor_es["acidentes"].sum()),
        "vbp_total_BR_milhoes": float(vbp_br["vbp_milhoes_BR"].sum()),
        "vbp_total_ES_milhoes": float(setores_es["vbp_milhoes_RS"].sum()),
        "a_agg_ES": a_es_agg, "a_agg_BR": a_br_agg,
        "diferenca_total": a_es_agg - a_br_agg,
        "efeito_composicao": ef_comp,
        "efeito_intensidade": ef_int,
        "efeito_interacao": ef_inter,
        "f_agg_ES": float(f_es.mean()),
        "f_agg_BR_counterf": float(f_br_counterf.mean()),
    }
    pd.Series(summary).to_csv(PROCESSED / "comparativo_br_es_summary.csv")
    print(f"\nSalvo: {PROCESSED}/comparativo_br_es_summary.csv")


if __name__ == "__main__":
    main()
