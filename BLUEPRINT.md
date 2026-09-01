# BLUEPRINT MASTER — AFFILIATE COMMERCE ENGINE

## 0. STATUS DO DOCUMENTO

Este documento define a visão, arquitetura, princípios, módulos e estratégia de evolução do Affiliate Commerce Engine.

Ele deve ser tratado como o documento estratégico principal do projeto.

Antes de criar uma nova funcionalidade, refatorar uma arquitetura existente ou adicionar um novo agente, consulte este Blueprint.

O objetivo não é implementar tudo imediatamente.

O objetivo é garantir que cada implementação aproxime o sistema da arquitetura final sem criar dívida estrutural desnecessária.

---

# 1. VISÃO DO PRODUTO

O Affiliate Commerce Engine é um sistema de inteligência e automação para construir operações de marketing de afiliados orientadas por dados.

O sistema deve ser capaz de:

1. descobrir oportunidades de produtos;
2. analisar demanda;
3. analisar tendências;
4. identificar programas de afiliados;
5. analisar comissões;
6. avaliar potencial comercial;
7. selecionar oportunidades;
8. criar uma oferta;
9. criar páginas de apresentação;
10. criar copy;
11. criar criativos;
12. criar campanhas;
13. direcionar tráfego;
14. medir comportamento;
15. medir vendas e comissões;
16. identificar o que funciona;
17. interromper o que não funciona;
18. escalar o que funciona;
19. aprender com os resultados;
20. utilizar esse aprendizado para encontrar oportunidades melhores.

O sistema não possui como objetivo manter estoque.

Não deve comprar produtos para revenda.

Não deve assumir logística do produto.

Não deve processar pedidos do consumidor.

A venda deve ocorrer através do vendedor, marketplace ou plataforma afiliada.

A receita do sistema vem principalmente de:

# COMISSÕES DE AFILIADO

---

# 2. MODELO DE NEGÓCIO

O modelo fundamental é:

```text
PRODUTO
   ↓
PROGRAMA DE AFILIADOS
   ↓
LINK / TRACKING
   ↓
TRÁFEGO
   ↓
CONSUMIDOR
   ↓
VENDA
   ↓
COMISSÃO
```

O sistema deve otimizar para:

# COMISSÃO LÍQUIDA GERADA PELO TRÁFEGO

Não otimizar apenas para:

* cliques;
* impressões;
* seguidores;
* visualizações;
* CTR;
* produtos populares.

Essas métricas são intermediárias.

O objetivo final é resultado econômico sustentável.

---

# 3. PRINCÍPIO FUNDAMENTAL

O sistema não deve perguntar apenas:

> "Qual produto está vendendo?"

Deve perguntar:

> "Qual oportunidade possui maior probabilidade de gerar comissão lucrativa através de tráfego que conseguimos adquirir?"

Essa diferença deve orientar toda a arquitetura.

---

# 4. RESTRIÇÃO DE PREÇO

O preço de venda ao consumidor deve ser:

# ≤ R$150

Esse é um requisito fundamental do projeto.

Produtos acima desse valor devem ser filtrados ou explicitamente marcados como incompatíveis.

Como preferência, produtos entre aproximadamente:

# R$30 — R$120

podem receber prioridade, mas isso não é uma regra absoluta.

---

# 5. O QUE É UMA OPORTUNIDADE

Uma oportunidade não é simplesmente um produto.

Uma oportunidade é a combinação:

```text
PRODUTO
+
DEMANDA
+
TENDÊNCIA
+
PROGRAMA DE AFILIADOS
+
COMISSÃO
+
PÚBLICO
+
OFERTA
+
CRIATIVO
+
CANAL
+
TRÁFEGO
+
CONVERSÃO
=
OPORTUNIDADE
```

Portanto, o sistema deve eventualmente avaliar o conjunto e não apenas o produto isolado.

---

# 6. ARQUITETURA MACRO

A arquitetura conceitual deve evoluir para:

```text
                    ┌──────────────────────┐
                    │    DATA SOURCES      │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ OPPORTUNITY ENGINE   │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ AFFILIATE ECONOMICS  │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ OPPORTUNITY RANKING  │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │   OFFER ENGINE       │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │   PAGE ENGINE        │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │  CREATIVE ENGINE     │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │   TRAFFIC ENGINE     │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ ANALYTICS ENGINE     │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ LEARNING ENGINE      │
                    └──────────┬───────────┘
                               │
                               └───────────────┐
                                               ↓
                                      OPPORTUNITY ENGINE
```

