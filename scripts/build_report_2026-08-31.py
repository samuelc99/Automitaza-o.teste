"""Gera o relatório TOP 5 da execução de 2026-08-31.

A seleção do TOP 5 e as narrativas (motivo_top5, melhor oportunidade, maior
risco, próximo passo) são julgamento crítico registrado aqui — não geradas
automaticamente pelo score (Seção 14: "Não escolha os produtos apenas pela
pontuação").
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poe.pipeline.run import run_pipeline
from poe.report.top5 import BestOpportunity, ReportEntry, render_report

result = run_pipeline("data/evidence_2026-08-31.json", db_path="data/history.db")
by_name = {sp.candidate.name: sp for sp in result.scored}

entries = [
    ReportEntry(
        scored=by_name["Bebedouro automático para gatos (fonte de água em movimento)"],
        motivo_top5=(
            "Maior score da rodada (37,4/100) e a evidência mais sólida entre os cinco: "
            "há um dado numérico de crescimento real de busca (+132% a/a, ainda que via fonte "
            "secundária) e o mercado pet brasileiro tem trajetória de crescimento confirmada "
            "(9,6% projetado para 2026). É o único candidato onde demanda E crescimento têm "
            "algum lastro em número, não só em 'está na lista de tendências'."
        ),
    ),
    ReportEntry(
        scored=by_name["Fone de ouvido com condução óssea (linha de entrada)"],
        motivo_top5=(
            "Entra no TOP 5 pela melhor margem estimada do grupo (~26%) e por ter um ângulo de "
            "marketing genuinamente diferenciado (segurança para corredores/ciclistas — não é "
            "'mais um fone bluetooth'). Mas a confiança é Baixa: só 1 fonte independente e "
            "nenhum dado de crescimento específico do nicho. Está aqui como aposta de margem, "
            "não como aposta de demanda comprovada."
        ),
    ),
    ReportEntry(
        scored=by_name["Mini liquidificador portátil USB (garrafa/coqueteleira elétrica)"],
        motivo_top5=(
            "Tem a demanda mais fácil de verificar (milhares de listagens ativas em 5+ "
            "varejistas) — mas essa mesma evidência é o motivo do score baixo: é prova de "
            "saturação, não de oportunidade. Entra no TOP 5 mais como 'categoria validada, "
            "produto sem diferenciação' do que como recomendação forte."
        ),
    ),
    ReportEntry(
        scored=by_name["Rolo/massageador facial Gua Sha (quartzo rosa ou jade)"],
        motivo_top5=(
            "Único candidato com prova de demanda vinda de um ranking de bestseller real "
            "(Amazon Brasil, categoria Rollers Faciais). Mas não há nenhuma evidência de "
            "crescimento recente — pode ser um produto maduro/estável, não uma tendência em "
            "alta — e a saturação de preço (R$15-259) é a mais extrema do grupo. Entra no TOP 5 "
            "mais por completude do que por convicção."
        ),
    ),
    ReportEntry(
        scored=by_name["Sérum facial vitamina C (linha nacional acessível)"],
        motivo_top5=(
            "Score zerado pelas penalidades (regulatório ANVISA + risco de devolução + marcas "
            "dominantes + margem apertada somados). Entra no TOP 5 apenas para documentar por "
            "que um produto que 'parece' óbvio (viral no TikTok, categoria em alta) na prática "
            "falha no crivo crítico quando a evidência de crescimento real não aparece e os "
            "riscos se empilham. É o exemplo didático de Seção 5/22 desta rodada."
        ),
    ),
]

best = BestOpportunity(
    nome="Bebedouro automático para gatos",
    motivo=(
        "É o único candidato desta rodada com evidência de crescimento numérica (mesmo que "
        "de fonte secundária) combinada com um mercado macro comprovadamente em expansão "
        "(pet, +9,6% em 2026) e sem saturação extrema — a faixa de preço entre os poucos "
        "concorrentes identificados é ampla (R$37,60-75,77+), sugerindo espaço para um produto "
        "mais silencioso ou com maior capacidade se diferenciar."
    ),
    pontos_fortes=[
        "Único dado de crescimento numérico da rodada (+132% busca a/a, fonte secundária)",
        "Mercado macro (pet) com crescimento projetado e verificável",
        "Baixo risco regulatório/de propriedade intelectual",
        "Alto potencial de demonstração em vídeo (apelo emocional real: saúde do animal)",
    ],
    pontos_fracos=[
        "Confiança geral ainda é Média, não Alta — só 3 fontes independentes",
        "Margem estimada apertada (~13%) nas premissas usadas — não é dado real de custo",
        "Nenhuma reclamação recorrente de consumidores foi levantada (dado insuficiente)",
        "Estatística de crescimento vem de fonte secundária citando Google Trends, não do gráfico original",
    ],
    informacoes_faltando=[
        "Custo real de aquisição do produto (fornecedor nacional ou importado)",
        "Número real de vendedores/anúncios ativos e volume de avaliações por anúncio",
        "Taxa de devolução real reportada por vendedores atuais",
        "Confirmação direta do dado de crescimento de busca no Google Trends",
    ],
    principal_risco=(
        "Margem apertada: se o custo real de aquisição for maior que a premissa de 30% usada "
        "aqui, o produto pode não ser viável mesmo com demanda validada."
    ),
    proximo_teste=(
        "Cotar custo real com 2-3 fornecedores (nacional e importado) e rodar um teste de "
        "anúncio de baixo orçamento (ex: R$300-500 em tráfego) para medir CPA real antes de "
        "comprar estoque — isso substitui a premissa de 15% de publicidade por um número real."
    ),
)

biggest_risk = (
    "Nenhum dos cinco candidatos tem confiança Alta — a maior é Média. Isso não é um problema "
    "do produto, é um limite da coleta de dados desta rodada: sem acesso a Mercado Livre/Amazon "
    "(bloqueados por robots.txt, ver README) e sem acesso ao Google Trends /explore (também "
    "bloqueado), a evidência de demanda e crescimento vem majoritariamente de artigos "
    "secundários, não de dados primários de vendas. Tratar qualquer um destes scores como "
    "'aprovado para investir estoque' seria repetir exatamente o erro que o Princípio "
    "Fundamental do projeto (Seção 3) pede para evitar."
)

next_step = (
    "Antes de comprar estoque de qualquer candidato: (1) registrar um app na API oficial de "
    "desenvolvedor do Mercado Livre (grátis, ver README) para obter contagem real de "
    "concorrentes, preço médio praticado e — nos itens que expõem esse campo — quantidade "
    "vendida; (2) para o Bebedouro Automático especificamente, cotar custo com fornecedores "
    "reais; (3) rodar esta mesma análise novamente em 2-4 semanas com os novos dados e comparar "
    "no histórico (`python -m poe.cli history`) se o score do bebedouro sobe, cai ou se mantém "
    "— isso é o teste real de tendência vs. pico passageiro (Seção 7)."
)

report_md = render_report(entries, best, biggest_risk, next_step)
out_path = Path("reports/top5_2026-08-31.md")
out_path.parent.mkdir(exist_ok=True)
out_path.write_text(report_md, encoding="utf-8")
print(f"Relatório salvo em {out_path} ({len(report_md)} chars)")
