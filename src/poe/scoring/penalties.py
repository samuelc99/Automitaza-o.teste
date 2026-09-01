"""Penalizações (Seção 9). Aplicadas sobre o score total, não sobre sub-scores.

RiskFlag.name deve corresponder a uma chave em config['penalties'] para ser
reconhecida. Flags desconhecidas geram um aviso mas não penalizam
silenciosamente — assim erros de digitação no arquivo de evidências não
somem sem serem notados.
"""

from __future__ import annotations

from poe.models import ProductCandidate, ScoreBreakdown

SEVERITY_MULTIPLIER = {"baixa": 0.5, "media": 1.0, "alta": 1.5}


def apply_penalties(
    candidate: ProductCandidate, score: ScoreBreakdown, penalty_config: dict
) -> tuple[ScoreBreakdown, list[str]]:
    warnings: list[str] = []
    max_total = penalty_config.get("max_total_penalty", 60)

    applied: list[tuple[str, float]] = []
    for flag in candidate.risk_flags:
        weight = penalty_config.get(flag.name)
        if weight is None:
            warnings.append(
                f"{candidate.name}: risk_flag '{flag.name}' não corresponde a nenhuma "
                f"penalidade configurada em config.yaml — ignorada (verifique o nome)."
            )
            continue
        multiplier = SEVERITY_MULTIPLIER.get(flag.severity, 1.0)
        effective = round(float(weight) * multiplier, 2)
        applied.append((f"{flag.name} [{flag.severity}] ({flag.description})", effective))

    total_penalty = min(sum(w for _, w in applied), max_total)
    if sum(w for _, w in applied) > max_total:
        warnings.append(
            f"{candidate.name}: penalidades somadas ({sum(w for _, w in applied):.0f}) "
            f"excederam o teto de {max_total}; aplicado o teto."
        )

    final_total = max(0.0, round(score.raw_total - total_penalty, 2))

    new_score = ScoreBreakdown(
        dimension_scores=score.dimension_scores,
        penalties_applied=applied,
        raw_total=score.raw_total,
        final_total=final_total,
    )
    return new_score, warnings