O sistema deve funcionar como um ciclo fechado.

---

# 7. MÓDULO 1 — OPPORTUNITY ENGINE

Este módulo já existe parcialmente.

Responsabilidades:

* descoberta de produtos;
* coleta de evidências;
* normalização;
* filtro de preço;
* scoring;
* penalizações;
* confiança;
* auditoria;
* histórico.

Estado atual:

* MVP funcional;
* 45 testes passando;
* histórico persistido;
* pesquisa via WebSearch;
* integração oficial Mercado Livre implementada, porém bloqueada externamente;
* automação semanal funcionando.

NÃO reescrever esse módulo sem necessidade.

Ele é a fundação do sistema.

---

# 8. MÓDULO 2 — AFFILIATE ECONOMICS ENGINE

Este módulo deve responder:

> "Se eu gerar uma venda desse produto, quanto ganho?"

Deve analisar, quando disponível:

* preço;
* comissão percentual;
* comissão fixa;
* comissão estimada;
* duração do cookie;
* regras de atribuição;
* EPC;
* conversão;
* taxas;
* restrições de tráfego;
* categorias elegíveis;
* cancelamentos;
* devoluções;
* payout.

Calcular:

```text
Comissão Bruta
-
Custos diretamente associados
=
Comissão Líquida
```

Quando dados estiverem ausentes:

NÃO inventar.

Classificar como:

* confirmado;
* estimado;
* desconhecido.

---

# 9. MÓDULO 3 — OPPORTUNITY RANKING

O ranking deve combinar:

### Produto

* demanda;
* crescimento;
* concorrência;
* preço;
* risco.

### Afiliado

* comissão;
* conversão;
* EPC;
* confiabilidade do programa.

### Marketing

* potencial de anúncio;
* potencial de vídeo;
* potencial de compra por impulso;
* facilidade de demonstrar;
* facilidade de criar oferta.

### Econômico

* comissão por venda;
* CAC máximo estimado;
* margem potencial;
* potencial de escala.

O score inicial existente não deve ser destruído.

A nova camada deve evoluir gradualmente.

---

# 10. MÓDULO 4 — OFFER ENGINE

Depois que uma oportunidade for selecionada, o sistema deve construir a estratégia da oferta.

Definir:

* público;
* problema;
* desejo;
* benefício principal;
* diferencial;
* argumento central;
* mecanismo;
* objeções;
* prova;
* CTA;
* ângulo de comunicação.

O sistema deve criar múltiplas hipóteses de oferta.

Exemplo:

```text
Produto X

Ângulo 1 → economia de tempo
Ângulo 2 → conforto
Ângulo 3 → problema/solução
Ângulo 4 → curiosidade
Ângulo 5 → transformação
```

Não assumir antecipadamente qual ângulo será vencedor.

---

# 11. MÓDULO 5 — PAGE ENGINE

O sistema deve poder gerar páginas de destino.

A página pode ser:

* landing page;
* página de pré-venda;
* advertorial;
* review;
* comparativo;
* página simples de oferta.

A página deve possuir:

```text
HOOK
↓
PROBLEMA
↓
SOLUÇÃO
↓
DEMONSTRAÇÃO
↓
BENEFÍCIOS
↓
PROVA
↓
OBJEÇÕES
↓
CTA
```

O CTA deve direcionar para o link de afiliado quando permitido pelas regras do programa.

Não criar falsas alegações.

Não criar depoimentos falsos.

Não fabricar avaliações.

---

# 12. MÓDULO 6 — CREATIVE ENGINE

Responsável pela produção e experimentação de criativos.

Tipos:

* UGC;
* demonstração;
* problema/solução;
* antes/depois, quando legítimo;
* tutorial;
* comparação;
* storytelling;
* oferta;
* curiosidade;
* prova social real.

Cada criativo deve possuir metadados:

* produto;
* oferta;
* público;
* ângulo;
* hook;
* formato;
* canal;
* versão.

Exemplo:

```text
Produto: X
Ângulo: Problema/Solução
Hook: H03
Criativo: C07
Versão: 2
```

Isso permitirá descobrir posteriormente quais características geram melhores resultados.

---

# 13. MÓDULO 7 — TRAFFIC ENGINE

Responsável por planejar e executar experimentos de aquisição de tráfego.

O sistema deve ser capaz de trabalhar com canais como:

* Meta Ads;
* TikTok Ads;
* Google Ads;
* outras plataformas compatíveis.

Sempre respeitando:

