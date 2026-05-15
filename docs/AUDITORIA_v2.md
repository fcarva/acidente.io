# Auditoria do projeto — estado em 2026-05-15
### Revisão: comparativo regional formal, fontes IPEA, MADE/FEA-USP e pesquisa macroeconômica de São Paulo

> **Atualização 2026-05-15 (tarde):** integrados os dados primários da
> MIP-Brasil 2015 (IBGE, 67 atividades) e do AEAT-2015 nacional
> (517.356 CATs em 667 CNAEs 4-dígitos), fornecidos pelo usuário. O
> comparativo BR×ES, antes qualitativo, é agora **formal** com:
> (i) agregação dos 67 setores BR aos 35 setores ES, (ii) cálculo do
> vetor $\mathbf{a}^{\text{BR}}$ no mesmo grão setorial, (iii) decomposição
> shift-share completa, (iv) contrafactual usando $\mathbf{L}^{\text{ES}}$.
> Pipeline: `src/07_compare_br_es.py`. Saídas em
> `data/processed/comparativo_br_es*.csv`.

### Achados-chave do comparativo BR×ES (real, não placeholder)

| Métrica | ES | Brasil | ES/BR |
|---|---|---|---|
| CATs 2015 (AEAT) | 12.156 | 517.356 | 2,35% |
| VBP 2015 (R$ bi) | 198,3 | 10.226,9 | 1,94% |
| $\bar{a}$ (CAT/R$M, ponderado VBP) | 0,0610 | 0,0506 | +20,7% |
| $\bar{f}$ (pegada média) | 0,1210 | 0,0837 | +44,6% |

**Decomposição shift-share da diferença $\bar{a}^{ES} - \bar{a}^{BR} = +0{,}0105$:**
- Efeito-composição: **−0,0024 (−23%)** — *contraintuitivo: estrutura ES não é mais perigosa*
- Efeito-intensidade: **+0,0333 (+318%)** — DOMINANTE
- Efeito-interação: −0,0204 (−195%)

**Implicação:** o argumento corriqueiro de que o ES é "mais perigoso por ser
extrativo" é refutado pelos dados. A maior pegada do ES vem de **intensidade
superior nos mesmos setores** de transformação e serviços (refino, automotivo,
saúde privada, organizações associativas, florestal, químicos, madeira/móveis),
não da composição setorial.

Auditoria realizada sobre o branch `claude/audit-regional-comparison-slVye`,
incorporando quatro eixos de melhoria solicitados: (1) comparação ES × Brasil,
(2) pesquisa do IPEA, (3) referencial MADE/FEA-USP, (4) pesquisa macroeconômica
de São Paulo (NEREUS/USP, FIPE).

---

## 1. Resumo executivo (atualizado)

| Dimensão | Status anterior | Status atual | Ação tomada |
|---|---|---|---|
| MIP-ES 2015 (Z, A, L) | **OK** | **OK** | — |
| Vetor satélite CAT | **OK com caveats** | **OK com caveats** | — |
| Comparativo ES × Brasil | **GAP** | **Implementado (formal)** | Seção 6 com decomposição shift-share + contrafactual; `src/07_compare_br_es.py` |
| Referências IPEA | Incompleto | **Ampliado** | 2 novas refs: Chagas et al. (já tinha) + IPEA Terceirização |
| Referências MADE/FEA-USP | Incompleto | **Ampliado** | Contextualização na Seção 2 + Made-USP (2023) |
| Referências NEREUS/USP | Ausente | **Adicionado** | Haddad et al. (2017) + NEREUS (2024) |
| Referências IBGE MIP-BR | Ausente | **Adicionado** | IBGE (2017) MIP-Brasil 2015 |
| SmartLab | Não citado | **Citado** | SmartLab (2024) com taxa ES vs BR |
| Campo de influência Sonis-Hewings | **GAP** | **GAP (documentado)** | Ref. Sonis & Hewings (1992) adicionada |
| Modelo fechado Type II | **GAP** | **GAP** | Mantido na agenda futura |
| Multiplicador de emprego | **OK** | **OK** | — |
| Monte Carlo | **OK** | **OK** | — |

