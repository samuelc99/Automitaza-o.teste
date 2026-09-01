"""Auditoria crítica (Seção 22).

Importante: isto NÃO substitui o julgamento crítico do agente ao escrever o
relatório final. São checagens mecânicas e keyword-based que apontam sinais
para revisão humana/do agente — elas nunca deveriam ser a única linha de
defesa contra uma má recomendação. Trate os audit_notes como uma lista de
"coisas a verificar antes de recomendar", não como um veredito automático.
"""

from __future__ import annotations

from poe.models import Confidence, Dimension, EvidenceType, ProductCandidate, ScoreBreakdown

_RED_FLAG_KEYWORDS = [
    "queda", "declínio", "declinio", "caindo", "perdendo força",
    "saturad", "saturaç", "copiad", "falsificad", "processo judicial",
    "patente", "recall", "proibid", "banido", "ilegal", "reclama",
]

_SEASONALITY_KEYWORDS = [
    "natal", "black friday", "dia das mães", "dia das maes", "dia dos namorados",
    "verão", "verao", "festa junina", "volta às aulas", "volta as aulas", "páscoa", "pascoa",
]


def audit_candidate(
    candidate: ProductCandidate,
    score: ScoreBreakdown,
    confidence: Confidence,
    price_hard_limit: float,
) -> list[str]:
    notes: list[str] = []

    # 1. Score alto x confiança baixa (Seção 16)
    if score.final_total >= 70 and confidence in (Confidence.BAIXA, Confidence.MEDIA):
        notes.append(
            f"Score alto ({score.final_total}) mas confiança {confidence.value} — "
            f"não tratar como oportunidade robusta sem evidências adicionais."
        )

    # 2. Preço perto do limite obrigatório
    ref_price = candidate.price.representative
    if ref_price >= price_hard_limit * 0.9:
        notes.append(
            f"Preço de referência (R${ref_price:.2f}) está próximo do limite de "
            f"R${price_hard_limit:.2f} — confirmar que os demais indicadores são "
            f"excepcionalmente fortes antes de manter no ranking (Seção 4)."
        )

    # 3. Crescimento sem evidência real (só HIPOTESE/INFERENCIA)
    crescimento_evs = candidate.evidences_for(Dimension.CRESCIMENTO)
    if crescimento_evs and all(
        e.evidence_type in (EvidenceType.HIPOTESE, EvidenceType.INFERENCIA) for e in crescimento_evs
    ):
        notes.append(
            "Crescimento não está confirmado por DADO/ESTIMATIVA — é inferência ou hipótese. "
            "Risco de recomendar um pico passageiro em vez de tendência real (Seção 7)."
        )
    elif not crescimento_evs:
        notes.append("Dados insuficientes para confirmar crescimento.")

    # 4. Demanda sem evidência real
    if not candidate.evidences_for(Dimension.DEMANDA):
        notes.append("Dados insuficientes para confirmar demanda atual.")

    # 5. Keyword scan por sinais contraditórios em qualquer claim
    for ev in candidate.evidences:
        lowered = ev.claim.lower()
        for kw in _RED_FLAG_KEYWORDS:
            if kw in lowered:
                notes.append(
                    f"Possível sinal de alerta na evidência de {ev.dimension.value}: "
                    f"\"{ev.claim[:140]}\" (contém '{kw}') — revisar antes de recomendar."
                )
                break

    # 6. Sazonalidade
    all_text = " ".join(e.claim.lower() for e in candidate.evidences) + " " + (candidate.notes or "").lower()
    for kw in _SEASONALITY_KEYWORDS:
        if kw in all_text:
            notes.append(
                f"Possível sazonalidade detectada (menção a '{kw}') — verificar se a demanda "
                f"se sustenta fora dessa época antes de investir estoque."
            )
            break

    # 7. Risco de propriedade intelectual / dependência de marca sem penalidade correspondente
    flag_names = {f.name for f in candidate.risk_flags}
    if "risco_propriedade_intelectual" not in flag_names:
        for ev in candidate.evidences:
            if "marca" in ev.claim.lower() and ("réplica" in ev.claim.lower() or "replica" in ev.claim.lower()):
                notes.append(
                    "Evidência menciona possível réplica/uso de marca sem risk_flag "
                    "'risco_propriedade_intelectual' registrada — considerar adicionar."
                )

    return notes
