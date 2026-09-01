# Product Opportunity Engine

Sistema de descoberta e pontuação de oportunidades de produto para e-commerce
(preço final ao consumidor ≤ R$150), construído para reduzir decisões por
achismo: toda conclusão é rastreável até uma evidência rotulada como DADO,
ESTIMATIVA, INFERÊNCIA ou HIPÓTESE.

Este projeto é o Módulo 1 (Opportunity Engine) de uma visão maior — ver
**[BLUEPRINT.md](BLUEPRINT.md)** para a arquitetura completa do Affiliate
Commerce Engine e o roteiro de evolução (Fases A-K).

## Status estratégico atual (2026-09-01)

**Roadmap técnico pausado de propósito** após a Fase B.5 (Affiliate Market
Discovery, pesquisa ad-hoc, não virou módulo de código). Achado: a melhor
oportunidade de afiliado para promoção via TikTok é o **TikTok Shop
Affiliate/Creator Program** (nativo da plataforma, comissão 8-15%, podendo
passar disso em produtos que o vendedor quer empurrar — bem melhor que os
R$3,88-6,83/venda que a Amazon Associates dá nos candidatos atuais). Mas
esse programa exige **1.000+ seguidores no TikTok e histórico de postagem
nos últimos 180 dias** — não é uma barreira de código, é construção real de
audiência (semanas/meses).

Decisão: pausar a implementação de novas fases (Historical Intelligence,
Offer Engine, etc.) até que exista uma conta TikTok elegível. Retomar o
roadmap técnico quando esse pré-requisito for resolvido — ver BLUEPRINT.md
para a sequência completa (Fase C em diante).

Enquanto isso, Amazon Associates (integrado, `data/affiliate_2026-09-01.json`)
e Magalu Parceiros/Lomadee (pesquisados, ainda não integrados — política de
tráfego pago deles não foi confirmada publicamente) seguem como alternativas
de comissão mais baixa mas sem essa barreira.

## Módulo 2 — Affiliate Economics Engine

Responde "se eu gerar uma venda desse produto, quanto ganho de comissão?"
(ver BLUEPRINT.md, Seção 8). Pacote `src/poe/affiliate/`:

- `models.py` — `TrackedValue` (número + status CONFIRMADO/ESTIMADO/DESCONHECIDO,
  nunca um valor sem procedência), `CommissionInfo`, `CommissionEstimate`
- `network.py` — `AffiliateNetwork`, adaptador abstrato (Seção 47) — hoje só
  existe implementação manual, pelo mesmo motivo do Opportunity Engine:
  nenhum programa de afiliado testado (Amazon Associates, AliExpress
  Affiliate, Shopee Affiliate) dá acesso programático sem aprovação prévia
  com histórico de vendas/tráfego
- `manual_source.py` — `AffiliateInfoFileCollector`, carrega comissões de um
  JSON pesquisado via WebSearch em tabelas **públicas** de comissão (essas
  tabelas, ao contrário do acesso à API, geralmente são públicas)
- `economics.py` — calcula comissão bruta e líquida, propagando o status
  mais fraco entre os campos usados (se um custo é desconhecido, o líquido
  também fica desconhecido, nunca vira um valor inventado)

Uso:

```bash
python -m poe.cli affiliate data/evidence_2026-08-31.json data/affiliate_2026-09-01.json
```