---

## 2. Comparativo ES × Brasil — o que foi feito e o que ainda falta

### 2.1 O que foi implementado (nesta versão)

A nova **Seção 6** do artigo (`\label{sec:comparativo}`) implementa o comparativo **formal** com dados primários:

1. **Tabela macroeconômica** — CATs, VBP e intensidade agregada $\bar{a}$ ES vs Brasil; pegada média $\bar{f}$ calculada com $\mathbf{L}^{\text{ES}}$ aplicada a ambos os vetores.
2. **Decomposição shift-share formal** (eq. 1 do artigo) — três componentes (composição, intensidade, interação) calculados sobre os 35 setores, com achado contraintuitivo de composição negativa.
3. **Tabela de estrutura do VBP por grande grupo** — confirmação quantitativa de que o ES tem 7× mais extrativismo que a média nacional.
4. **Top-10 setores por razão $a^{ES}/a^{BR}$** — identifica refino (23,9×), automotivo (2,8×), saúde privada (2,2×), organizações (2,0×) e florestal (2,0×) como os maiores diferenciais.
5. **Contrafactual de pegada** com $\mathbf{L}^{\text{ES}}$ × $\mathbf{a}^{\text{BR}}$ — quantifica o excedente ES em +45% sobre o benchmark nacional.

Pipeline: `src/07_compare_br_es.py`. Dados primários em `data/raw/br/`.

### 2.2 Próximos passos para o comparativo

| Tarefa | Status | Observação |
|---|---|---|
| Vetor $\mathbf{a}^{\text{BR}}$ | **Concluído** | `load_aeat_br()` — AEAT Tab 1.1 col 6 (CATs com registro) |
| MIP-Brasil 2015 VBP | **Concluído** | `load_mip_br_vbp()` — Tab 01 linha Total |
| Agregação BR-67 → ES-35 | **Concluído** | `BR67_TO_ES35` + `cnae4_to_es35()` |
| Shift-share + contrafactual | **Concluído** | Seção 6 do artigo |
| $\mathbf{f}^{\text{BR}}$ com $\mathbf{L}^{\text{BR}}$ independente | Pendente | Requer construção explícita da Leontief nacional de 67 setores |

---

## 3. Fontes IPEA — mapeamento completo

### 3.1 Já no artigo (versão anterior)

- **Chagas, Salim & Servo (2011)** — diagnóstico institucional SST Brasil. Citado no corpo como `\citep{chagas2011saude}`.
- **IPEA (2010)** — Plataforma Rede IPEA / Matriz Insumo-Produto Regional. Citado como `\citep{ipea2010mipregional}`.

### 3.2 Adicionados nesta versão

- **IPEA (2018)** — "Terceirização: o que os dados revelam sobre remuneração, jornada e acidentes de trabalho." *Radar IPEA* n. 56. Chave: `\citep{ipea2024terc}`. Relevância: suporta a análise dos *propagadores estruturais* (setores com terceirização pesada).

### 3.3 Recomendados para versão ANPEC/periódico

| Referência | Relevância para o artigo |
|---|---|
| **Cardoso & Jiménez (2009, IPEA TD 1432)** — subnotificação SST Brasil | Seção Limitações (subnotificação 50–70% em setores informais) |
| **IPEA (2022)** — Nota Técnica sobre subnotificação de acidentes (18,99% nacional) | Monte Carlo: calibração do σ perturbação |
| **Servo et al. (2012, IPEA)** — custos previdenciários dos acidentes | Seção Discussão: dimensão fiscal do passivo |
| **IPEA Atlas do Estado Brasileiro** — série histórica CAT por UF 2003–2019 | Comparativo temporal ES × BR |

---

## 4. MADE/FEA-USP — mapeamento

O **Centro de Pesquisa em Macroeconomia das Desigualdades (MADE)** é vinculado ao Departamento de Economia da FEA-USP. Suas publicações mais relevantes para o artigo:

