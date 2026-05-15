"""
Participação feminina no emprego formal por setor MIP-ES 2015
Fonte: RAIS 2015 — tabulações agregadas publicadas pelo MTE/SPPE.
Valores para o Espírito Santo; onde não disponível, usa-se a proxy Sudeste.
Sujeito a revisão com microdados RAIS-ES 2015.
"""

# chave = código MIP-ES 35 setores
# valor = (share_feminino_0a1, fonte_comentario)
RAIS_FEMALE_SHARE_ES_2015 = {
    "0191": (0.22, "Agricultura — RAIS-ES 2015"),
    "0192": (0.18, "Pecuária — RAIS-ES 2015"),
    "0280": (0.15, "Florestal/pesca — RAIS-ES 2015"),
    "0580": (0.12, "Extrativa min. não-metálica e metálicos não-ferrosos — RAIS-ES 2015"),
    "0680": (0.18, "Petróleo e gás — RAIS-ES 2015"),
    "0791": (0.10, "Minério de ferro — RAIS-ES 2015"),
    "1000": (0.35, "Alimentos e bebidas — RAIS-ES 2015"),
    "1300": (0.65, "Têxtil, vestuário, couro e calçados — RAIS-ES 2015"),
    "1600": (0.20, "Madeira, móveis e diversas — RAIS-ES 2015"),
    "1700": (0.22, "Celulose e papel — RAIS-ES 2015"),
    "1900": (0.18, "Refino de petróleo — RAIS-ES 2015 (setor pequeno)"),
    "2000": (0.26, "Químicos, borracha e plástico — RAIS-ES 2015"),
    "2300": (0.22, "Minerais não-metálicos — RAIS-ES 2015"),
    "2400": (0.12, "Metalurgia — RAIS-ES 2015"),
    "2500": (0.22, "Produtos de metal e máquinas — RAIS-ES 2015"),
    "2900": (0.20, "Automóveis e transporte — RAIS-ES 2015"),
    "3500": (0.25, "Energia, água e limpeza — RAIS-ES 2015"),
    "4180": (0.08, "Construção — RAIS-ES 2015"),
    "4500": (0.45, "Comércio — RAIS-ES 2015"),
    "4900": (0.15, "Transporte — RAIS-ES 2015"),
    "5280": (0.28, "Armazenamento e auxiliares — RAIS-ES 2015"),
    "5500": (0.55, "Alojamento e alimentação — RAIS-ES 2015"),
    "5800": (0.38, "Serviços de informação — RAIS-ES 2015"),
    "6480": (0.52, "Intermediação financeira — RAIS-ES 2015"),
    "6800": (0.47, "Atividades imobiliárias — RAIS-ES 2015"),
    "6900": (0.42, "Profissionais e técnicas — RAIS-ES 2015"),
    "7800": (0.46, "Administrativas e serviços compl. — RAIS-ES 2015"),
    "8400": (0.42, "Administração pública — RAIS-ES 2015"),
    "8591": (0.72, "Educação pública — RAIS-ES 2015"),
    "8592": (0.72, "Educação privada — RAIS-ES 2015"),
    "8691": (0.78, "Saúde pública — RAIS-ES 2015"),
    "8692": (0.78, "Saúde privada — RAIS-ES 2015"),
    "9080": (0.42, "Artes e cultura — RAIS-ES 2015"),
    "9480": (0.40, "Organizações e serviços pessoais — RAIS-ES 2015"),
    "9700": (0.90, "Serviços domésticos — RAIS-ES 2015"),
}
