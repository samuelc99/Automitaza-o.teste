"""Motor de pontuação (Seção 8 do briefing).

Cada dimensão vale um número máximo de pontos (configurável em config.yaml).
A pontuação de uma dimensão é a média das evidências daquela dimensão,
ponderada por: strength (julgamento de quem coletou) x credibility_multiplier
(desconto conforme o tipo: DADO > ESTIMATIVA > INFERENCIA > HIPOTESE).

Sem evidência para uma dimensão = 0 pontos nela + nota de auditoria explícita.
Isso é intencional: no data, no score. Nunca preenchemos lacunas com um
"score médio" arbitrário.
"""

from __future__ import annotations

from poe.models import Dimension, DimensionScore, Evidence, ProductCandidate, ScoreBreakdown


def _weighted_strength(evidences: list[Evidence]) -> float:
    if not evidences:
        return 0.0
    total = sum(e.strength * e.credibility_multiplier() for e in evidences)
    return min(1.0, total / len(evidences))


def score_dimension(
    candidate: ProductCandidate, dimension: Dimension, max_points: float
) -> DimensionScore:
    evidences = candidate.evidences_for(dimension)

    if not evidences:
        return DimensionScore(
            dimension=dimension,
            points=0.0,
            max_points=max_points,
            rationale="Dados insuficientes para confirmar — nenhuma evidência anexada para esta dimensão.",
            evidence_type_used=None,
        )

    weighted = _weighted_strength(evidences)
    points = round(max_points * weighted, 2)

    types_used = sorted({e.evidence_type.value for e in evidences})
    dominant_type = evidences[0].evidence_type
    rationale = (
        f"{len(evidences)} evidência(s) ({', '.join(types_used)}), "
        f"força ponderada média {weighted:.2f} de 1.0."
    )

    return DimensionScore(
        dimension=dimension,
        points=points,
        max_points=max_points,
        rationale=rationale,
        evidence_type_used=dominant_type,
    )


def compute_score(candidate: ProductCandidate, weights: dict[str, float]) -> ScoreBreakdown:
    dimension_scores = [
        score_dimension(candidate, Dimension(dim_name), max_points)
        for dim_name, max_points in weights.items()
    ]
    raw_total = round(sum(ds.points for ds in dimension_scores), 2)

    return ScoreBreakdown(
        dimension_scores=dimension_scores,
        penalties_applied=[],
        raw_total=raw_total,
        final_total=raw_total,  # penalidades aplicadas depois, em penalties.py
    )