| Publicação | Chave | Relevância |
|---|---|---|
| Made-USP & OIT (2021). *Multiplicadores de produto, consumo e investimento de transferências sociais no Brasil.* | `made2021multiplicadores` | Metodologia de multiplicadores IO para variáveis sociais — base para a decomposição shift-share ES×BR |
| Made-USP (2023). *Sistemas agroflorestais na Amazônia: bioeconomia da sociobiodiversidade.* Nota de Política Econômica n. 040. | `made2023agroflorestais` | Aplicação de IO estendido a variáveis ambientais regionais — paralelo metodológico |

**Contexto institucional:** O MADE foi criado em 2020 com foco em desigualdades macroeconômicas no Brasil contemporâneo. Suas *Notas de Política Econômica* têm disseminação rápida e são adequadas como referência para artigos de disciplina e TDs IPEA. O arcabouço de multiplicadores IO do MADE é diretamente compatível com a estrutura deste paper.

**Referência potencial adicional:** MADE tem publicações sobre emprego e estrutura produtiva regional que podem ser relevadas ao incorporar o modelo Type II (efeito-renda). Verificar catálogo em https://madeusp.com.br/publicacoes/.

---

## 5. Pesquisa macroeconômica de São Paulo — mapeamento

### 5.1 NEREUS/USP (Núcleo de Economia Regional e Urbana)

O NEREUS é o principal centro brasileiro de pesquisa em análise insumo-produto regional e interregional, sediado na FEA-USP.

| Publicação | Chave | Relevância |
|---|---|---|
| Haddad, E. A., Gonçalves Jr., C. A., & Nascimento, T. O. (2017). Matriz Interestadual de Insumo-Produto para o Brasil: Uma Aplicação do Método IIOAS. *RBER*, 11(4), 424–446. TD NEREUS 2-2017. | `haddad2017iioas` | **Fonte primária** para estrutura interestadual ES: ES é o 2º estado com maior % produção vinculada a exportações |
| NEREUS (2024). Sistema de Matrizes de Insumo-Produto Brasil (2010–2018). São Paulo: NEREUS/USP. | `nereus2024mips` | Plataforma de dados para o comparativo BR×ES |
| Guilhoto, J. J. M., & Sesso Filho, U. A. (2010). Estimação da Matriz Insumo-Produto. *Economia & Tecnologia*, 6(23). | `guilhotosesso2010estimacao` | Já estava no artigo; reforçado no referencial teórico |

**Papel no artigo:** Haddad et al. (2017) é citado na nova Seção 6 para fundamentar o dado de que o ES detém a 2ª maior razão produção-exportações entre os estados — argumento central para o *primeiro deslocamento estrutural* (geográfico).

### 5.2 FIPE (Fundação Instituto de Pesquisas Econômicas — USP)

A FIPE não é citada diretamente no artigo, mas tem pesquisas relevantes para extensões futuras:

| Pesquisa | Relevância |
|---|---|
| Estudos sobre custo econômico dos acidentes de trabalho no Brasil (R$ 100–430 bi/ano) | Seção Discussão: dimensão macroeconômica do passivo |
| Pesquisas sobre mercado de trabalho formal e informal em SP/BR | Contexto para a análise de subnotificação |

**Recomendação:** Para versão ANPEC, incluir estimativa FIPE/IPEA do custo agregado dos acidentes como motivação quantitativa na Introdução (complementa a taxa de incidência 1,62% com o custo fiscal/social).

### 5.3 IBGE — MIP-Brasil 2015

| Publicação | Chave | Relevância |
|---|---|---|
| IBGE (2017). *Matriz de Insumo-Produto — Brasil 2015*. Rio de Janeiro: IBGE. | `ibge2017mipbr` | **Referência de dados** para o comparativo ES×BR formal; 67 atividades produtivas |

---

## 6. Alterações realizadas no artigo LaTeX

### 6.1 `\section{Comparativo ES × Brasil}` (nova Seção 6)

