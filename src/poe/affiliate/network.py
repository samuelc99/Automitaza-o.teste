"""Adaptador de rede de afiliados (BLUEPRINT.md, Seção 47 — não depender de um único provedor).

Hoje só existe implementação manual (AffiliateInfoFileCollector, ver
manual_source.py) porque nenhum programa de afiliado testado nesta sessão
(Amazon Associates, AliExpress Affiliate, Shopee Affiliate) dá acesso
programático sem aprovação prévia com histórico de vendas/tráfego — mesma
barreira já documentada no README do Opportunity Engine. Quando/se uma conta
for aprovada em algum programa, uma nova classe implementando esta mesma
interface (ex.: AmazonAssociatesNetwork) pluga sem mudar o resto do sistema.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from poe.affiliate.models import CommissionInfo
from poe.models import ProductCandidate


class AffiliateNetwork(ABC):
    name: str

    @abstractmethod
    def lookup_commission(self, candidate: ProductCandidate) -> Optional[CommissionInfo]:
        """Retorna os termos de comissão para este candidato, ou None se não encontrado.

        None é uma resposta válida (Seção 25 — nunca inventar dado). Um
        candidato sem oferta de afiliado encontrada simplesmente não aparece
        no relatório de economics, não deve virar CommissionInfo com campos
        forçados.
        """
        raise NotImplementedError