* políticas da plataforma;
* regras do programa de afiliados;
* legislação aplicável;
* limites de orçamento.

---

# 14. EXPERIMENTAÇÃO DE TRÁFEGO

O sistema não deve simplesmente colocar todo o orçamento em um único anúncio.

Deve experimentar.

Exemplo:

```text
Produto X

Criativo A → R$20
Criativo B → R$20
Criativo C → R$20
Criativo D → R$20
```

Depois analisar:

* CPM;
* CTR;
* CPC;
* LPV;
* ATC, quando disponível;
* conversão;
* CPA;
* comissão;
* ROAS;
* lucro.

Identificar vencedores e perdedores.

---

# 15. CONTROLE DE ORÇAMENTO

NUNCA permitir gasto ilimitado.

O sistema deve trabalhar com:

* orçamento diário;
* orçamento máximo por experimento;
* limite por campanha;
* limite por produto;
* limite de perda;
* regra de pausa;
* regra de escala.

Inicialmente:

# TODA AÇÃO QUE GASTE DINHEIRO DEVE EXIGIR APROVAÇÃO HUMANA.

Somente depois de validação suficiente devem ser consideradas automações financeiras limitadas.

---

# 16. MÓDULO 8 — ANALYTICS ENGINE

Registrar o funil:

```text
IMPRESSÕES
↓
CLIQUES
↓
VISITAS
↓
CLIQUES NO LINK AFILIADO
↓
VENDAS
↓
COMISSÕES
```

Quando os dados estiverem disponíveis.

Calcular:

* CTR;
* CPC;
* CVR;
* CPA;
* EPC;
* comissão por clique;
* comissão por venda;
* lucro estimado;
* ROI;
* ROAS.

Diferenciar:

### Métrica observada

Dado real.

### Métrica estimada

Estimativa.

### Métrica atribuída

Resultado associado por tracking.

---

# 17. MÓDULO 9 — ATTRIBUTION

A atribuição deve ser tratada como componente fundamental.

Sempre que tecnicamente e legalmente possível, registrar:

* campanha;
* conjunto;
* anúncio;
* criativo;
* landing page;
* link;
* produto;
* timestamp;
* conversão;
* comissão.

Objetivo:

descobrir exatamente:

> "Qual produto + criativo + público + canal gerou a comissão?"

Sem atribuição, o sistema não consegue aprender adequadamente.

---

# 18. MÓDULO 10 — LEARNING ENGINE

Este será um dos módulos mais importantes do sistema.

Ele deve comparar:

### PREVISÃO

O que o sistema esperava.

versus

### REALIDADE

O que aconteceu.

Exemplo:

```text
Previsão:
Produto X = oportunidade excelente

Resultado:
CAC alto
Conversão baixa
Comissão insuficiente

Conclusão:
hipótese rejeitada
```

O resultado deve alimentar futuras decisões.

---

# 19. OPPORTUNITY DNA

Com histórico suficiente, identificar padrões.

Perguntas:

* Que preços aparecem nos vencedores?
* Que categorias aparecem?
* Qual nível de comissão?
* Que tipos de criativo funcionam?
* Quais públicos convertem?
* Quais ângulos funcionam?
* Quais canais funcionam?
* Quais características aparecem nos perdedores?

O sistema deve tentar descobrir:

# O DNA DAS OPORTUNIDADES VENCEDORAS

---

# 20. FEEDBACK LOOP

A arquitetura deve formar:

```text
DISCOVERY
↓
SELECTION
↓
OFFER
↓
CREATIVE
↓
TRAFFIC
↓
SALE
↓
COMMISSION
↓
ANALYSIS
↓
LEARNING
↓
DISCOVERY
```

Esse ciclo é o coração do produto.

---

# 21. AGENTES CLAUDE

O sistema pode utilizar agentes especializados.

Arquitetura conceitual:

### Discovery Agent

Encontra oportunidades.

### Market Research Agent

Pesquisa mercado.

### Affiliate Agent

Pesquisa programas e comissões.

### Economics Agent

Analisa viabilidade econômica.

### Offer Agent

Cria ofertas.

### Copy Agent

Produz copy.

### Creative Director Agent

Define conceitos criativos.

### Design Agent

Cria páginas e interfaces.

### Traffic Strategist Agent

Planeja aquisição.

### Media Buyer Agent

Analisa campanhas e recomenda ações.

### Analytics Agent

Interpreta resultados.

### Auditor Agent

Questiona conclusões.

### Orchestrator Agent

Coordena os demais.

---

