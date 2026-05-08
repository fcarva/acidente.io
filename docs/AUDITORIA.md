# Auditoria do projeto — estado em 2026-05-08

Auditoria realizada após a integração de dados oficiais (commits `c4043de`
a `fb321d8`) cruzando o pipeline atual com a literatura brasileira de
acidentes de trabalho, metodologia de matriz insumo-produto e fontes do
Ministério do Trabalho/Previdência.

---

## 1. Resumo executivo

| Dimensão | Status | Notas |
|---|---|---|
| MIP-ES 2015 (Z, A, L) | **OK** | XLSX oficial IJSN (Tabelas 11+12); ‖(I−A)L − I‖_F = 2.06e-15 |
| Vetor satélite CAT | **OK com caveats** | AEAT-2015 oficial; 92 entradas no de-para; cobertura 100% das CNAEs presentes |
| Modelo de Leontief aberto (f' = a'L) | **OK** | Implementado, validado |
| Rasmussen-Hirschman backward | **OK** | U_j = média coluna L / média global L |
| Multiplicador de produção m_j | **OK** | Σ_i l_ij |
| HEM (Dietzenbacher) | **OK** | Linha+coluna zeradas; variante Miller-Lahr documentada |
| Modelo fechado (Type II) | **OK** | 06_modelo_fechado.py; aproximação VA/X p/ wages; induzido = 36,7% |
| Multiplicador de emprego | **OK** | Em 02_io_model: e, m_e, ã = CAT/L, f̃ |
| Análise de sensibilidade Monte Carlo | **OK** | 05_sensibilidade.py; 6 setores robustos a ±25% |
| Campo de influência (Sonis-Hewings) | **OK** | 07_campo_influencia.py; Φ_ij = (a'L)_i · (L1)_j |
| Decomposição da pegada por demanda | **OK** | 08_decomposicao_demanda.py; 30% interestadual, 14% exterior |
| Subnotificação (correção) | **GAP** | INSS estima 19% nacional; varia por setor |
| Setores RJU (8591, 8691) | **LIMITAÇÃO** | RGPS não cobre estatutários |
| Serviços domésticos (9700) | **LIMITAÇÃO** | Subnotificação severa (CAT=0 em 2015) |

---

## 2. Validação dos números

### 2.1 Total de CATs no Espírito Santo, 2015

| Fonte | Total | Observação |
|---|---|---|
| AEAT-2015, Tabela 19.1, linha "TOTAL" | **13.245** | Inclui CNAEs não-classificadas |
| Soma 4-dígitos (com_cat + sem_cat) | 12.299 | Diferença 946 = "Não classificada" |
| Soma com_cat 2015 (4-dig) | 12.156 | Igual a típico+trajeto+doença |
| Soma típico+trajeto+doença (4-dig) | 9.366+2.621+169 = 12.156 | ✓ consistência interna |
| Vetor MIP-35 agregado | 12.156 | ✓ identidade preservada após de-para |

**Plausibilidade:** ES tinha ~750 mil trabalhadores formais no RAIS-2015. Taxa
1.62%, ligeiramente acima da média nacional (1.22%) — coerente com perfil
industrial-extrativo (ArcelorMittal, Petrobras, Vale, rochas ornamentais).

**Lacuna:** os 946 CATs de "CNAE não classificada" (linha TOTAL − soma 4-dig)
não são alocáveis a nenhum setor MIP-35. Representam 7,1% do total declarado.
Decisão: deixar fora (consistente com a maioria dos estudos brasileiros que
trabalham com 4-dig).

### 2.2 Subnotificação (literatura)

- **INSS (2022):** 18,99% de subnotificação nacional, com variação severa
  por setor (saúde melhor, agropecuária pior).
- **Cardoso & Jiménez (2009), Wünsch Filho (2004):** subnotificação chega
  a 50–70% em setores com alta informalidade (agropecuária, construção,
  serviços domésticos).
- **AEAT cobre apenas RGPS** (CLT) → **não captura**:
  - Servidores estatutários (8400 parcial, 8591, 8691)
  - Trabalhadores informais (~40% da força de trabalho)
  - Trabalhadores autônomos sem CAT registrada

**Implicação:** o vetor `a` é um **piso** sub-estimado. A robustez do
"deslocamento estrutural duplo" frente a perturbações em `a_j` é o teste
metodológico fundamental que ainda **não foi feito** (gap 2.1).

### 2.3 Top setores: comparação com literatura

| Setor (top a_j) | Nosso a_j | Coerência com literatura |
|---|---|---|
| 8692 Saúde privada | 0.648 | ✓ Saúde tem notificação fidedigna; alta intensidade ergonômica/biológica |
| 1900 Refino petróleo | 0.320 | ⚠ Dependente do tamanho pequeno do setor no ES (R$ 328M, 105 CATs) |
| 1600 Madeira/móveis | 0.220 | ✓ Setor historicamente acidentário |
| 7800 Atividades adm | 0.156 | ✓ Inclui terceirização pesada |
| 5280 Armazenamento | 0.154 | ✓ Acidentes de carga típicos |
| 2900 Automotivo | 0.147 | ✓ Setor manufatureiro com alta exposição |

Top extraídos pelo HEM (Dietzenbacher completa):

| Setor | ΔCAT% | Interpretação |
|---|---|---|
| 4500 Comércio | 17,2% | Alto encadeamento (compra inputs de 8692, 4900, 7800) |
| 8692 Saúde privada | 12,6% | Alta intensidade direta |
| 7800 Adm/serviços | 8,4% | Encadeamento médio + intensidade média |
| 4900 Transporte | 6,0% | Trajeto + carga |
| 4180 Construção | 5,5% | Setor-chave clássico |

**Crítica:** o ranking HEM premia muito setores grandes (Comércio é o maior
ativo do ES). O artigo deve reportar **tanto** ranking absoluto (ΔCAT) quanto
relativo (ΔCAT / X_k) para distinguir "setor estruturalmente perigoso" de
"setor grande que arrasta tudo".

---

## 3. Lacunas metodológicas (programa da disciplina PECO-5054)

### 3.1 🔴 Modelo fechado (Type II) — Item 2.5

**Estado:** modelo aberto apenas. O programa pede explicitamente Type I + II.

**O que falta:**

```
Ā = [ A    h ]    onde h = vetor consumo das famílias / X
    [ ω'   0 ]          ω = vetor remunerações / X (ou empregos/X)

L̄ = (I − Ā)^-1   (n+1 × n+1)
```

A pegada Type II separa **direto + indireto + induzido (efeito-renda)**.
Sem isso, todos os multiplicadores estão sub-estimados em ~25–40%.

**Dados necessários:** vetor consumo das famílias por setor (coluna FBKF/FBC
da TRU) e vetor de remunerações. **Disponíveis no XLSX da MIP-ES** (que
ainda não temos no `data/raw/` por bloqueio de allowlist).

### 3.2 🔴 Multiplicador de emprego — Item 2.4

**Estado:** ocupações estão no `setores.csv`, mas não usadas no modelo.

**Fórmulas:**
- Coeficiente de emprego direto: `e_j = Ocupações_j / X_j`
- Multiplicador de emprego Tipo I: `m^e_j = Σ_i e_i · l_ij`
- Taxa CAT/trabalhador (alternativa a a_j): `ã_j = CAT_j / Ocupações_j`

**Por que importa:** `a_j = CAT/X` enviesa o ranking a favor de setores
trabalho-intensivos com baixo VBP (justamente os de baixo salário e alto
risco). `ã_j = CAT/L` corrige para o tamanho real da força de trabalho
exposta. **Comparar os dois rankings é o exercício clássico de robustez.**

### 3.3 🔴 Análise de sensibilidade Monte Carlo — Item 2.1

**Estado:** ausente. O paper não tem nenhuma estatística de incerteza.

**Implementação proposta:**
1. Perturbar `a_j` com ruído log-normal ±20% (refletir subnotificação heterogênea).
2. 1000 iterações; recalcular f, U, quadrantes em cada uma.
3. Reportar: % de iterações em que cada setor permanece em "Setor-chave".

**Motivação literária:** com subnotificação variando 19–70% por setor, a
robustez do achado central é a primeira pergunta de banca/revisor.

### 3.4 🟡 Campo de influência (Sonis-Hewings) — Item 3.2

**Estado:** não implementado. Útil mas não bloqueador.

`F_ij = Σ_kl l_ki · l_jl` — identifica quais relações intersetoriais são
mais críticas para a pegada total. Usado tipicamente em análises avançadas.

### 3.5 🟡 Decomposição estrutural (SDA)

Comparar MIP-ES 2015 com MIP-Brasil 2015 (NEREUS/CECEG). Decompor as
diferenças em: efeito de mudança em A, efeito de mudança em a, efeito
de mudança em Y. **Extensão futura (ANPEC).**

---

## 4. Limitações documentadas (não-fechadas, mas declaradas)

### 4.1 Cobertura RGPS

- **8591 Educação pública**: 0 CATs no AEAT (estatutários, não-RGPS).
  Fonte alternativa: SIASS (Subsistema Integrado de Atenção à Saúde do
  Servidor) — federal apenas; para municipais/estaduais ES não há base
  pública unificada.
- **8691 Saúde pública**: idem.
- **8400 Adm Pública**: 541 CATs vêm dos celetistas (empresas públicas e
  sociedade economia mista). Sub-estimado.

### 4.2 Trabalhadores informais

~40% da força nacional. PNAD-Contínua trimestre 4/2015 reportava
informalidade no ES de ~38%. **Nenhum dado de acidente para esses
trabalhadores existe** sistematicamente. Mencionar no §5.

### 4.3 Domésticas (9700)

CAT_2015 = 0 no AEAT-ES. Lei 8.213/91 obriga mas fiscalização é nula.
Estimativas RAIS-2015: ~114 mil domésticos no ES. Risco real provavelmente
não-zero. **Limitação severa.**

### 4.4 Discrepância MIP-ES TD-60 reconstruída vs L oficial IJSN — RESOLVIDA

Em uma célula de A o erro de transcrição do PDF chegava a 0.67 (mean |ΔA|
= 2.8e-3). **Resolvido** em 2026-05-08 com a integração direta do XLSX
oficial IJSN (`Matriz_Insumo-Produto_MIP_35x35.xlsx`) como fonte primária.
O pipeline agora lê A e L diretamente das Tabelas 11 e 12 do XLSX
(`xlsx_ijsn_oficial_tab11_tab12`); a L-csv processada e a Z-TD60
reconstruída ficam como fallbacks ordenados.

A diferença entre L_xlsx e L_csv é 4.99e-12 (precisão de ponto flutuante),
confirmando que o CSV anteriormente fornecido é faithful. A Z reconstruída
do TD-60 PDF, por outro lado, mantém-se inadequada como fonte primária.

---

## 5. Plano de fechamento (priorizado)

### Iteração imediata (concluída em 2026-05-08)

1. ✅ **Multiplicador de emprego** + taxa CAT/trabalhador (`ã_j`).
2. ✅ **Análise de sensibilidade Monte Carlo** sobre `a_j`.
3. ✅ **Tabela final** com a + ã + f + f̃ + U + m + quadrante.
4. ✅ **XLSX oficial IJSN** integrado como fonte primária de A e L.

### Próxima iteração (paper) — concluída em 2026-05-08

5. ✅ **Modelo fechado Type II** — `06_modelo_fechado.py`. Endogeniza
   famílias via Tabela 03 (DOMÉSTICOS) col 43 + matriz D (Tabela 10).
   Coluna de consumo: h_setor / Σ(VA). Linha de renda: VA_j/X_j (proxy).
   Raio espectral A_bar = 0,587 < 1 (convergente). Decomposição:
   42,1% direto, 21,2% indireto, 36,7% induzido.
6. ✅ **Campo de influência Φ_ij** — `07_campo_influencia.py`. Formulação
   ponderada: Φ = (a'L) ⊗ (L·1). Heatmap log10 + tabela top-30 pares.
   Achado: Saúde privada (8692) é a origem dominante (5 dos top-5 pares
   com i=8692). Perturbações em A[8692, j] têm o maior impacto agregado.
7. ✅ **Decomposição da pegada por componente de Y** — `08_decomposicao_demanda.py`.
   Componentes via Tabela 03 (DOMÉSTICOS), agregação produto→setor via D.
   Resultado:
   - Consumo das famílias       37,0%   (4.503 CATs)
   - Exportações p/ Brasil      30,0%   (3.649 CATs) ← interestadual
   - Exportações p/ exterior    13,8%   (1.674 CATs)
   - FBKF (investimento)        10,5%   (1.277 CATs)
   - Consumo do governo          7,1%     (863 CATs)
   - ISFLSF + var. estoque       1,6%     (191 CATs)
   **Insight de policy**: ~44% da pegada serve demanda de fora do ES
   (BR + exterior). Argumento para responsabilidade compartilhada
   (consumer responsibility) no desenho de FAP/RAT regional.

### Próxima iteração (extensão acadêmica)

8. **Validação cruzada SmartLab vs AEAT** para os top-10 setores.
9. **Refinar wages do Type II** com RAIS-2015 (substituir proxy VA/X).
10. **SDA temporal** com MIP-ES 2010 vs 2015 (decomposição estrutural).

### Extensão acadêmica (ANPEC/ENABER)

7. **Comparativo BR×ES** com MIP-CECEG 68 setores.
8. **SDA temporal** com MIP-ES 2010 (se disponível) vs 2015.
9. **Modelagem de subnotificação** com fatores setoriais conhecidos.

---

## 6. Referências consultadas

- IBGE/CES (Comitê de Estatísticas Sociais) — metadados AEAT
- SmartLab — Observatório SST (TST/MPT/OIT)
- Guilhoto & Sesso Filho (2010) — metodologia MIP regional
- Cardoso & Jiménez (2009) — subnotificação SST Brasil
- Chagas, Salim & Servo (2011, IPEA) — diagnóstico institucional SST
- Miller & Blair (2009) — Input-Output Analysis: foundations and extensions
- Dietzenbacher & Lahr (2013) — Hypothetical extraction methods
- IJSN/TD-60 — TRU e MIP do Espírito Santo, 2015
