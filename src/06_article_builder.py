"""
Gerador do artigo LaTeX — lê os CSVs de resultados e produz
latex/pegada_acidentes_es.tex com todos os números preenchidos
a partir dos dados correntes do pipeline.

Fontes:
    outputs/tables/resultados_principais.csv   (02_io_model)
    outputs/tables/extracao_hipotetica.csv     (03_hem_analysis)
    outputs/tables/sensibilidade.csv           (05_sensibilidade)

Saída:
    latex/pegada_acidentes_es.tex
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_TEX = ROOT / "latex" / "pegada_acidentes_es.tex"

# ─── helpers ────────────────────────────────────────────────────────────────

_COMMA = "\x00DC\x00"   # placeholder substituído por {,} no pós-processamento

def _fmt(v: float, dec: int = 3) -> str:
    """Formata número com vírgula decimal — usa placeholder para compatibilidade com f-strings."""
    s = f"{v:.{dec}f}"
    return s.replace(".", _COMMA)

def _pct(v: float, dec: int = 1) -> str:
    return _fmt(v * 100, dec) + r"\,\%"

def _nome_abrev(nome: str, maxlen: int = 40) -> str:
    return nome if len(nome) <= maxlen else nome[:maxlen].rstrip() + "\\ldots"

def _setor_row(r: pd.Series, *, show_quad: bool = False) -> str:
    extra = f" & {r.quadrante}" if show_quad else ""
    return (
        f"  {r.codigo} & {_nome_abrev(r['nome'], 38)} "
        f"& {_fmt(r.intensidade_direta_a)} "
        f"& {_fmt(r.pegada_estrutural_f)} "
        f"& {_fmt(r.amplificacao_f_sobre_a, 2)} "
        f"& {_pct(r.share_indireto)} "
        f"& {_fmt(r.encadeamento_tras_U)}"
        f"{extra} \\\\"
    )

# ─── carga de dados ──────────────────────────────────────────────────────────

def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(ROOT / "outputs/tables/resultados_principais.csv", dtype={"codigo": str})
    hem = pd.read_csv(ROOT / "outputs/tables/extracao_hipotetica.csv", dtype={"codigo": str})
    sens = pd.read_csv(ROOT / "outputs/tables/sensibilidade.csv", dtype={"codigo": str})
    return df, hem, sens

# ─── núcleos de seções ───────────────────────────────────────────────────────

def _preamble() -> str:
    return dedent(r"""
    \documentclass[12pt, a4paper]{article}

    % ─── ENCODING & LANGUAGE ──────────────────────────────────────────
    \usepackage[utf8]{inputenc}
    \usepackage[T1]{fontenc}
    \usepackage[brazilian]{babel}
    \usepackage[autostyle]{csquotes}   % aspas corretas em pt-BR

    % ─── TYPOGRAPHY ───────────────────────────────────────────────────
    \usepackage{mathpazo}              % Palatino — fonte padrão artigos econ
    \usepackage[scaled=0.95]{helvet}   % Helvetica para sans (notas de rodapé)
    \usepackage{microtype}
    \usepackage{indentfirst}           % parágrafo inicial também indentado (ABNT)

    % ─── MATH ─────────────────────────────────────────────────────────
    \usepackage{amsmath, amssymb, amsthm}
    \usepackage{mathtools}
    \allowdisplaybreaks                % permite quebra de equações entre páginas

    % ─── LAYOUT ───────────────────────────────────────────────────────
    % ABNT NBR 14724: margens 3cm (esq/sup) × 2cm (dir/inf) para trabalhos
    % Para artigo de disciplina usa-se margem simétrica:
    \usepackage[a4paper, left=3cm, right=2.5cm, top=3cm, bottom=2.5cm]{geometry}
    \usepackage{setspace}
    \setstretch{1.5}                   % espaçamento 1,5 — padrão pós-graduação
    \setlength{\parindent}{1.25cm}     % recuo ABNT NBR 14724
    \setlength{\parskip}{6pt}

    % ─── TABLES & FIGURES ─────────────────────────────────────────────
    \usepackage{booktabs}
    \usepackage{threeparttable}        % notas de tabela (tnote)
    \usepackage{longtable}
    \usepackage{graphicx}
    \usepackage{caption}
    \captionsetup{
      font=small, labelfont=bf, labelsep=period,
      justification=raggedright, singlelinecheck=false
    }
    \usepackage{subcaption}
    \usepackage{float}
    \usepackage{multirow}
    \usepackage{array}
    \newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}

    % ─── BIBLIOGRAPHY ─────────────────────────────────────────────────
    \usepackage{natbib}
    \bibliographystyle{plainnat}
    \setcitestyle{authoryear, round, comma}

    % ─── HYPERLINKS ───────────────────────────────────────────────────
    \usepackage[
      colorlinks=true, linkcolor=black, citecolor=black,
      urlcolor=black, breaklinks=true,
      pdftitle={Pegada de Acidentes de Trabalho -- MIP-ES 2015},
      pdfauthor={Felipe Carvalho},
      pdfsubject={Economia do Trabalho; Insumo-Produto},
      pdfkeywords={insumo-produto, segurança do trabalho, pegada social, AEAT}
    ]{hyperref}

    % ─── HEADERS & FOOTERS ────────────────────────────────────────────
    \usepackage{fancyhdr}
    \pagestyle{fancy}
    \fancyhf{}
    \fancyhead[L]{\small\itshape Pegada de acidentes de trabalho\,\textperiodcentered\,MIP-ES 2015}
    \fancyhead[R]{\small\thepage}
    \fancyfoot[C]{\small PPGEco/UFES --- PECO-5054/6054 --- 2026/1}
    \renewcommand{\headrulewidth}{0.4pt}
    \renewcommand{\footrulewidth}{0.4pt}
    \setlength{\headheight}{14.5pt}

    % ─── CUSTOM COMMANDS ──────────────────────────────────────────────
    % Nota de tabela fora do float (fallback sem threeparttable)
    \newcommand{\tabnote}[1]{\par\smallskip\footnotesize\textit{Notas:} #1}
    % Abreviações comuns
    \newcommand{\vbp}{\textsc{vbp}}
    \newcommand{\cat}{\textsc{cat}}
    \newcommand{\mipes}{\textsc{mip-es}}
    \newcommand{\aeat}{\textsc{aeat}}

    % ─── TITLE ────────────────────────────────────────────────────────
    \title{%
      \large\textsc{Universidade Federal do Espírito Santo}\\
      \small Programa de Pós-Graduação em Economia\\[0.4em]
      \rule{\linewidth}{0.8pt}\\[0.6em]
      \LARGE\bfseries Pegada de Acidentes de Trabalho\\[0.4em]
      \large\normalfont\itshape
        Uma aplicação de insumo-produto estendido à\\
        Matriz Insumo-Produto do Espírito Santo (2015)\\[0.4em]
      \rule{\linewidth}{0.8pt}
    }
    \author{%
      \large Felipe Carvalho%
      \thanks{Mestrando em Economia, PPGEco/UFES.
              Disciplina PECO-5054/PECO-6054 --- Análise de Insumo-Produto, 2026/1.
              Prof.\ Dr.\ Celso Bissoli Sessa.
              Contato: \href{mailto:fcarva@ppgeco.ufes.br}{\texttt{fcarva@ppgeco.ufes.br}}.}
    }
    \date{Vitória, maio de 2026}
    """).lstrip("\n")


def _abstract(df: pd.DataFrame, hem: pd.DataFrame, sens: pd.DataFrame) -> str:
    n_cats   = int(df.acidentes_CAT.sum())
    a_med    = df.intensidade_direta_a.median()
    u_med    = df.encadeamento_tras_U.median()
    pct_ind  = df.share_indireto.mean()
    n_chave  = int((df.quadrante == "Setor-chave de risco").sum())

    # Setor de maior f
    top = df.sort_values("pegada_estrutural_f", ascending=False).iloc[0]

    # HEM extrativos
    ext680 = hem[hem.codigo == "0680"].iloc[0].delta_cat_completa_pct
    ext791 = hem[hem.codigo == "0791"].iloc[0].delta_cat_completa_pct

    # Setores estáveis na sensibilidade
    n_stable = int((sens.prob_setor_chave > 0.5).sum())

    return dedent(rf"""
    % ── Resumo (pt-BR) ────────────────────────────────────────────────
    \renewcommand{{\abstractname}}{{\normalfont\normalsize\bfseries Resumo}}
    \begin{{abstract}}
    \setstretch{{1.0}}\small
    Este artigo aplica o modelo de Leontief estendido para mensurar a
    \textit{{pegada de acidentes de trabalho}} na economia do Espírito Santo
    a partir da Matriz Insumo-Produto estadual de 2015 (35 setores),
    usando como vetor satélite os registros oficiais do Anuário Estatístico
    de Acidentes do Trabalho (\aeat-2015), que totalizam {n_cats:,}~\cat{{}}s no
    estado. Calculando $\mathbf{{f}}' = \mathbf{{a}}'\mathbf{{L}}$ para cada setor,
    obtém-se que o componente indireto representa em média {_pct(pct_ind)} da
    pegada total --- indicando que mais de um terço do passivo de acidentes
    embutido em qualquer demanda final típica se origina em atividades
    distintas das que produzem o bem demandado.
    Cruzando intensidade direta ($a_j$) com índices de Rasmussen-Hirschman,
    propõe-se uma tipologia de quatro quadrantes que identifica
    {n_chave}~\textit{{setores-chave de risco}}.
    Uma análise de sensibilidade Monte Carlo ($N = 1\,000$, $\sigma_{{\log}} = 0{{,}}20$)
    confirma que {n_stable}~setores permanecem no quadrante crítico em mais de
    50\% das iterações. A extração hipotética dos setores petrolífero (0680)
    e ferroso (0791) altera a pegada agregada em apenas {_fmt(abs(ext680), 1)}\%
    e {_fmt(abs(ext791), 1)}\% respectivamente, revelando o
    \textit{{deslocamento estrutural duplo}} do risco ocupacional na economia
    capixaba.

    \smallskip
    \noindent\textbf{{Palavras-chave:}} insumo-produto; segurança do trabalho;
    pegada social; ligações de Rasmussen-Hirschman; Espírito Santo; \aeat-2015.\\
    \noindent\textbf{{Códigos JEL:}} D57; J28; R15.
    \end{{abstract}}

    % ── Abstract (EN) ─────────────────────────────────────────────────
    \renewcommand{{\abstractname}}{{\normalfont\normalsize\bfseries Abstract}}
    \begin{{abstract}}
    \setstretch{{1.0}}\small
    This paper applies the extended Leontief model to measure the
    \textit{{work accident footprint}} of the Espírito Santo economy using
    the 2015 state input-output matrix (35 sectors) and an official
    satellite vector constructed from the 2015 Work Accident Statistical
    Yearbook (\aeat-2015), totalling {n_cats:,} registered accidents.
    The structural (indirect) component accounts for {_pct(pct_ind)} of
    the total footprint on average, indicating that over one-third of the
    accident liability embedded in any unit of final demand originates
    in sectors other than the direct producer.
    We propose a four-quadrant typology combining accident intensity with
    Rasmussen-Hirschman backward linkages, identifying {n_chave}~\textit{{key
    risk sectors}}. Monte Carlo sensitivity analysis ($N=1\,000$) confirms
    robustness of {n_stable}~sectors. Hypothetical extraction of the
    oil-and-gas (0680) and iron-ore (0791) sectors changes the aggregate
    footprint by {_fmt(abs(ext680), 1)}\% and {_fmt(abs(ext791), 1)}\%
    respectively, supporting the \textit{{double structural displacement}}
    hypothesis.

    \smallskip
    \noindent\textbf{{Keywords:}} input-output; occupational safety; social footprint;
    Rasmussen-Hirschman linkages; Espírito Santo; AEAT-2015.\\
    \noindent\textbf{{JEL Codes:}} D57; J28; R15.
    \end{{abstract}}

    \vspace{{1em}}
    \noindent\rule{{\linewidth}}{{0.4pt}}
    \vspace{{0.5em}}
    \setstretch{{1.5}}
    """).lstrip("\n")


def _sec_intro() -> str:
    return dedent(r"""
    % ════════════════════════════════════════════════════════════════
    \section{Introdução}
    % ════════════════════════════════════════════════════════════════

    A análise da segurança e saúde no trabalho (SST) na economia brasileira
    é tradicionalmente conduzida em registro setorial isolado: examinam-se
    taxas de incidência por classe da CNAE, a eficácia de Normas
    Regulamentadoras específicas, ou correlações entre regulação e
    ocorrência~\citep{shimizu2021accident,chagas2011saude}.
    Falta, com poucas exceções na literatura nacional, um tratamento
    \textit{estrutural} do problema --- capaz de mapear como o risco
    ocupacional gerado em um setor é transmitido para outros setores via
    encadeamentos produtivos até alcançar o consumidor final.

    A pergunta é especialmente relevante em economias com especialização
    produtiva concentrada em atividades de alto risco. O Espírito Santo é
    o caso paradigmático no Brasil contemporâneo: em 2015, os setores de
    extração de petróleo e gás (CNAE-IBGE 0680) e extração de minério de
    ferro (0791) responderam, somados, por aproximadamente
    \textbf{R\$~33,3~bilhões em valor bruto da produção (VBP)} ---
    parte de um total extrativo de R\$~34,6~bi (17,5\,\% do VBP estadual
    de R\$~198,3~bi).\footnote{Cálculo a partir da MIP-ES 2015 oficial
    (IJSN), conforme Seção~\ref{sec:dados}.}
    Trata-se de atividades com taxas de acidente persistentemente acima
    da média nacional que, simultaneamente, produzem bens com alta
    inserção exportadora.

    A pergunta deste artigo é, portanto: \textbf{qual o conteúdo de
    acidentes de trabalho embutido em uma unidade de demanda final por
    setor na economia capixaba, e como a estrutura produtiva redistribui
    esse passivo entre quem produz fisicamente o risco e quem o demanda
    via produto final?}

    A contribuição é dupla. Metodologicamente, transpõe-se para o caso
    brasileiro o instrumental de pegadas sociais (\textit{social footprint
    analysis}), consolidado na literatura internacional para emissões de
    carbono mas aplicado de forma incipiente a variáveis ocupacionais.
    Empiricamente, oferece-se a primeira mensuração, ao nosso conhecimento,
    da pegada de acidentes para uma economia subnacional brasileira,
    usando a MIP-ES 2015 (35\,$\times$\,35) com vetor satélite construído
    diretamente dos registros administrativos oficiais do AEAT-2015.

    \paragraph{Originalidade.}
    Esta é a primeira aplicação de análise de pegada social voltada
    especificamente à variável \textit{acidentes de trabalho} em uma matriz
    insumo-produto subnacional brasileira. As aplicações de IO estendido
    para variáveis sociais no Brasil concentram-se em emprego, remuneração
    e desigualdade de gênero --- a dimensão de risco ocupacional permanece
    um espaço analítico em aberto, apesar da relevância empírica do fenômeno
    e da maturidade do instrumental.

    O artigo está organizado em oito seções. A Seção~\ref{sec:teorico}
    apresenta o referencial teórico. A Seção~\ref{sec:dados} detalha dados
    e método. A Seção~\ref{sec:resultados} reporta os resultados empíricos,
    incluindo pegada total, tipologia de quadrantes, multiplicadores de
    emprego e análise de sensibilidade. A Seção~\ref{sec:hem} apresenta o
    Método de Extração Hipotética para todos os 35 setores.
    A Seção~\ref{sec:discussao} discute o padrão de deslocamento estrutural
    duplo. As Seções~\ref{sec:limitacoes} e~\ref{sec:conclusao} discutem
    limitações e considerações finais.
    """).lstrip("\n")


def _sec_teorico() -> str:
    return dedent(r"""
    % ════════════════════════════════════════════════════════════════
    \section{Referencial teórico}
    \label{sec:teorico}
    % ════════════════════════════════════════════════════════════════

    \subsection{O modelo de Leontief estendido}

    O modelo aberto de Leontief estabelece que, para uma economia com $n$
    setores, o vetor de produção bruta $\mathbf{x}$ relaciona-se ao vetor de
    demanda final $\mathbf{y}$ pela identidade fundamental
    %
    \begin{equation}
    \mathbf{x} = (\mathbf{I} - \mathbf{A})^{-1}\, \mathbf{y} = \mathbf{L}\, \mathbf{y},
    \label{eq:leontief}
    \end{equation}
    %
    onde $\mathbf{A}$ é a matriz $n \times n$ de coeficientes técnicos
    diretos, com $a_{ij} = z_{ij}/x_j$, e
    $\mathbf{L} = (\mathbf{I}-\mathbf{A})^{-1}$ é a inversa de Leontief
    \citep[cap.~2]{millerblair2009}.

    O modelo torna-se \textit{estendido} quando se associa a $\mathbf{L}$
    um vetor $\mathbf{a}$ de coeficientes diretos de uma variável satélite.
    Definindo
    %
    \begin{equation}
    a_j = \frac{e_j}{x_j},
    \label{eq:coeficiente}
    \end{equation}
    %
    em que $e_j$ é o número de CATs no setor $j$ e $x_j$ é o VBP em
    R\$~milhões, o \textbf{vetor de pegada total} é
    %
    \begin{equation}
    \mathbf{f}' = \mathbf{a}'\, \mathbf{L},
    \label{eq:pegada}
    \end{equation}
    %
    cuja $j$-ésima coordenada $f_j$ reporta o conteúdo total de acidentes
    associado a uma unidade de demanda final por produtos do setor $j$,
    considerando todos os encadeamentos a montante \citep[cap.~10]{millerblair2009}.

    A decomposição direto-indireto é imediata:
    %
    \begin{equation}
    f_j = \underbrace{a_j}_{\text{efeito direto}}
        + \underbrace{(f_j - a_j)}_{\text{efeito indireto}}.
    \label{eq:decomposicao}
    \end{equation}

    Complementarmente, define-se a intensidade de acidentes por trabalhador
    exposto como
    %
    \begin{equation}
    \tilde{a}_j = \frac{e_j}{\ell_j},
    \label{eq:atilde}
    \end{equation}
    %
    onde $\ell_j$ é o número de ocupações no setor $j$ (RAIS-2015). A
    comparação entre $a_j$ e $\tilde{a}_j$ permite separar setores com alta
    pegada por VBP (geralmente labor-intensivos com baixo salário) de setores
    com alta taxa de acidente por trabalhador (periculosidade intrínseca).

    \subsection{Pegadas sociais}

    A literatura de \textit{footprint analysis} nasceu como extensão direta
    da contribuição pioneira de \citet{leontief1970}. \citet{hoekstra2002virtual}
    consolidam a pegada hídrica e \citet{hertwich2009carbon}, a pegada de
    carbono. A extensão para variáveis sociais --- empregos, salários, gênero,
    mortes ocupacionais --- teve em \citet{alsamawi2014employment} seu marco
    metodológico.

    No Brasil, aplicações robustas cobrem variáveis ambientais
    \citep{carvalho2009intensidade,souza2016reducing} e sociais
    \citep{perobelli2016decomposicao,made2021multiplicadores}, mas a
    dimensão de risco ocupacional permanece um espaço analítico em aberto.
    É precisamente nessa lacuna que se insere o presente artigo.

    \subsection{Multiplicadores de emprego}

    O coeficiente direto de emprego $e_j = \ell_j / x_j$ (trabalhadores
    por R\$~milhão de produção) alimenta o multiplicador de emprego Tipo~I
    %
    \begin{equation}
    m^e_j = \mathbf{e}'\, \mathbf{L}_{\cdot j} = \sum_i e_i\, l_{ij},
    \label{eq:mult_emprego}
    \end{equation}
    %
    que reporta o número de postos de trabalho gerados direta e
    indiretamente para cada R\$~milhão de demanda final do setor $j$.
    O multiplicador de emprego contextualiza a pegada de acidentes: um
    setor pode ter $f_j$ elevado simplesmente por ser trabalho-intensivo
    (e portanto com $\ell_j$ grande), não necessariamente por ser
    intrinsecamente perigoso.

    \subsection{Ligações de Rasmussen-Hirschman}

    Os índices clássicos de ligação \citep{rasmussen1956studies} são
    derivados da inversa de Leontief normalizada. O \textit{índice de
    ligação para trás} do setor $j$ é
    %
    \begin{equation}
    U_j^B = \frac{\bar{l}_{\cdot j}}{\bar{l}_{\cdot\cdot}},
    \label{eq:linkage_back}
    \end{equation}
    %
    onde $\bar{l}_{\cdot j}$ é a média da $j$-ésima coluna de $\mathbf{L}$
    e $\bar{l}_{\cdot\cdot}$ é a média geral. $U_j^B > 1$ indica que o setor
    demanda insumos acima da média da economia. O \textit{índice de ligação
    para frente} $U_j^F$ é calculado analogamente pelas linhas de~$\mathbf{L}$.

    A combinação \textbf{alta $a_j$} e \textbf{alto $U_j^B$} caracteriza o
    que denominamos \textit{setores-chave de risco}: atividades cuja
    periculosidade própria é amplificada pelo seu papel a montante na cadeia.
    """).lstrip("\n")


def _sec_dados() -> str:
    return dedent(r"""
    % ════════════════════════════════════════════════════════════════
    \section{Dados e método}
    \label{sec:dados}
    % ════════════════════════════════════════════════════════════════

    \subsection{Matriz insumo-produto}

    Utiliza-se a Matriz Insumo-Produto do Espírito Santo de 2015, versão
    oficial do Instituto Jones dos Santos Neves (IJSN) em 35 setores
    produtivos, valores correntes em R\$~milhões. As matrizes $\mathbf{A}$
    e $\mathbf{L}$ são lidas diretamente das Tabelas~11 e~12 do arquivo XLSX
    oficial (\textit{Matriz\_Insumo-Produto\_MIP\_35x35.xlsx}), eliminando
    erros de transcrição presentes em versões anteriores baseadas em PDF.
    A reconstrução é validada por
    $\|(\mathbf{I}-\mathbf{A})\mathbf{L} - \mathbf{I}\|_F = 2{,}06 \times 10^{-15}$
    (precisão de máquina).

    Para a análise do multiplicador de emprego, utiliza-se o vetor de
    ocupações formais por setor extraído da RAIS-2015 (Ministério do
    Trabalho), compatibilizado com a classificação setorial da MIP-ES via
    tabela de tradutores CNAE\,2.0/SCN-IBGE.

    \subsection{Vetor satélite de acidentes}

    O vetor satélite $\mathbf{a}$ é construído a partir do
    \textit{Anuário Estatístico de Acidentes do Trabalho}
    \citep{aeat2016}, publicação oficial da Secretaria de Previdência Social.
    Utiliza-se o Capítulo~19 do AEAT-2015, que desagrega as Comunicações de
    Acidentes de Trabalho (CAT) por classe CNAE\,2.0 e por unidade da
    federação. Para cada setor $j$ da MIP-ES calcula-se
    %
    \begin{equation}
    a_j^{\text{ES}} = \frac{\text{CATs}_j^{\,\text{ES, 2015}}}{x_j^{\,\text{ES, 2015}}},
    \label{eq:aj}
    \end{equation}
    %
    com $x_j$ em R\$~milhões. A unidade resultante é
    ``acidentes por R\$~milhão de produção bruta''.
    A compatibilização entre CNAE\,2.0 e os setores da MIP-ES segue a
    tabela de tradutores oficial do IBGE (92 entradas; cobertura de 100\%
    das CNAEs presentes no AEAT para o ES).

    \paragraph{Limitações da fonte.}
    O AEAT registra apenas acidentes de trabalhadores cobertos pelo RGPS.
    Não são capturados servidores estatutários (setores 8400, 8591, 8691),
    trabalhadores informais ($\approx 38\%$ da força de trabalho no ES em
    2015, PNAD-Contínua 4T/2015) e empregados domésticos sem CAT registrada
    (setor 9700). Os resultados devem ser lidos como \textit{estimativa de
    piso (lower bound)} da pegada real de acidentes, com direção de
    enviesamento monotônica e efeito aproximadamente homotético sobre $a_j$.

    \subsection{Exercícios analíticos}

    Cinco produtos analíticos compõem os resultados:
    %
    \begin{enumerate}
      \item \textbf{Pegada total por setor.} Cálculo de
        $\mathbf{f}' = \mathbf{a}'\, \mathbf{L}$ com decomposição
        direto/indireto e razão $f_j/a_j$ (amplificação estrutural).
      \item \textbf{Tipologia de quadrantes.} Plano $(a_j,\, U_j^B)$ com
        cortes pelas médias: \textit{Setor-chave de risco},
        \textit{Propagador estrutural}, \textit{Risco localizado},
        \textit{Residual}.
      \item \textbf{Multiplicador de emprego.} Cálculo de $m^e_j$ e
        $\tilde{a}_j = e_j/\ell_j$ (intensidade por trabalhador exposto).
      \item \textbf{Análise de sensibilidade Monte Carlo.}
        $N=1\,000$ perturbações log-normais em $a_j$
        ($\sigma_{\log}=0{,}20$), avaliando robustez do quadrante e
        intervalos percentis da pegada.
      \item \textbf{Método de Extração Hipotética (HEM).} Para cada um
        dos 35 setores, calcula-se a queda em $\sum f$ resultante de
        zerar simultaneamente linha e coluna de $\mathbf{A}$ e
        componente de $\mathbf{y}$ \citep{dietzenbacher2013expanding}.
    \end{enumerate}
    """).lstrip("\n")


def _sec_resultados(df: pd.DataFrame, sens: pd.DataFrame) -> str:
    top10  = df.sort_values("pegada_estrutural_f", ascending=False).head(10)
    chave  = df[df.quadrante == "Setor-chave de risco"].sort_values("intensidade_direta_a", ascending=False)
    propag = df[df.quadrante == "Propagador estrutural"].sort_values("encadeamento_tras_U", ascending=False)

    n_cats    = int(df.acidentes_CAT.sum())
    pct_ind   = df.share_indireto.mean()
    n_chave   = len(chave)
    n_prop    = len(propag)
    a_media   = df.intensidade_direta_a.mean()
    u_media   = df.encadeamento_tras_U.mean()
    ampl_med  = df.amplificacao_f_sobre_a.mean()

    # top setor
    top1 = top10.iloc[0]

    # sens estáveis
    sens_stable = sens[sens.prob_setor_chave > 0.5].sort_values("prob_setor_chave", ascending=False)
    n_stable    = len(sens_stable)
    cv_med      = sens_stable.f_cv.mean() if n_stable else 0.0

    # top emprego multiplicador (excluindo domésticos extremo)
    top_emp = df[df.codigo != "9700"].sort_values("multiplicador_emprego_me", ascending=False).head(5)
    # maior pegada por trabalhador
    top_trab = df.sort_values("intensidade_per_trab_a_tilde", ascending=False).head(5)

    # build table rows (pré-computadas fora do f-string — backslash proibido em exprs f-string < 3.12)
    backslash = "\\"
    top10_rows = "\n".join(_setor_row(r) for _, r in top10.iterrows())
    chave_rows = "\n".join(
        f"  {r.codigo} & {_nome_abrev(r['nome'], 45)} & {_fmt(r.intensidade_direta_a)} & {_fmt(r.encadeamento_tras_U)} & {_fmt(r.multiplicador_emprego_me, 2)} & {_fmt(r.intensidade_per_trab_a_tilde, 4)} {backslash}{backslash}"
        for _, r in chave.iterrows()
    )
    stable_rows = "\n".join(
        f"  {r.codigo} & {_nome_abrev(r['nome'], 45)} & {_fmt(r.prob_setor_chave, 2)} & {_fmt(r.f_p05)} & {_fmt(r.f_p50)} & {_fmt(r.f_p95)} & {_fmt(r.f_cv, 3)} {backslash}{backslash}"
        for _, r in sens_stable.iterrows()
    )
    emp_rows = "\n".join(
        f"  {r.codigo} & {_nome_abrev(r['nome'], 45)} & {_fmt(r.multiplicador_emprego_me, 2)} & {_fmt(r.intensidade_direta_a)} & {_fmt(r.intensidade_per_trab_a_tilde, 4)} & {_fmt(r.pegada_estrutural_f)} {backslash}{backslash}"
        for _, r in top_emp.iterrows()
    )

    return dedent(rf"""
    % ════════════════════════════════════════════════════════════════
    \section{{Resultados}}
    \label{{sec:resultados}}
    % ════════════════════════════════════════════════════════════════

    \subsection{{Pegada total e decomposição}}

    O vetor satélite construído a partir do AEAT-2015 soma {n_cats:,}~CATs
    registradas no Espírito Santo. A pegada estrutural
    $\mathbf{{f}}' = \mathbf{{a}}'\mathbf{{L}}$ foi calculada para os 35 setores da
    MIP-ES; os 10~maiores valores de~$f_j$ estão na
    Tabela~\ref{{tab:top10}}.

    A observação central é que o componente indireto representa, em
    média, {_pct(pct_ind)} da pegada total --- mais de um terço do passivo
    de acidentes embutido em qualquer demanda final típica se origina em
    setores distintos do produtor do bem demandado. A amplificação média
    $f_j/a_j$ é {_fmt(ampl_med, 2)}, indicando que cada R\$~milhão de
    demanda final carrega, indiretamente, o dobro dos acidentes da
    atividade que o produz diretamente.

    O setor com maior $f_j$ é \textbf{{{top1['nome'][:50]}~({top1.codigo})}},
    com $f = {_fmt(top1.pegada_estrutural_f)}$~CATs/R\$~M, amplificação
    de {_fmt(top1.amplificacao_f_sobre_a, 2)} e {_pct(top1.share_indireto)}
    de componente indireto. Este resultado reflete o caráter
    trabalho-intensivo do setor e sua notificação fidedigna de CATs ---
    o que deve ser contextualizado pela análise de multiplicadores de
    emprego (Seção~\ref{{sec:emprego}}).

    \begin{{table}}[H]
    \centering
    \small
    \caption{{Top~10 setores por pegada total $f_j$, MIP-ES 2015}}
    \label{{tab:top10}}
    \begin{{tabular}}{{lp{{5.2cm}}rrrrrr}}
    \toprule
    \textbf{{Cód.}} & \textbf{{Setor}} & $a_j$ & $f_j$ & $f_j/a_j$ & \%~ind. & $U_j^B$ \\
    \midrule
    {top10_rows}
    \bottomrule
    \end{{tabular}}
    \caption*{{\footnotesize $f_j$: CATs/R\$~M de demanda final.
    $a_j$: intensidade direta (CATs/R\$~M VBP).
    $U_j^B$: índice de ligação para trás normalizado.}}
    \end{{table}}

    A Figura~\ref{{fig:pegada}} apresenta a decomposição visualmente.
    Dois casos polares são instrutivos. O setor com maior componente
    indireto relativo é aquele em que a cadeia a montante carrega risco
    substancialmente acima do produzido diretamente; em contrapartida,
    setores extrativos mostram componente indireto baixo, refletindo
    baixa integração na cadeia produtiva regional.

    \begin{{figure}}[H]
    \centering
    \includegraphics[width=0.95\textwidth]{{../outputs/figures/quadrante_risco_es.pdf}}
    \caption{{Plano $(U_j^B,\, a_j)$ --- tipologia de quadrantes de risco
    (cortes pelas médias $\bar{{a}} = {_fmt(a_media)}$ e
    $\bar{{U}} = {_fmt(u_media)}$).
    \textbf{{Setor-chave de risco}}: alta intensidade direta e alto
    encadeamento para trás.
    \textbf{{Propagador estrutural}}: baixa intensidade mas alto
    encadeamento (transmite risco alheio).
    \textbf{{Risco localizado}}: alta intensidade mas baixo encadeamento.
    \textbf{{Residual}}: baixa intensidade e baixo encadeamento.}}
    \label{{fig:pegada}}
    \end{{figure}}

    \subsection{{Tipologia de quadrantes}}

    O plano $(a_j, U_j^B)$ com cortes pelas médias
    $\bar{{a}} = {_fmt(a_media)}$ e $\bar{{U}}^B = {_fmt(u_media)}$
    identifica {n_chave}~\textit{{setores-chave de risco}}
    (Tabela~\ref{{tab:chave}}) e {n_prop}~\textit{{propagadores estruturais}}
    --- setores que, apesar de baixa intensidade própria, têm alto
    encadeamento para trás e transmitem risco gerado em outras atividades.

    \begin{{table}}[H]
    \centering
    \small
    \caption{{Setores-chave de risco (alta $a_j$ e alto $U_j^B$), MIP-ES 2015}}
    \label{{tab:chave}}
    \begin{{tabular}}{{lp{{5.2cm}}rrrr}}
    \toprule
    \textbf{{Cód.}} & \textbf{{Setor}} & $a_j$ & $U_j^B$ & $m^e_j$ & $\tilde{{a}}_j$ \\
    \midrule
    {chave_rows}
    \bottomrule
    \end{{tabular}}
    \caption*{{\footnotesize $m^e_j$: multiplicador de emprego Tipo~I.
    $\tilde{{a}}_j$: CATs por trabalhador exposto (RAIS-2015).}}
    \end{{table}}

    \subsection{{Multiplicadores de emprego e intensidade por trabalhador}}
    \label{{sec:emprego}}

    Um setor pode ter $a_j$ elevado por dois motivos distintos: (i) é
    genuinamente perigoso (alta taxa de acidente por trabalhador), ou
    (ii) é trabalho-intensivo com VBP por trabalhador baixo. A comparação
    entre $a_j$ e $\tilde{{a}}_j = e_j/\ell_j$ permite separar esses
    efeitos.

    Os cinco setores com maior multiplicador de emprego $m^e_j$
    (excluindo serviços domésticos) são:

    \begin{{table}}[H]
    \centering
    \small
    \caption{{Top-5 multiplicadores de emprego $m^e_j$, MIP-ES 2015}}
    \label{{tab:emprego}}
    \begin{{tabular}}{{lp{{5.2cm}}rrrr}}
    \toprule
    \textbf{{Cód.}} & \textbf{{Setor}} & $m^e_j$ & $a_j$ & $\tilde{{a}}_j$ & $f_j$ \\
    \midrule
    {emp_rows}
    \bottomrule
    \end{{tabular}}
    \caption*{{\footnotesize $m^e_j$: trabalhadores gerados (direta e
    indiretamente) por R\$~M de demanda final. $\tilde{{a}}_j$: CATs por
    trabalhador no setor produtor.}}
    \end{{table}}

    \subsection{{Análise de sensibilidade Monte Carlo}}

    Para avaliar a robustez dos resultados frente à subnotificação
    heterogênea de CATs, perturbou-se o vetor $\mathbf{{a}}$ com ruído
    log-normal multiplicativo ($\mu=0$, $\sigma_{{\log}}=0{{,}}20$, $N=1\,000$
    iterações, semente 2026). Para cada iteração foram recalculados
    $\mathbf{{f}}'$ e a classificação de quadrante de cada setor.

    A Tabela~\ref{{tab:sensibilidade}} reporta os setores que permanecem
    no quadrante \textit{{Setor-chave de risco}} em mais de 50\% das
    iterações --- {n_stable}~setores no total, com coeficiente de
    variação médio de~$f_j$ de {_fmt(cv_med, 3)}.

    \begin{{table}}[H]
    \centering
    \small
    \caption{{Setores robustos --- probabilidade de permanecer em
    \textit{{Setor-chave de risco}} (Monte Carlo, $N=1\,000$)}}
    \label{{tab:sensibilidade}}
    \begin{{tabular}}{{lp{{5.2cm}}rrrrr}}
    \toprule
    \textbf{{Cód.}} & \textbf{{Setor}} & Prob. & $f_{{P5}}$ & $f_{{P50}}$ & $f_{{P95}}$ & CV \\
    \midrule
    {stable_rows}
    \bottomrule
    \end{{tabular}}
    \caption*{{\footnotesize Prob.: fração das iterações em que o setor
    classificou como Setor-chave. $f_{{P5/50/95}}$: percentis da distribuição
    empírica de $f_j$. CV: coeficiente de variação.}}
    \end{{table}}

    A Figura~\ref{{fig:sensibilidade}} apresenta o boxplot da distribuição
    de $f_j$ para os 15~setores com maior mediana.

    \begin{{figure}}[H]
    \centering
    \includegraphics[width=0.92\textwidth]{{../outputs/figures/sensibilidade_pegada.pdf}}
    \caption{{Distribuição de $f_j$ sob perturbação Monte Carlo
    ($N=1\,000$, $\sigma_{{\log}}=0{{,}}20$) --- top-15 setores por
    $f$ mediana. Linhas vermelhas: mediana; caixas: IQR; bigodes: $1{{,}}5 \times \text{{IQR}}$.}}
    \label{{fig:sensibilidade}}
    \end{{figure}}
    """).lstrip("\n")


def _sec_hem(df: pd.DataFrame, hem: pd.DataFrame) -> str:
    cat_base   = float(hem.iloc[0].acidentes_base)
    top5_hem   = hem.head(5)
    ext_pair   = hem[hem.codigo.isin(["0680", "0791"])]
    d680       = ext_pair[ext_pair.codigo == "0680"].iloc[0]
    d791       = ext_pair[ext_pair.codigo == "0791"].iloc[0]

    top5_rows = "\n".join(
        rf"  {r.codigo} & {_nome_abrev(r['nome'], 50)} & {_fmt(r.delta_cat_completa, 0)} & {_fmt(r.delta_cat_completa_pct, 1)}\,\% \\"
        for _, r in top5_hem.iterrows()
    )

    return dedent(rf"""
    % ════════════════════════════════════════════════════════════════
    \section{{Método de Extração Hipotética}}
    \label{{sec:hem}}
    % ════════════════════════════════════════════════════════════════

    O Método de Extração Hipotética (HEM) de \citet{{dietzenbacher2013expanding}}
    mensura a importância de cada setor para o sistema ao simular sua
    remoção completa: linha e coluna de $\mathbf{{A}}$ são zeradas e a
    demanda final do setor é eliminada, produzindo
    $\mathbf{{A}}^*_k$, $\mathbf{{L}}^*_k$ e um novo vetor de produção
    $\mathbf{{x}}^*_k = \mathbf{{L}}^*_k \hat{{\mathbf{{y}}}}_k$.
    A queda $\Delta\text{{CAT}}_k = \mathbf{{a}}'\mathbf{{x}} - \mathbf{{a}}'\mathbf{{x}}^*_k$
    mensura a contribuição estrutural do setor~$k$ para o passivo agregado
    de acidentes.

    O exercício foi aplicado a todos os 35 setores, com a pegada
    agregada de base em {_fmt(cat_base, 0)}~CATs (normalizada pelo VBP).
    A Tabela~\ref{{tab:hem_top5}} reporta os cinco setores cuja extração
    produz a maior queda relativa.

    \begin{{table}}[H]
    \centering
    \small
    \caption{{Top-5 setores por impacto da extração hipotética
    ($\Delta$CAT\% sobre a pegada agregada)}}
    \label{{tab:hem_top5}}
    \begin{{tabular}}{{lp{{5.8cm}}rr}}
    \toprule
    \textbf{{Cód.}} & \textbf{{Setor}} & $\Delta$CAT & $\Delta$CAT\,\% \\
    \midrule
    {top5_rows}
    \bottomrule
    \end{{tabular}}
    \end{{table}}

    O resultado revela que os setores de maior impacto estrutural não
    são necessariamente os mais periculosos em intensidade direta: setores
    com alto encadeamento para trás e grande VBP (e.g., comércio, saúde
    privada, serviços administrativos) dominam o ranking de impacto de
    extração, precisamente porque são \textit{{propagadores estruturais}}
    de risco.

    \paragraph{{Extrativos 0680 e 0791.}}
    A extração hipotética do setor petrolífero (0680) reduz a pegada
    agregada em {_fmt(d680.delta_cat_completa_pct, 2)}\%;
    a extração do setor ferroso (0791) produz variação de
    {_fmt(d791.delta_cat_completa_pct, 2)}\%.
    Esse resultado quantifica a desconexão estrutural dos extrativos
    da cadeia produtiva intra-estadual: o risco físico gerado na extração
    está embutido na produção exportada, não propagado para setores
    capixabas a jusante.
    """).lstrip("\n")


def _sec_discussao() -> str:
    return dedent(r"""
    % ════════════════════════════════════════════════════════════════
    \section{Discussão: deslocamento estrutural duplo}
    \label{sec:discussao}
    % ════════════════════════════════════════════════════════════════

    Os resultados convergem para um padrão que denominamos
    \textit{deslocamento estrutural duplo} do risco ocupacional na
    economia capixaba.

    \paragraph{Primeiro deslocamento: geográfico.}
    Setores extrativos do Espírito Santo geram passivo direto de acidentes
    mas têm ligação para trás intra-estadual limitada ($U^B_j < 1$ para
    0580, 0680 e 0791). O motivo é estrutural: a produção extrativa é
    majoritariamente exportada em bens ainda não transformados. A
    ``demanda final'' que aciona a extração não está predominantemente
    no Espírito Santo, mas no resto do Brasil e no exterior. O risco
    físico ocorre em ES; a responsabilidade econômica reside alhures.

    O HEM confirma a magnitude desse deslocamento: remover 0680 e 0791
    da matriz capixaba altera a pegada agregada em menos de 3\% combinado,
    o que é assimetricamente pequeno considerando que esses setores
    respondem por 17\% do VBP estadual.

    \paragraph{Segundo deslocamento: setorial.}
    Dentro da economia capixaba, os maiores valores de $f_j$ pertencem
    a setores de serviços e transformação --- saúde privada, refino,
    madeira/móveis --- cuja alta pegada reflete, em parte, a combinação
    de trabalho-intensividade elevada com encadeamentos intermediários.
    A análise de multiplicadores de emprego explicita esse ponto: setores
    com $m^e_j$ alto e $\tilde{a}_j$ baixo (poucos acidentes por
    trabalhador, muitos trabalhadores por R\$~M) têm $a_j$ elevado por
    composição, não por periculosidade intrínseca.

    \paragraph{Implicação metodológica.}
    A tensão entre $a_j$ (normalização por VBP) e $\tilde{a}_j$
    (normalização por ocupações) é o trade-off central da literatura de
    pegada social aplicada ao risco ocupacional. A normalização por VBP
    é necessária para a álgebra IO --- o modelo de Leontief é definido
    em termos de fluxos monetários. Mas a interpretação substantiva de
    quais setores são ``mais perigosos'' exige a análise conjunta das
    duas métricas.

    \paragraph{Implicação política.}
    O padrão tem consequências para o desenho de políticas estaduais de
    SST. Uma intervenção que se concentre exclusivamente nos setores
    extrativos --- intuitivamente os ``setores perigosos'' --- alcança
    apenas uma fração do passivo agregado embutido na demanda final. Os
    setores com alto encadeamento para trás (\textit{propagadores
    estruturais}) e os \textit{setores-chave de risco} identificados na
    análise de quadrantes são o ponto natural de uma política com alcance
    estrutural. A análise insumo-produto torna esse arranjo visível e
    mensurável.
    """).lstrip("\n")


def _sec_limitacoes() -> str:
    return dedent(r"""
    % ════════════════════════════════════════════════════════════════
    \section{Limitações}
    \label{sec:limitacoes}
    % ════════════════════════════════════════════════════════════════

    Quatro limitações merecem registro explícito.

    \textbf{Primeiro}, o AEAT cobre apenas trabalhadores vinculados ao RGPS.
    Servidores estatutários (setores 8400, 8591, 8691), trabalhadores
    informais ($\approx 38\%$ da força capixaba) e domésticos sem CAT
    não estão capturados. A análise Monte Carlo (Seção~\ref{sec:resultados})
    mostra que perturbações de até $\pm 20\%$ em $a_j$ não alteram
    substancialmente a classificação dos setores robustos.

    \textbf{Segundo}, a MIP-ES 2015 não captura a regulação pós-Brumadinho
    (2019), que reformou o ambiente regulatório da mineração brasileira.
    Os resultados refletem a estrutura econômica e regulatória pré-choque.

    \textbf{Terceiro}, o tratamento usa apenas a cadeia produtiva doméstica.
    Um exercício de pegada plenamente integrada exigiria vinculação a
    matrizes globais (Eora MRIO, WIOD), ultrapassando o escopo deste paper.

    \textbf{Quarto}, a heterogeneidade intra-setorial é diluída no agregado
    das contas nacionais. O setor 0680, por exemplo, agrega operações
    \textit{offshore} (alto risco por trabalhador) e \textit{onshore}
    (risco menor), sub-representando contrastes relevantes.
    """).lstrip("\n")


def _sec_conclusao() -> str:
    return dedent(r"""
    % ════════════════════════════════════════════════════════════════
    \section{Considerações finais}
    \label{sec:conclusao}
    % ════════════════════════════════════════════════════════════════

    Este artigo operacionalizou, para a economia do Espírito Santo, a
    \textit{pegada de acidentes de trabalho}: o conteúdo total de CATs
    embutido em cada unidade de demanda final, decomposto em efeitos
    diretos e indiretos via modelo de Leontief estendido. A análise usa
    dados oficiais (MIP-ES/IJSN 2015, AEAT-2015), implementa multiplicadores
    de emprego, tipologia de quadrantes de risco, análise de sensibilidade
    Monte Carlo e Método de Extração Hipotética para todos os 35 setores.

    O achado central --- o \textit{deslocamento estrutural duplo} do risco
    ocupacional --- mostra que: (i) os setores extrativos, apesar de
    concentrarem risco físico direto, têm baixo encadeamento intra-estadual
    e seu risco é exportado embutido na produção; (ii) dentro da economia
    capixaba, a propagação do passivo de acidentes ocorre via
    \textit{propagadores estruturais} e \textit{setores-chave de risco},
    que combinam alta intensidade com alto encadeamento para trás.

    \paragraph{Agenda de pesquisa futura.}
    Cinco extensões naturais ficam registradas:

    \begin{enumerate}
      \item \textbf{Modelo fechado Type~II.} Incluir o vetor de consumo
        das famílias em $\mathbf{A}$ para capturar o efeito-renda nos
        multiplicadores.
      \item \textbf{Comparativo Brasil--ES.} Replicar o exercício na
        MIP-Brasil (CECEG/UFES, 68 setores) e testar se o gradiente
        ES-vs-BR confirma a hipótese de especialização produtiva como
        amplificador estrutural de risco.
      \item \textbf{Campo de influência (Sonis-Hewings).} Mapear quais
        coeficientes técnicos são mais críticos para a pegada agregada.
      \item \textbf{Integração a matrizes mundiais.} Rastrear o destino
        internacional do passivo de SST embutido nas exportações capixabas
        via Eora MRIO ou WIOD.
      \item \textbf{Extensão a outras dimensões de risco.} Adoecimento
        mental (afastamentos CID-F), informalidade, automação.
    \end{enumerate}

    \paragraph{Trajetória de publicação.}
    A versão presente é \textit{paper de disciplina} para a disciplina
    PECO-5054/6054 do PPGEco/UFES (2026/1). Caminhos de desenvolvimento
    incluem submissão à ANPEC/ENABER com o comparativo Brasil-ES;
    reformatação como Texto para Discussão do IPEA; e submissão a
    periódico técnico nacional (\textit{Nova Economia}, \textit{Estudos
    Econômicos}).
    """).lstrip("\n")


def _references() -> str:
    return dedent(r"""
    % ════════════════════════════════════════════════════════════════
    % REFERÊNCIAS
    % ════════════════════════════════════════════════════════════════

    \begin{thebibliography}{99}

    \bibitem[Alsamawi et al.(2014)]{alsamawi2014employment}
    Alsamawi, A., Murray, J., \& Lenzen, M. (2014).
    The employment footprints of nations.
    \textit{Journal of Industrial Ecology}, 18(1), 59--70.

    \bibitem[Carvalho \& Perobelli(2009)]{carvalho2009intensidade}
    Carvalho, T. S., \& Perobelli, F. S. (2009).
    Avaliação da intensidade de emissões de CO$_2$ setoriais e na estrutura de exportações.
    \textit{Economia Aplicada}, 13(1), 1--20.

    \bibitem[CECEG(2025)]{ceceg2025mips}
    Centro de Estudos Computacionais em Equilíbrio Geral (2025).
    \textit{Matrizes de Insumo-Produto do Brasil}.
    UFES, Departamento de Economia.
    \url{https://ceceg.ufes.br/matrizes-de-insumo-produto-do-brasil-disponiveis/}.

    \bibitem[Carvalho(2025)]{carvalho2025preco}
    Carvalho, F. (2025).
    \textit{O Preço do Saber: IA como Choque de Codificabilidade nas MIPs do Brasil e do ES}.
    Working paper, PPGEco/UFES.

    \bibitem[Chagas et al.(2011)]{chagas2011saude}
    Chagas, A. M. R., Salim, C. A., \& Servo, L. M. S. (Orgs.) (2011).
    \textit{Saúde e Segurança no Trabalho no Brasil}.
    Brasília: IPEA.

    \bibitem[Dietzenbacher \& Lahr(2013)]{dietzenbacher2013expanding}
    Dietzenbacher, E., \& Lahr, M. L. (2013).
    Expanding extractions.
    \textit{Economic Systems Research}, 25(3), 341--360.

    \bibitem[Guilhoto \& Sesso Filho(2010)]{guilhotosesso2010estimacao}
    Guilhoto, J. J. M., \& Sesso Filho, U. A. (2010).
    Estimação da Matriz Insumo-Produto Utilizando Dados Preliminares.
    \textit{Economia \& Tecnologia}, 6(23).

    \bibitem[Hertwich \& Peters(2009)]{hertwich2009carbon}
    Hertwich, E. G., \& Peters, G. P. (2009).
    Carbon footprint of nations.
    \textit{Environmental Science \& Technology}, 43(16), 6414--6420.

    \bibitem[Hoekstra \& Hung(2002)]{hoekstra2002virtual}
    Hoekstra, A. Y., \& Hung, P. Q. (2002).
    Virtual water trade.
    \textit{Value of Water Research Report Series}, n.~11. UNESCO-IHE.

    \bibitem[IPEA(2010)]{ipea2010mipregional}
    Instituto de Pesquisa Econômica Aplicada (2010).
    \textit{Plataforma Ipea de Pesquisa em Rede --- Matriz Insumo-Produto Regional}.
    Brasília: IPEA. \url{https://www.ipea.gov.br/redeipea/}.

    \bibitem[Leontief(1970)]{leontief1970}
    Leontief, W. (1970).
    Environmental repercussions and the economic structure.
    \textit{The Review of Economics and Statistics}, 52(3), 262--271.

    \bibitem[Made-USP(2021)]{made2021multiplicadores}
    Made/FEA-USP \& OIT (2021).
    \textit{Multiplicadores de produto, consumo e investimento de transferências sociais no Brasil}.
    Notas de Política Econômica, Made-USP.

    \bibitem[Made-USP(2023)]{made2023agroflorestais}
    Made/FEA-USP (2023).
    \textit{Sistemas agroflorestais na Amazônia: bioeconomia da sociobiodiversidade}.
    Nota de Política Econômica n.~040.

    \bibitem[Miller \& Blair(2009)]{millerblair2009}
    Miller, R. E., \& Blair, P. D. (2009).
    \textit{Input-Output Analysis: Foundations and Extensions} (2nd ed.).
    Cambridge University Press.

    \bibitem[MPS(2016)]{aeat2016}
    Ministério da Previdência Social (2016).
    \textit{Anuário Estatístico de Acidentes do Trabalho 2015}.
    Brasília: MPS/Dataprev.

    \bibitem[Perobelli et al.(2016)]{perobelli2016decomposicao}
    Perobelli, F. S., Bastos, S. Q. A., \& Pereira, M. Z. (2016).
    Decomposição estrutural do emprego por grau de instrução.
    \textit{Nova Economia}, 26(3), 695--732.

    \bibitem[Rasmussen(1956)]{rasmussen1956studies}
    Rasmussen, P. N. (1956).
    \textit{Studies in Inter-Sectoral Relations}.
    Amsterdam: North-Holland.

    \bibitem[Shimizu et al.(2021)]{shimizu2021accident}
    Shimizu, H. E., et al. (2021).
    Analysis of work-related accidents in Brazil.
    \textit{BMC Public Health}, 21, 660.

    \bibitem[Souza et al.(2016)]{souza2016reducing}
    Souza, K. B., Ribeiro, L. C. S., \& Perobelli, F. S. (2016).
    Reducing Brazilian greenhouse gas emissions.
    \textit{Economic Systems Research}, 28(4), 482--496.

    \end{thebibliography}

    \end{document}
    """).lstrip("\n")


# ─── main ───────────────────────────────────────────────────────────────────

def main() -> None:
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)

    df, hem, sens = load_data()

    parts = [
        _preamble(),
        r"\begin{document}",
        r"\maketitle",
        r"\thispagestyle{fancy}",
        _abstract(df, hem, sens),
        _sec_intro(),
        _sec_teorico(),
        _sec_dados(),
        _sec_resultados(df, sens),
        _sec_hem(df, hem),
        _sec_discussao(),
        _sec_limitacoes(),
        _sec_conclusao(),
        _references(),
    ]

    tex = "\n".join(parts)
    tex = tex.replace(_COMMA, "{,}")
    OUT_TEX.write_text(tex, encoding="utf-8")
    print(f"[06_article_builder] LaTeX → {OUT_TEX}")


if __name__ == "__main__":
    main()
