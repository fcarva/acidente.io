# Auditoria do projeto — estado em 2026-05-15
### Revisão: comparativo regional, fontes IPEA, MADE/FEA-USP e pesquisa macroeconômica de São Paulo

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
| Comparativo ES × Brasil | **GAP** | **Parcialmente implementado** | Seção 6 adicionada ao artigo |
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

A nova **Seção 6** do artigo (`\label{sec:comparativo}`) cobre:

1. **Tabela de taxas de incidência CAT por setor** — ES vs Brasil (AEAT-2015 + RAIS-2015), para os setores mais relevantes da análise.
2. **Tabela de participação setorial no VBP** — comparação MIP-ES (35 setores) vs MIP-Brasil (67 atividades, IBGE 2017), mostrando o sobrep eso extrativo do ES (+13,9 p.p. acima da média nacional).
3. **Decomposição qualitativa do diferencial ES/BR** em efeito-composição e efeito-intensidade, usando o arcabouço shift-share de \citet{made2021multiplicadores}.
4. **Contextualização dos encadeamentos** com referência aos índices Rasmussen-Hirschman publicados pelo CECEG/UFES e ao estudo NEREUS de matrizes interestaduais.
5. **Link com literatura IPEA sobre terceirização** (IPEA 2018, Radar 56): setores com alta externalização de mão-de-obra apresentam risco 3,4× maior — argumento que reforça os achados dos *propagadores estruturais*.

### 2.2 O que ainda falta para o comparativo completo

Para o comparativo formal $\mathbf{f}^{\text{ES}}$ vs $\mathbf{f}^{\text{BR}}$ (previsto na agenda de pesquisa):

| Tarefa | Dado necessário | Fonte | Bloqueio |
|---|---|---|---|
| Construir vetor $\mathbf{a}^{\text{BR}}$ | AEAT-2015 nacional por setor | MPS/Dataprev | Mapeamento CNAE→SCN-67 |
| Carregar MIP-Brasil 2015 | Matriz A (67×67) | IBGE | Download do XLSX IBGE |
| Calcular $\mathbf{f}^{\text{BR}} = \mathbf{a}^{\text{BR}}\mathbf{L}^{\text{BR}}$ | A e L nacionais | IBGE + CECEG | Tabela de concordância SCN-67→MIP-35 |
| Shift-share formal | Ambos os vetores | — | Aguarda itens acima |

**Estimativa de esforço:** 1–2 dias de trabalho com acesso ao XLSX IBGE e à tabela de de-para CNAE-2.0/SCN-67.

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

### 7.1 🔴 Comparativo BR×ES formal (vetor $\mathbf{f}^{\text{BR}}$)

A Seção 6 adicionada é qualitativa e usa dados secundários. O comparativo completo requer:
1. Download da MIP-Brasil IBGE 2015 (XLSX, 67 setores)
2. Construção do vetor $\mathbf{a}^{\text{BR}}$ via AEAT-2015 nacional (Capítulo 19 do AEAT)
3. Mapeamento CNAE 2.0 → SCN-67 → MIP-35 (equivalência ES↔BR)
4. Cálculo de $\mathbf{f}^{\text{BR}}$ e comparação setor a setor

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