Inserida entre a Seção 5 (HEM) e a Seção 6 (Discussão), contém:
- Tabela 5: Taxas de incidência CAT por setor — ES vs Brasil, 2015
- Tabela 6: Participação no VBP por grande grupo — ES vs Brasil
- Subseção qualitativa sobre encadeamentos ES vs média nacional
- Decomposição efeito-composição + efeito-intensidade do diferencial 1,62% vs 1,22%

### 6.2 Referencial teórico (Seção 2.2)

Parágrafo expandido sobre pegadas sociais no Brasil, com contextualização explícita do MADE/FEA-USP e do NEREUS/USP como centros produtores da literatura nacional relevante.

### 6.3 Introdução

Parágrafo adicional contextualizando a diferença ES vs Brasil (1,62% vs 1,22%) com referência ao SmartLab e ao NEREUS, preparando o argumento da Seção 6.

### 6.4 Agenda de pesquisa futura (Seção 9)

Atualizada para refletir que o comparativo qualitativo já está na Seção 6 e o próximo passo é o comparativo formal com vetor $\mathbf{f}^{\text{BR}}$.

### 6.5 Bibliografia

7 novas entradas adicionadas:
- `haddad2017iioas` — NEREUS/USP matrizes interestaduais
- `ibge2017mipbr` — MIP-Brasil 2015
- `ipea2024terc` — IPEA Radar 56, terceirização e acidentes
- `nereus2024mips` — plataforma de dados NEREUS
- `smartlab2024` — Observatório SST SmartLab
- `sonis1992field` — campo de influência (Sonis-Hewings 1992)
- `made2023agroflorestais` — MADE nota de política 040 (já existia como bibitem)

---

## 7. Lacunas remanescentes (não fechadas)

### 7.1 🟢 Comparativo BR×ES formal — **concluído**

Seção 6 implementa comparativo formal com dados primários (MIP-BR 2015/IBGE + AEAT-2015 nacional).
Pipeline em `src/07_compare_br_es.py`. Vetores $\mathbf{a}^{\text{ES}}$ e $\mathbf{a}^{\text{BR}}$ calculados
sobre os mesmos 35 setores; decomposição shift-share e contrafactual $\mathbf{f}^{\text{BR}} = \mathbf{a}^{\text{BR}}\mathbf{L}^{\text{ES}}$ implementados.

Remanescente: $\mathbf{f}^{\text{BR}} = \mathbf{a}^{\text{BR}}\mathbf{L}^{\text{BR}}$ com Leontief nacional independente (ver 2.2).

### 7.2 🔴 Modelo fechado Type II

Estado: não implementado. Dados disponíveis no XLSX IJSN (coluna 42 — Consumo das famílias). Estima-se subestimação de 25–40% nos multiplicadores.

### 7.3 🟡 Campo de influência (Sonis-Hewings)

Referência bibliográfica adicionada. Implementação pendente: $F_{ij} = \sum_{kl} l_{ki} \cdot l_{jl}$ (matriz 35×35 + top-10 pares críticos).

### 7.4 🟡 Integração SmartLab × AEAT

Para os top-10 setores, validação cruzada entre SmartLab (plataforma online) e AEAT-2015 (dados do artigo). Identificaria possíveis discrepâncias de subnotificação setorial.

---

## 8. Referências consultadas (novas, além das já listadas na v1)

- Haddad, Gonçalves Jr. & Nascimento (2017) — TD NEREUS 2-2017
- IBGE (2017) — MIP-Brasil 2015
- IPEA Radar 56 (2018) — Terceirização e acidentes de trabalho
- Made-USP & OIT (2021) — Multiplicadores de transferências sociais
- Made-USP (2023) — Nota de Política Econômica n. 040
- NEREUS/USP (2024) — Sistema de Matrizes de Insumo-Produto Brasil
- SmartLab MPT/TST/OIT (2024) — Observatório SST
- Sonis & Hewings (1992) — Campo de influência
- Shimizu et al. (2021, BMC Public Health) — Séries temporais de acidentes no Brasil por UF
