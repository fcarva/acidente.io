"""
Bloco B — Pegada distributiva de acidentes: dimensão renda/demanda (MADE-style)
================================================================================
Metodologia (lado da demanda, demand-side, à la NPE76/MADE):

  Para cada unidade consumidora (domicílio/indivíduo) com cesta de consumo c^h:
      F^h = f' · B · c^h
  onde:
    f'  = vetor linha de pegada de acidentes (35 setores, já calculado)
    B   = matriz-ponte POF→MIP-ES (categorias COICOP → 35 setores)
    c^h = vetor de gastos do domicílio h (R$/mês, por categoria POF)

  Resultado: pegada per-capita de acidentes embutida no consumo doméstico,
  desagregada por:
    - decil de renda (1=mais pobre, 10=mais rico)
    - gênero do responsável pelo domicílio
    - classe socioeconômica (A/B/C/D/E ou por faixa salarial)
    - região (ES vs resto do Brasil)

Dados necessários (ainda não carregados):
  - POF 2017-2018 microdados IBGE (tabelas de gastos individuais e domiciliares)
  - Tabela-ponte COICOP/POF → CNAE → MIP-ES 35 setores
  - [Opcional] PNAD Contínua 2015 para perfil de renda alternativo

INSTRUÇÕES DE USO:
  1. Faça upload dos arquivos POF na pasta data/raw/pof/
     Estrutura esperada (microdados IBGE):
       data/raw/pof/MORADOR.txt       (ou .csv)
       data/raw/pof/DESPESA_INDIVIDUAL.txt
       data/raw/pof/DESPESA_COLETIVA.txt
       data/raw/pof/RENDIMENTO.txt
  2. Execute: python3 src/09_pof_demanda.py --check
     (verifica os arquivos sem processar)
  3. Execute: python3 src/09_pof_demanda.py
     (processa e gera resultados em data/processed/pegada_renda_*.csv)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC  = ROOT / "data" / "processed"
POF_DIR = ROOT / "data" / "raw" / "pof"
OUT_FIG = ROOT / "outputs" / "figures"
OUT_TAB = ROOT / "outputs" / "tables"

# ─────────────────────────────────────────────────────────────────────────────
# Tabela-ponte COICOP → MIP-ES 35 setores
# Baseada em IBGE (2019) "Compatibilização das despesas da POF 2017-2018
# com a Estrutura do Sistema de Contas Nacionais"
# Cada linha: (produto_pof_prefix, codigo_mip, descricao_aproximada)
# ─────────────────────────────────────────────────────────────────────────────
BRIDGE_POF_MIP = [
    # Alimentação no domicílio → Alimentos e bebidas
    ("1101", "1000", "Cereais e farináceos"),
    ("1102", "1000", "Leguminosas"),
    ("1103", "0191", "Hortaliças e verduras"),
    ("1104", "0192", "Carnes e vísceras"),
    ("1105", "0192", "Pescados"),
    ("1106", "1000", "Aves e ovos"),
    ("1107", "1000", "Leite e derivados"),
    ("1108", "0191", "Frutas"),
    ("1109", "1000", "Açúcares e derivados"),
    ("1110", "2000", "Óleos e gorduras"),
    ("1111", "1000", "Farinhas, féculas e massas"),
    ("1112", "1000", "Panificados"),
    ("1113", "1000", "Sal e condimentos"),
    ("1114", "1000", "Outras alimentações no domicílio"),
    # Alimentação fora do domicílio → Alojamento/alimentação
    ("1200", "5500", "Refeições e lanches fora do domicílio"),
    # Habitação
    ("2101", "3500", "Aluguel e encargos"),
    ("2102", "6800", "Aluguel estimado"),
    ("2103", "3500", "Condomínio"),
    ("2201", "3500", "Energia elétrica"),
    ("2202", "3500", "Gás doméstico"),
    ("2203", "3500", "Água e esgoto"),
    ("2301", "1600", "Móveis e artigos do lar"),
    ("2302", "1600", "Eletrodomésticos"),
    ("2401", "7800", "Serviços domésticos"),
    ("2402", "7800", "Reparos no domicílio"),
    ("2403", "2500", "Equipamentos de uso doméstico"),
    # Vestuário → Têxtil/vestuário
    ("3101", "1300", "Roupas e acessórios"),
    ("3201", "1300", "Calçados e bolsas"),
    # Transporte
    ("4101", "2900", "Aquisição de veículos"),
    ("4201", "4900", "Transporte urbano"),
    ("4202", "4900", "Transporte intermunicipal"),
    ("4203", "4900", "Transporte aéreo"),
    ("4301", "1900", "Gasolina e álcool"),
    ("4302", "2000", "Lubrificantes"),
    ("4303", "2500", "Peças e manutenção"),
    # Higiene e cuidados pessoais
    ("5101", "2000", "Produtos de higiene pessoal"),
    ("5102", "8692", "Serviços pessoais de beleza"),
    # Assistência à saúde
    ("6101", "8692", "Medicamentos e farmácia"),
    ("6102", "8691", "Serviços médicos"),
    ("6103", "8692", "Plano de saúde"),
    ("6104", "2000", "Material e aparelhos terapêuticos"),
    # Educação → split público/privado proporcional
    ("7101", "8592", "Cursos regulares privados"),
    ("7102", "8591", "Material escolar"),
    ("7103", "8592", "Cursos extracurriculares"),
    # Recreação e cultura
    ("8101", "9080", "Recreação e esportes"),
    ("8102", "5800", "Livros, jornais e revistas"),
    ("8103", "5800", "Pacotes turísticos e lazer"),
    # Fumo
    ("9101", "1000", "Fumo e derivados"),
    # Serviços pessoais
    ("10101", "9480", "Serviços pessoais e cuidados"),
    # Comunicação
    ("11101", "5800", "Telefone e internet"),
    # Seguros e serviços financeiros
    ("12101", "6480", "Seguros em geral"),
    ("12102", "6480", "Serviços financeiros"),
    # Outras despesas
    ("13101", "9480", "Outras despesas correntes"),
]

BRIDGE_DF = pd.DataFrame(
    BRIDGE_POF_MIP, columns=["codigo_pof_prefix", "codigo_mip", "descricao"]
)


def check_pof_files() -> bool:
    """Verifica se os arquivos POF estão disponíveis."""
    esperados = [
        "MORADOR.txt", "DESPESA_INDIVIDUAL.txt",
        "DESPESA_COLETIVA.txt", "RENDIMENTO.txt",
    ]
    ok = True
    print(f"\n=== Verificando arquivos POF em {POF_DIR} ===")
    POF_DIR.mkdir(parents=True, exist_ok=True)
    for nome in esperados:
        p = POF_DIR / nome
        # Aceita .txt ou .csv
        alternativas = [p, p.with_suffix(".csv"),
                        POF_DIR / nome.replace(".txt", "_ES.txt")]
        found = next((a for a in alternativas if a.exists()), None)
        status = f"✓ {found.name}" if found else f"✗ não encontrado"
        print(f"  {nome:<35} {status}")
        if not found:
            ok = False
    if not ok:
        print("\nINSTRUÇÕES:")
        print(f"  1. Baixe os microdados POF 2017-2018 de:")
        print(f"     https://ftp.ibge.gov.br/Orcamentos_Familiares/Pesquisa_de_Orcamentos_Familiares_2017-2018/Microdados/")
        print(f"  2. Extraia os arquivos na pasta:")
        print(f"     {POF_DIR}/")
        print(f"  3. Execute novamente: python3 src/09_pof_demanda.py")
    return ok


def load_pof_gastos(uf_filter: int | None = 32) -> pd.DataFrame:
    """
    Carrega e consolida gastos domiciliares da POF.
    uf_filter=32 → ES; None → Brasil completo.
    """
    # Tenta vários formatos de arquivo
    for fname in ["DESPESA_INDIVIDUAL.txt", "DESPESA_INDIVIDUAL.csv",
                  "DESPESA_COLETIVA.txt"]:
        p = POF_DIR / fname
        if not p.exists():
            continue
        # POF usa largura fixa ou CSV dependendo da versão
        try:
            df = pd.read_csv(p, sep=";", encoding="latin1", dtype=str, low_memory=False)
        except Exception:
            df = pd.read_fwf(p, encoding="latin1", dtype=str)
        # Normaliza nomes de colunas
        df.columns = [c.upper().strip() for c in df.columns]
        if uf_filter and "UF" in df.columns:
            df = df[df["UF"].astype(str).str.strip() == str(uf_filter)]
        return df
    raise FileNotFoundError(
        f"Nenhum arquivo de despesas POF encontrado em {POF_DIR}. "
        "Execute com --check para verificar."
    )


def load_pof_rendimento(uf_filter: int | None = 32) -> pd.DataFrame:
    for fname in ["RENDIMENTO.txt", "RENDIMENTO.csv"]:
        p = POF_DIR / fname
        if not p.exists():
            continue
        df = pd.read_csv(p, sep=";", encoding="latin1", dtype=str, low_memory=False)
        df.columns = [c.upper().strip() for c in df.columns]
        if uf_filter and "UF" in df.columns:
            df = df[df["UF"].astype(str).str.strip() == str(uf_filter)]
        return df
    raise FileNotFoundError("Arquivo RENDIMENTO não encontrado.")


def build_bridge_matrix(gastos: pd.DataFrame) -> pd.DataFrame:
    """
    Mapeia gastos POF → MIP-ES 35 setores usando BRIDGE_DF.
    Retorna DataFrame com colunas: [domicilio_id, codigo_mip, valor_mensal].
    """
    # Identifica coluna de código de produto e valor
    cod_col   = next((c for c in gastos.columns if "COD" in c and "PROD" in c), None)
    val_col   = next((c for c in gastos.columns if "VALOR" in c or "DESPESA" in c), None)
    dom_col   = next((c for c in gastos.columns if "DOM" in c or "DOMIC" in c), None)
    if not all([cod_col, val_col, dom_col]):
        raise ValueError(
            f"Colunas esperadas não encontradas. Disponíveis: {list(gastos.columns)[:20]}"
        )
    gastos = gastos[[dom_col, cod_col, val_col]].copy()
    gastos.columns = ["domicilio_id", "codigo_pof", "valor"]
    gastos["valor"] = pd.to_numeric(gastos["valor"].str.replace(",", "."), errors="coerce")
    gastos = gastos.dropna(subset=["valor"])

    # Match por prefixo do código POF
    rows = []
    for _, br in BRIDGE_DF.iterrows():
        mask = gastos["codigo_pof"].str.startswith(br["codigo_pof_prefix"])
        sub = gastos[mask].copy()
        if not sub.empty:
            sub["codigo_mip"] = br["codigo_mip"]
            rows.append(sub)
    if not rows:
        raise ValueError("Nenhum gasto mapeado. Verifique o formato dos códigos POF.")
    mapped = pd.concat(rows, ignore_index=True)
    agg = mapped.groupby(["domicilio_id", "codigo_mip"], as_index=False)["valor"].sum()
    return agg


def compute_demand_footprint(
    gastos_mip: pd.DataFrame,
    rendimento: pd.DataFrame,
    f_vector: pd.Series,
    n_decis: int = 10,
) -> pd.DataFrame:
    """
    Calcula pegada de acidentes por decil de renda.
    Retorna DataFrame com (decil, pegada_per_capita, gasto_per_capita, razao).
    """
    # Pivota gastos para matriz domicílio × setor
    pivot = gastos_mip.pivot_table(
        index="domicilio_id", columns="codigo_mip",
        values="valor", aggfunc="sum", fill_value=0.0,
    )
    # Alinha com vetor f
    f_aligned = f_vector.reindex(pivot.columns, fill_value=0.0).values

    # Pegada por domicílio (f' × c^h)
    pivot["pegada_total"] = pivot.values @ f_aligned
    pivot["gasto_total"]  = pivot.drop(columns=["pegada_total"]).sum(axis=1)

    # Renda por domicílio
    rend_col  = next((c for c in rendimento.columns if "REND" in c and "TOTAL" in c), None)
    dom_col_r = next((c for c in rendimento.columns if "DOM" in c), None)
    if rend_col and dom_col_r:
        rend = rendimento[[dom_col_r, rend_col]].copy()
        rend.columns = ["domicilio_id", "renda_total"]
        rend["renda_total"] = pd.to_numeric(
            rend["renda_total"].str.replace(",", "."), errors="coerce"
        )
        pivot = pivot.join(rend.set_index("domicilio_id")[["renda_total"]], how="left")
    else:
        pivot["renda_total"] = pivot["gasto_total"]  # proxy

    # Decis de renda
    pivot["decil"] = pd.qcut(
        pivot["renda_total"].rank(method="first"), n_decis,
        labels=range(1, n_decis + 1),
    )

    result = (
        pivot.groupby("decil", observed=True)
        .agg(
            pegada_media=("pegada_total", "mean"),
            gasto_medio=("gasto_total", "mean"),
            renda_media=("renda_total", "mean"),
            n_domicilios=("pegada_total", "count"),
        )
        .reset_index()
    )
    result["pegada_por_R1000_gasto"] = result["pegada_media"] / (result["gasto_medio"] / 1000)
    result["pegada_por_R1000_renda"] = result["pegada_media"] / (result["renda_media"] / 1000)
    return result


def main(check_only: bool = False) -> None:
    if not check_pof_files():
        if not check_only:
            print("\nAguardando upload dos arquivos POF. Abortando.")
        return
    if check_only:
        print("\nTodos os arquivos POF encontrados. Execute sem --check para processar.")
        return

    print("\n=== Bloco B: Pegada distributiva por renda/demanda (POF 2017-2018) ===")

    # Carrega vetor f (pegada total, já calculado)
    f_csv = PROC / "comparativo_br_es.csv"
    if f_csv.exists():
        comp = pd.read_csv(f_csv, dtype={"codigo": str})
        f_vector = comp.set_index("codigo")["f_ES"].fillna(0.0)
    else:
        # Recalcula do zero
        from common_io import load_leontief, load_vetor_acidentes
        L_df = load_leontief()
        vetor = load_vetor_acidentes()
        setores = pd.read_csv(PROC / "mip_es_setores.csv", dtype={"codigo": str})
        merged = setores.merge(vetor, on="codigo")
        a = (merged["acidentes"] / merged["vbp_milhoes_RS"]).fillna(0.0).values
        f = a @ L_df.values
        f_vector = pd.Series(f, index=L_df.index)

    # Processa POF
    print("  Carregando gastos POF (UF=32 Espírito Santo)...")
    try:
        gastos = load_pof_gastos(uf_filter=32)
        rendimento = load_pof_rendimento(uf_filter=32)
    except FileNotFoundError as e:
        print(f"  ERRO: {e}")
        return

    print("  Mapeando gastos POF → MIP-ES 35 setores...")
    gastos_mip = build_bridge_matrix(gastos)

    print("  Calculando pegada por decil de renda...")
    result = compute_demand_footprint(gastos_mip, rendimento, f_vector)

    print("\nPegada de acidentes por decil de renda (ES — POF 2017-2018):")
    print(result.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    out = PROC / "pegada_renda_decis.csv"
    result.to_csv(out, index=False, float_format="%.6f")
    print(f"\nSalvo: {out}")

    # Figura
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(result["decil"], result["pegada_por_R1000_gasto"], color="#2E86AB", alpha=0.85)
    ax.set_xlabel("Decil de renda (1=mais pobre, 10=mais rico)")
    ax.set_ylabel("Pegada de acidentes por R$1.000 gastos (CATs)")
    ax.set_title("Pegada distributiva de acidentes — ES (POF 2017-2018 × MIP-ES 2015)")
    ax.set_xticks(result["decil"])
    plt.tight_layout()
    out_fig = OUT_FIG / "pegada_renda_decis.pdf"
    fig.savefig(out_fig, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Figura salva: {out_fig}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="Apenas verifica se os arquivos POF estão disponíveis")
    args = parser.parse_args()
    main(check_only=args.check)
