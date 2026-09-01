"""Normalização e deduplicação de candidatos.

Regras (Seção 2 - Engenheiro de Dados):
- eliminar duplicidades;
- identificar dados inconsistentes.
"""

from __future__ import annotations

import difflib
import unicodedata

from poe.models import ProductCandidate

DUPLICATE_SIMILARITY_THRESHOLD = 0.85


def _normalize_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    return ascii_only.strip().lower()


def dedupe(candidates: list[ProductCandidate]) -> tuple[list[ProductCandidate], list[str]]:
    """Remove candidatos duplicados/quase-duplicados.

    Quando dois candidatos são muito similares, mantém o que tem mais
    evidências (mais rastreável). Retorna (candidatos_unicos, log_de_merges).
    """
    kept: list[ProductCandidate] = []
    kept_norm_names: list[str] = []
    log: list[str] = []

    for cand in candidates:
        norm = _normalize_name(cand.name)
        match_idx = None
        for idx, existing_norm in enumerate(kept_norm_names):
            ratio = difflib.SequenceMatcher(None, norm, existing_norm).ratio()
            if ratio >= DUPLICATE_SIMILARITY_THRESHOLD:
                match_idx = idx
                break

        if match_idx is None:
            kept.append(cand)
            kept_norm_names.append(norm)
            continue

        existing = kept[match_idx]
        if len(cand.evidences) > len(existing.evidences):
            log.append(
                f"Duplicata: '{cand.name}' substituiu '{existing.name}' "
                f"(mais evidências: {len(cand.evidences)} vs {len(existing.evidences)})"
            )
            kept[match_idx] = cand
        else:
            log.append(f"Duplicata: '{cand.name}' descartado em favor de '{existing.name}'")

    return kept, log


def flag_inconsistencies(candidates: list[ProductCandidate]) -> list[str]:
    """Detecta inconsistências óbvias sem eliminar o candidato — apenas registra."""
    warnings: list[str] = []
    for cand in candidates:
        if cand.price.max_brl is not None and cand.price.max_brl < cand.price.min_brl:
            warnings.append(f"{cand.name}: price.max menor que price.min — corrigindo (swap).")
            cand.price.min_brl, cand.price.max_brl = cand.price.max_brl, cand.price.min_brl
        if not cand.evidences:
            warnings.append(f"{cand.name}: nenhuma evidência anexada — score ficará baixo/baixa confiança.")
        if cand.price.min_brl <= 0:
            warnings.append(f"{cand.name}: preço mínimo inválido ({cand.price.min_brl}).")
    return warnings