# 22. ORCHESTRATOR

O Orchestrator deve ser o cérebro de coordenação.

Ele não deve necessariamente executar tudo.

Deve:

1. receber objetivo;
2. dividir problema;
3. chamar agentes especializados;
4. comparar respostas;
5. verificar evidências;
6. identificar conflitos;
7. solicitar auditoria;
8. produzir decisão;
9. solicitar aprovação quando necessário;
10. executar ações autorizadas;
11. registrar resultado.

---

# 23. HIERARQUIA DE AUTONOMIA

O sistema deve possuir níveis.

## Nível 0 — Assistente

Claude apenas recomenda.

## Nível 1 — Executor supervisionado

Claude executa tarefas não financeiras após aprovação.

## Nível 2 — Automação limitada

Claude pode executar ações previamente autorizadas dentro de limites.

## Nível 3 — Autonomia controlada

Claude pode tomar decisões operacionais de baixo risco.

## Nível 4 — Autonomia avançada

Somente considerar depois de dados e histórico suficientes.

A autonomia nunca deve significar:

> "Pode gastar dinheiro sem limites."

---

# 24. HUMAN-IN-THE-LOOP

Inicialmente, o usuário deve aprovar:

* escolha final do produto;
* entrada em programa de afiliados quando necessário;
* publicação de campanhas;
* orçamento;
* aumento significativo de orçamento;
* mudanças importantes de estratégia.

O sistema pode automatizar:

* análise;
* pesquisa;
* geração de conteúdo;
* geração de relatórios;
* comparação;
* testes não financeiros;
* organização de dados.

---

# 25. INTEGRIDADE DOS DADOS

REGRA ABSOLUTA:

# NÃO INVENTAR DADOS.

Nunca inventar:

* vendas;
* comissão;
* CTR;
* conversão;
* tendências;
* avaliações;
* preço;
* margem;
* EPC;
* lucro;
* resultados de campanha.

Quando um dado não existir:

# "DADO NÃO DISPONÍVEL"

Quando houver estimativa:

# "ESTIMATIVA"

Quando houver interpretação:

# "INFERÊNCIA"

---

# 26. FONTES E COMPLIANCE

Sempre preferir:

1. APIs oficiais;
2. integrações oficiais;
3. fontes públicas permitidas;
4. ferramentas de pesquisa autorizadas.

Não:

* contornar robots.txt;
* burlar autenticação;
* explorar endpoints privados;
* contornar bloqueios;
* quebrar CAPTCHAs;
* falsificar identidade;
* utilizar credenciais de terceiros;
* coletar dados de maneira proibida.

Quando uma fonte estiver bloqueada:

documentar a limitação e procurar alternativa legítima.

---

# 27. COMPLIANCE DE AFILIADOS

Antes de utilizar um programa:

verificar:

* regras de tráfego;
* restrições de anúncios;
* uso de marca;
* palavras-chave proibidas;
* redirecionamentos;
* cloaking;
* incentivos;
* disclosure de afiliado;
* regras de conteúdo.

O sistema nunca deve recomendar uma estratégia que viole explicitamente as regras do programa.

---

# 28. MARKETING É EXPERIMENTAÇÃO

O sistema não deve assumir que sabe antecipadamente o que vai funcionar.

Tudo deve ser tratado como hipótese:

```text
Hipótese
↓
Criativo
↓
Teste
↓
Resultado
↓
Aprendizado
```

Exemplo:

> "Acreditamos que o ângulo de economia de tempo converterá melhor."

Isso é uma hipótese.

Depois do teste:

> "Dados indicam que o ângulo de economia de tempo teve desempenho superior."

Agora existe evidência.

---

# 29. NÃO CONFUNDIR POPULARIDADE COM OPORTUNIDADE

Um produto muito popular pode ser uma oportunidade ruim.

Razões:

* concorrência;
* CPC elevado;
* baixa comissão;
* saturação;
* grandes marcas;
* dificuldade de diferenciação.

Um produto menor pode ser melhor se apresentar:

* crescimento;
* comissão alta;
* baixo custo de aquisição;
* excelente conversão;
* baixa saturação.

---

# 30. ECONOMIA UNITÁRIA

Para cada oportunidade, quando possível, calcular:

```text
Comissão por venda
-
CAC
=
Resultado por venda
```

E:

```text
Comissão total
-
Gasto com tráfego
=
Resultado da operação
```

A principal métrica econômica deve ser:

# LUCRO / COMISSÃO LÍQUIDA

Não simplesmente faturamento.