**Achado real da primeira rodada (2026-09-01, dados confirmados na tabela
oficial de comissões do Amazon Associates Brasil):** comissão bruta de
R$3,88 a R$6,83 por venda nos 5 candidatos com oferta encontrada (8-13% dos
preços de R$47-82). Isso é criticamente apertado para sustentar qualquer
CAC de tráfego pago — a Seção 3 do Blueprint pergunta exatamente isso
("qual oportunidade gera comissão lucrativa através de tráfego que
conseguimos adquirir?"), e a resposta preliminar é que o modelo de afiliado
puro nesses produtos específicos pode não fechar a conta, mesmo que o
Opportunity Engine os pontue bem para revenda direta. Vale investigar
programas com comissão fixa mais alta ou categorias com % maior antes de
escolher uma oportunidade para testar tráfego real.

## Por que não há um scraper automático

Antes de escrever código, testamos conectividade e política de robôs dos
marketplaces óbvios (Mercado Livre, Amazon.com.br, AliExpress, Shopee, Google
Trends). Resultado:

- **Mercado Livre** (site e domínio de API `api.mercadolibre.com`): o
  `robots.txt` do site nomeia `ClaudeBot`/`Claude-User` com `Disallow: /`
  explícito; o domínio da API bloqueia todos os agentes (`Disallow: /` geral)
  e retorna 403 mesmo em requisição direta.
- **Amazon.com.br**: `robots.txt` bloqueia explicitamente `ClaudeBot`,
  `Claude-User`, `Claude-SearchBot` e `Claude-Web`.
- **AliExpress**: `/search/*`, `/product/*` e `/productdetail/*` bloqueados
  para todos os agentes (não é específico de IA) — inviabiliza descoberta de
  produto por lá de qualquer forma.
- **Google Trends**: `/explore` (o endpoint de curva de interesse por
  palavra-chave, base do `pytrends`) está bloqueado no `robots.txt` para
  todos os agentes.
- **Shopee.com.br**: `robots.txt` não bloqueia, mas a página de busca é um
  SPA (Next.js) sem dados no HTML estático — preço/vendas só chegam via
  JS/XHR depois do carregamento.

Conclusão: um pipeline autônomo batendo direto nesses sites violaria
diretivas explícitas de robots.txt (Mercado Livre e Amazon citam "Claude"
literalmente) ou simplesmente não funciona tecnicamente. Por isso a coleta de
evidência real neste MVP é feita **pelo agente**, via WebSearch/WebFetch em
sessão interativa (respeitando robots.txt por página), e salva em JSON
estruturado — não por um script rodando sozinho.

**Atualização (integração oficial implementada):** a API oficial de
desenvolvedor do Mercado Livre está integrada — ver "Fonte oficial: Mercado
Livre Trends" abaixo. O que ela consegue trazer é mais restrito do que se
imaginava inicialmente: a documentação atual (verificada em 2026-08-31,
direto na fonte) só lista busca por `seller_id`/`nickname`, não busca livre
por palavra-chave — então preço/concorrência via API continuam fora de
alcance por enquanto (ver Limitações).

## Arquitetura

```
EvidenceSource(s)                    EvidenceEnricher(s) [opcional]
(cria candidatos com preço)          (anexa evidência a candidatos existentes)
EvidenceFileCollector                MercadoLivreTrendsSource
(JSON via WebSearch manual)          (API oficial /trends, precisa de credencial)
        │                                    │
        └──────────────┬─────────────────────┘
                        ▼
normalize.dedupe /          → remove duplicatas, corrige inconsistências
flag_inconsistencies         (src/poe/pipeline/normalize.py)
        │
        ▼
filter.apply_hard_filters   → elimina preço > R$150 e hard_flags
        │                      (src/poe/pipeline/filter.py)
        ▼
scoring.compute_score       → pontua 7 dimensões (0-100), configurável
        │                      (src/poe/scoring/score.py, config.yaml)
        ▼
scoring.apply_penalties     → subtrai penalidades (mercado saturado, etc.)
        │                      (src/poe/scoring/penalties.py)
        ▼
scoring.compute_confidence  → Alta/Média/Baixa baseado na QUALIDADE da
        │                      evidência, não no score (src/poe/scoring/confidence.py)
        ▼
audit.audit_candidate       → checagens mecânicas de sinal de alerta
        │                      (src/poe/audit/auditor.py)
        ▼
storage.HistoryStore        → salva no SQLite (agora inclui evidências
        │                      individuais, não só o score — src/poe/storage/db.py)
        ▼
report.top5.render_report   → Markdown no formato do briefing (curado por
                               quem revisa — não é 100% automático de propósito)
```

`EvidenceSource` (`src/poe/collectors/base.py`) cria candidatos do zero — só
faz sentido para fontes que têm preço/identidade de produto (hoje:
`EvidenceFileCollector`). `EvidenceEnricher` anexa evidência a candidatos que
já existem — para fontes que só têm sinal de popularidade/tendência para uma
palavra-chave, sem preço (hoje: `MercadoLivreTrendsSource`). Nenhuma das duas
sabe nada sobre scoring/ranking/auditoria/histórico — adicionar uma fonte
nova não toca nessas camadas.

Cada etapa é testável isoladamente (`tests/`), com mocks para tudo que fala
com rede — nenhum teste bate na API real do Mercado Livre.

## Como rodar

```bash
pip install -e .
python -m poe.cli run data/evidence_2026-08-31.json
python -m poe.cli history
pytest
```

### Fonte oficial: Mercado Livre Trends (opcional)

Modo híbrido: complementa as evidências manuais com o endpoint oficial
`/trends` (API de Desenvolvedor do Mercado Livre) — os termos de busca com
maior crescimento/mais buscados/mais populares da semana, casados por nome
com os candidatos já carregados do JSON.

```bash
cp .env.example .env   # preencha MELI_CLIENT_ID / MELI_CLIENT_SECRET / MELI_REFRESH_TOKEN
python -m poe.cli run data/evidence_2026-08-31.json --meli-trends
```

Sem as credenciais no ambiente, a flag `--meli-trends` não quebra nada: o
sistema loga um aviso e roda em modo manual normalmente (ver
`build_meli_trends_source_from_env` em `src/poe/collectors/mercadolivre.py`).
Passo a passo para gerar as credenciais está em `.env.example`.

**O que este endpoint realmente dá:** até 50 termos de busca em alta por
site/categoria, atualizados semanalmente — sinal real de demanda/crescimento
para uma *palavra-chave*, não um produto com preço. Por isso ele é um
`EvidenceEnricher`, não uma fonte que cria produtos novos.

## Como adicionar evidências

Preencha um JSON seguindo `data/evidence_template.json`. Regras:

- Todo `claim` numérico ou factual precisa de `type` e, se for `DADO`, de
  `source_url`.
- `strength` (0.0-1.0) é o julgamento explícito de quem coletou a evidência
  sobre o quão fortemente ela sustenta a dimensão — não é calculado por NLP,
  é uma decisão transparente e auditável (documente o porquê em `note`).
- `risk_flags[].name` precisa corresponder a uma chave em `config.yaml ->
  penalties`, senão o pipeline avisa e ignora (evita erro de digitação
  silencioso).

## Limitações conhecidas (honestas, não contornadas)

- **Sem preço/concorrência via API**: a busca livre por palavra-chave
  (`/sites/$SITE_ID/search?q=...`) não está mais documentada para uso geral
  pela ML — só busca por `seller_id`/`nickname` (catálogo de um vendedor já
  conhecido). Então hoje não há como obter preço médio praticado ou contagem
  de concorrentes via API oficial sem já saber o `seller_id` de alguém.
- **`/trends` não identifica produto, só palavra-chave** — o casamento
  produto↔termo em tendência é por substring normalizada (heurística, ver
  `match_keyword` em `collectors/base.py`), pode gerar falso positivo em
  termos genéricos.
- **`sold_quantity` não aparece na documentação pública atual** — não dá
  para obter quantidade vendida de um item via API pública hoje.
- Comparação de tendência real (T0→T1→T2) precisa de várias execuções ao
  longo do tempo — a estrutura para isso existe (`evidences` table,
  `HistoryStore.evidence_history_for`), mas a lógica de detecção de tendência
  em si não foi implementada (Seção 7 do briefing pediu explicitamente para
  não implementar isso ainda).
- **`GET /trends/MLB` retorna 403 ("At least one policy returned
  UNAUTHORIZED") mesmo com autenticação válida e o escopo
  `urn:ml:mktp:metrics:/read-only` concedido.** Validado em produção com
  credenciais reais em 2026-08-31, seguindo o checklist oficial de
  troubleshooting de erro 403 (`developers.mercadolivre.com.br/pt_br/erro-403`)
  ponto a ponto, via chamadas reais e documentadas:
  - `GET /users/{user_id}?attributes=status` → `site_status: active`,
    `required_action: null`, sem código de bloqueio em `sell`/`buy`/`list`.
  - `GET /applications/{app_id}` → `active: true`, `blocked: false`,
    `disabled: false`, scope `urn:ml:mktp:metrics:/read-only` presente.
  - IP allowlist: não aplicável (gerenciamento de IP é exclusivo para
    integradores whitelisteados, opção nem aparece pra este app).

  O único campo fora do padrão: **`certification_status: "not_certified"`**.
  Hipótese mais provável (não confirmada pela ML ainda): `/trends` exige
  aplicação certificada — um processo de revisão manual da equipe ML,
  separado de habilitar escopo no DevCenter. Chamado de suporte aberto com
  esse diagnóstico completo; resposta pendente.
- **Toda API oficial de "produtos em alta" das grandes plataformas exige
  tráfego/vendas prévios, não é acessível para pesquisa de mercado a frio**:
  investigado em 2026-08-31 —
  AliExpress Affiliate API (Hot Products) exige presença online ativa com
  tráfego + aprovação manual, e o catálogo "Hot Products" em si exige um
  tier extra ("Advanced API"); Shopee Affiliate Open Platform exige conta de
  afiliado já ativa com histórico de performance; Amazon PA-API exige mínimo
  de 3 vendas validadas como associado. TikTok Shop Open API exige conta de
  vendedor aprovada (CNPJ, dados bancários, `shop_id`); TikTok Creative
  Center (`ads.tiktok.com`) não bloqueia por `robots.txt`, mas é uma SPA
  100% client-side sem dado nenhum acessível via fetch direto (mesmo
  problema da Shopee). Essa é uma barreira estrutural de negócio, não
  técnica — só é contornável construindo antes uma audiência/histórico de
  vendas próprio, o que muda a natureza do projeto.

## Próximos passos naturais (não implementados ainda)

- Agentes especializados (Discovery/Trend/Competition/Margin/Marketing/Risk/
  Ranking/Auditor) como esboçado na Seção 21 do briefing — hoje o "agente"
  é o Claude fazendo essas funções em sessão, com o pipeline Python cuidando
  da parte determinística.
- `EvidenceSource` de catálogo de vendedor específico (`/sites/$SITE_ID/search?seller_id=`)
  — dá preço real e é documentado, mas exige já conhecer o `seller_id` de um
  concorrente/fornecedor (não serve para descoberta aberta de produto).
- Lógica de detecção de tendência sobre o histórico de evidências já
  persistido (ver Limitações acima).
- Dashboard (hoje o output é Markdown).
