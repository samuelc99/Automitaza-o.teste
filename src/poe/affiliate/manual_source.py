"""Fonte manual de dados de comissão — carrega de um JSON pesquisado via WebSearch
em tabelas públicas de comissão dos programas de afiliado.

Mesmo padrão do EvidenceFileCollector do Opportunity Engine
(poe.collectors.evidence_file): dado real coletado por quem pesquisa
(agente ou humano), validado contra um schema, nunca inventado pelo código.

Ver data/affiliate_template.json para o schema esperado.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from poe.affiliate.models import CommissionInfo, CommissionType, DataStatus, TrackedValue
from poe.affiliate.network import AffiliateNetwork
from poe.models import ProductCandidate


class AffiliateInfoValidationError(Exception):
    pass


def _parse_tracked_value(raw: Optional[dict], field_name: str, context: str) -> TrackedValue:
    if raw is None:
        return TrackedValue.unknown()
    try:
        status = DataStatus(raw["status"])
    except KeyError as e:
        raise AffiliateInfoValidationError(f"{context}: campo '{field_name}.status' é obrigatório") from e
    except ValueError as e:
        raise AffiliateInfoValidationError(f"{context}: {field_name}.status inválido: {e}") from e

    value = raw.get("value")
    try:
        return TrackedValue(
            value=float(value) if value is not None else None,
            status=status,
            source_url=raw.get("source_url"),
            note=raw.get("note"),
        )
    except ValueError as e:
        raise AffiliateInfoValidationError(f"{context}: {field_name}: {e}") from e


def _normalize(text: str) -> str:
    import unicodedata

    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).strip().lower()


class AffiliateInfoFileCollector(AffiliateNetwork):
    name = "affiliate_info_file"

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._by_candidate_name: dict[str, CommissionInfo] = {}
        self._by_category: dict[str, CommissionInfo] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if not self.path.exists():
            raise AffiliateInfoValidationError(f"Arquivo de comissões não encontrado: {self.path}")

        raw = json.loads(self.path.read_text(encoding="utf-8"))
        for i, offer in enumerate(raw.get("offers", [])):
            context = f"offers[{i}] ({offer.get('network_name', '?')})"
            match = offer.get("match", {})
            if not match.get("candidate_name") and not match.get("category"):
                raise AffiliateInfoValidationError(
                    f"{context}: 'match' precisa de 'candidate_name' e/ou 'category'"
                )

            try:
                commission_type = CommissionType(offer["commission_type"])
            except KeyError as e:
                raise AffiliateInfoValidationError(f"{context}: 'commission_type' é obrigatório") from e
            except ValueError as e:
                raise AffiliateInfoValidationError(f"{context}: commission_type inválido: {e}") from e

            if not offer.get("network_name"):
                raise AffiliateInfoValidationError(f"{context}: 'network_name' é obrigatório")

            info = CommissionInfo(
                network_name=offer["network_name"],
                commission_type=commission_type,
                commission_percent=_parse_tracked_value(offer.get("commission_percent"), "commission_percent", context),
                commission_fixed_brl=_parse_tracked_value(
                    offer.get("commission_fixed_brl"), "commission_fixed_brl", context
                ),
                cookie_duration_days=_parse_tracked_value(
                    offer.get("cookie_duration_days"), "cookie_duration_days", context
                ),
                epc_brl=_parse_tracked_value(offer.get("epc_brl"), "epc_brl", context),
                direct_costs_brl=_parse_tracked_value(offer.get("direct_costs_brl"), "direct_costs_brl", context),
                payout_terms=offer.get("payout_terms"),
                restrictions=offer.get("restrictions", []),
                category=offer.get("category"),
                collected_at=offer.get("collected_at"),
                source_url=offer.get("source_url"),
                source_name=offer.get("source_name"),
            )

            if match.get("candidate_name"):
                self._by_candidate_name[_normalize(match["candidate_name"])] = info
            if match.get("category"):
                self._by_category[_normalize(match["category"])] = info

        self._loaded = True

    def lookup_commission(self, candidate: ProductCandidate) -> Optional[CommissionInfo]:
        self._ensure_loaded()
        by_name = self._by_candidate_name.get(_normalize(candidate.name))
        if by_name is not None:
            return by_name
        return self._by_category.get(_normalize(candidate.category))