---

# 31. ESCALA

Um produto só deve ser considerado escalável quando houver evidência de:

* demanda;
* conversão;
* comissão suficiente;
* CAC sustentável;
* criativo vencedor;
* público identificável;
* disponibilidade do produto/programa;
* capacidade de continuar recebendo comissão.

Não escalar simplesmente porque uma campanha teve um bom dia.

---

# 32. DISCOVERY CONTÍNUO

Mesmo quando existir um produto vencedor, o sistema deve continuar procurando alternativas.

Nunca depender de um único produto.

Estratégia:

```text
WINNER
+
NEW CANDIDATES
+
EXPERIMENTS
=
PORTFÓLIO
```

Isso reduz dependência.

---

# 33. PORTFÓLIO DE OPORTUNIDADES

No futuro, o sistema poderá classificar:

### EXPERIMENTAL

Ainda sem evidência suficiente.

### PROMISING

Sinais iniciais positivos.

### VALIDATED

Resultados reais positivos.

### WINNER

Resultado consistente.

### SCALING

Pode receber mais orçamento.

### DECLINING

Está perdendo performance.

### DEAD

Não apresentou viabilidade.

Isso permite administrar múltiplas oportunidades simultaneamente.

---

# 34. HISTÓRICO

Tudo relevante deve possuir histórico.

Registrar:

* produtos;
* fontes;
* evidências;
* scores;
* decisões;
* campanhas;
* criativos;
* públicos;
* resultados;
* comissões;
* hipóteses;
* conclusões.

O histórico não é apenas armazenamento.

É matéria-prima para inteligência.

---

# 35. ARQUITETURA TÉCNICA

A arquitetura deve permanecer modular.

O projeto atual possui:

```text
src/poe/
```

Não destruir a estrutura existente.

Novos módulos podem seguir organização equivalente:

```text
src/
  opportunity/
  affiliate/
  economics/
  offer/
  page/
  creative/
  traffic/
  analytics/
  attribution/
  learning/
  agents/
  orchestration/
  storage/
```

A estrutura exata deve ser decidida após inspeção do código existente.

Não criar abstrações desnecessárias antecipadamente.

---

# 36. PRINCÍPIO MVP

Não implementar todos os agentes simultaneamente.

Evolução recomendada:

### FASE A

Opportunity Engine

### FASE B

Affiliate Economics

### FASE C

Historical Intelligence

### FASE D

Offer Engine

### FASE E

Page Engine

### FASE F

Creative Engine

### FASE G

Traffic Analytics

### FASE H

Traffic Automation

### FASE I

Learning Engine

### FASE J

Orchestration

### FASE K

Controlled Autonomy

---

# 37. PRIMEIRA PRIORIDADE

O próximo desenvolvimento deve responder:

> "Como transformar um produto identificado pelo Opportunity Engine em uma oportunidade de afiliado economicamente mensurável?"

Portanto, o próximo módulo prioritário é:

# AFFILIATE ECONOMICS ENGINE

Ele deve conectar:

```text
Produto
↓
Programa de afiliado
↓
Comissão
↓
Link
↓
Tracking
↓
Economia
```

Não começar ainda pela automação completa de tráfego.

---

# 38. PRINCÍPIO DE DESENVOLVIMENTO

Antes de implementar uma funcionalidade:

1. compreender o código existente;
2. compreender a arquitetura;
3. verificar se já existe abstração;
4. reutilizar quando possível;
5. propor alteração;
6. implementar;
7. testar;
8. documentar.

Não refatorar por estética.

Não adicionar complexidade sem benefício.

---

# 39. TESTES

Cada módulo deve possuir testes.

Nenhuma nova funcionalidade importante deve ser considerada concluída apenas porque "funciona manualmente".

Testar:

* casos normais;
* ausência de dados;
* dados inválidos;
* erros;
* limites;
* duplicidade;
* integrações;
* fallback;
* segurança.

Manter todos os testes existentes passando.

---

# 40. OBSERVABILIDADE

O sistema deve conseguir explicar:

> "Por que tomou essa decisão?"

Registrar:

* fonte;
* evidência;
* cálculo;
* score;
* regra;
* agente responsável;
* decisão;
* resultado.

O sistema deve ser auditável.

---

# 41. EXPLAINABILITY

Toda recomendação importante deve possuir:

### DECISÃO

O que foi recomendado.

### EVIDÊNCIA

Por que foi recomendado.

### INCERTEZA

O que não sabemos.

### RISCO

