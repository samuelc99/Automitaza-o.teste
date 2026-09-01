"""Orquestração mínima do Affiliate Economics Engine:

candidatos (do Opportunity Engine) + rede de afiliados -> AffiliateOffer[]

Candidatos sem oferta encontrada são omitidos do resultado, não forçados
com dado inventado (Seção 25).
"""

from __future__ import annotations

from poe.affiliate.economics import compute_commission_estimate
from poe.affiliate.models import AffiliateOffer
from poe.affiliate.network import AffiliateNetwork
from poe.models import ProductCandidate


def build_affiliate_offers(
    candidates: list[ProductCandidate], network: AffiliateNetwork
) -> tuple[list[AffiliateOffer], list[str]]:
    """Retorna (offers, avisos). Um aviso é gerado para cada candidato sem oferta encontrada."""
    offers: list[AffiliateOffer] = []
    warnings: list[str] = []

    for candidate in candidates:
        commission = network.lookup_commission(candidate)
        if commission is None:
            warnings.append(
                f"{candidate.name}: nenhuma oferta de afiliado encontrada em '{network.name}' "
                f"(nem por nome nem por categoria '{candidate.category}')."
            )
            continue

        estimate = compute_commission_estimate(candidate.price.representative, commission)
        offers.append(AffiliateOffer(candidate=candidate, commission=commission, estimate=estimate))

    return offers, warnings
