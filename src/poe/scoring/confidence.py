"""Nível de confiança (Seção 16).

Um score alto baseado em evidências fracas (HIPOTESE/INFERENCIA, poucas
fontes independentes) NÃO deve ser tratado como alta confiança. A confiança
mede a qualidade da evidência, não a magnitude do score.
"""

from __future__ import annotations

from poe.models import Confidence, EvidenceType, ProductCandidate


def compute_confidence(
    candidate: ProductCandidate, confidence_config: dict
) -> tuple[Confidence, str]:
    evidences = candidate.evidences
    if not evidences:
        return Confidence.BAIXA, "Nenhuma evidência coletada para este candidato."

    n_sources = len(candidate.independent_sources())
    n_dado = sum(1 for e in evidences if e.evidence_type == EvidenceType.DADO and e.source_url)
    dado_ratio = n_dado / len(evidences)

    min_sources_alta = confidence_config.get("min_sources_for_alta", 3)
    min_ratio_alta = confidence_config.get("min_dado_ratio_for_alta", 0.5)
    min_sources_media = confidence_config.get("min_sources_for_media", 2)

    if n_sources >= min_sources_alta and dado_ratio >= min_ratio_alta:
        return (
            Confidence.ALTA,
            f"{n_sources} fontes independentes, {n_dado}/{len(evidences)} evidências são DADO verificável.",
        )

    if n_sources >= min_sources_media:
        return (
            Confidence.MEDIA,
            f"{n_sources} fontes independentes, mas apenas {n_dado}/{len(evidences)} evidências "
            f"são DADO verificável — restante é estimativa/inferência/hipótese.",
        )

    return (
        Confidence.BAIXA,
        f"Apenas {n_sources} fonte(s) independente(s) e {n_dado}/{len(evidences)} evidências "
        f"verificáveis — evidência insuficiente para confiar fortemente neste score.",
    )