O que pode dar errado.

### PRÓXIMO TESTE

Como validar.

---

# 42. SEGURANÇA FINANCEIRA

O sistema deve possuir limites rígidos.

Nunca:

* aumentar orçamento indefinidamente;
* continuar campanha perdedora sem regra;
* criar múltiplas campanhas para driblar limites;
* esconder gasto;
* executar pagamento não autorizado.

Qualquer ação financeira deve ser rastreável.

---

# 43. SEGURANÇA DE CREDENCIAIS

Nunca armazenar diretamente no código:

* API keys;
* tokens;
* client secrets;
* senhas;
* credenciais de anúncios;
* credenciais de afiliados.

Utilizar:

* variáveis de ambiente;
* secret managers;
* armazenamento seguro.

Nunca commitar credenciais.

---

# 44. DESIGN DO SISTEMA

A interface futura deve priorizar:

### Clareza

O usuário deve entender rapidamente:

* o que está acontecendo;
* por que está acontecendo;
* quanto está sendo gasto;
* quanto está retornando.

### Ação

Deve ser fácil:

* aprovar;
* rejeitar;
* pausar;
* escalar;
* testar.

### Transparência

Nunca esconder incerteza.

---

# 45. DASHBOARD FUTURO

O dashboard principal deve eventualmente mostrar:

```text
COMISSÕES
R$ XXX

TRÁFEGO
R$ XXX

RESULTADO
R$ XXX

OPORTUNIDADES ATIVAS
XX

WINNERS
XX

TESTES
XX

TAXA DE SUCESSO
XX%
```

Além disso:

### TOP OPORTUNIDADES

### CAMPANHAS ATIVAS

### ALERTAS

### APRENDIZADOS RECENTES

---

# 46. PRINCÍPIO DE NÃO DEPENDÊNCIA

Sempre que possível, não depender de uma única:

* plataforma;
* marketplace;
* programa de afiliados;
* fonte de dados;
* canal de tráfego.

O sistema deve possuir adaptadores.

Se uma plataforma desaparecer, o sistema deve continuar funcionando parcialmente.

---

# 47. ADAPTADORES

Criar abstrações para:

```text
AffiliateNetwork
TrafficPlatform
DataSource
AnalyticsSource
CreativeProvider
LLMProvider
```

Assim diferentes provedores podem ser substituídos.

---

# 48. CLAUDE COMO ORQUESTRADOR, NÃO COMO VERDADE ABSOLUTA

Claude pode:

* pesquisar;
* analisar;
* escrever;
* programar;
* criar estratégias;
* interpretar dados;
* coordenar agentes.

Mas Claude não é a fonte dos dados.

A fonte é:

# A EVIDÊNCIA

Claude interpreta a evidência.

---

# 49. PRINCÍPIO CENTRAL DO PRODUTO

O sistema deve ser construído em torno deste ciclo:

# FIND → BUILD → ATTRACT → CONVERT → MEASURE → LEARN

### FIND

Encontrar oportunidades.

### BUILD

Construir oferta e ativos.

### ATTRACT

Atrair consumidores.

### CONVERT

Direcionar para compra.

### MEASURE

Medir resultado.

### LEARN

Aprender com o resultado.

Depois:

# REPETIR.

---

# 50. VISÃO FINAL

O objetivo de longo prazo é chegar a uma plataforma em que seja possível iniciar com:

> "Encontre oportunidades de afiliado de até R$150."

E o sistema consiga executar progressivamente:

```text
PESQUISAR
↓
ENCONTRAR
↓
VALIDAR
↓
ESCOLHER
↓
ENCONTRAR AFILIADO
↓
ANALISAR COMISSÃO
↓
CRIAR OFERTA
↓
CRIAR PÁGINA
↓
CRIAR CRIATIVOS
↓
PLANEJAR TRÁFEGO
↓
TESTAR
↓
MEDIR
↓
GERAR COMISSÃO
↓
ANALISAR
↓
APRENDER
↓
ESCALAR
↓
ENCONTRAR PRÓXIMA OPORTUNIDADE
```

O objetivo não é construir um bot que simplesmente "vende produtos".

O objetivo é construir um:

# AFFILIATE COMMERCE ENGINE

Um sistema orientado por evidências que transforma oportunidades em experimentos comerciais, experimentos em dados e dados em decisões cada vez melhores.

A automação deve crescer conforme a confiança aumenta.

A inteligência deve crescer conforme o histórico aumenta.

E a autonomia deve crescer somente quando os resultados justificarem.
