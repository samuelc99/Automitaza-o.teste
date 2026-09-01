"""Filtro de eliminação: remove candidatos com barreiras de entrada, antes do score.

Seção 4: preço final ao consumidor deve ser <= hard_limit_brl.
Seção 9: produtos com riscos graves podem ser eliminados antes do ranking final.
"""

from __future__ import annotations

from poe.models import ProductCandidate


def apply_hard_filters(
    candidates: list[ProductCandidate], price_hard_limit: float
) -> tuple[list[ProductCandidate], list[tuple[ProductCandidate, str]]]:
    """Retorna (aprovados, eliminados_com_motivo)."""
    approved: list[ProductCandidate] = []
    eliminated: list[tuple[ProductCandidate, str]] = []

    for cand in candidates:
        reference_price = cand.price.representative

        if reference_price > price_hard_limit:
            eliminated.append(
                (
                    cand,
                    f"Preço de referência R${reference_price:.2f} acima do limite obrigatório "
                    f"de R${price_hard_limit:.2f}.",
                )
            )
            continue

        if cand.hard_flags:
            eliminated.append(
                (cand, f"Flag(s) crítica(s) de eliminação: {', '.join(cand.hard_flags)}.")
            )
            continue

        approved.append(cand)

    return approved, eliminated
