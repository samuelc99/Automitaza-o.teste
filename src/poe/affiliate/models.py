"""Modelos do Affiliate Economics Engine (BLUEPRINT.md, Seção 8).

Vocabulário deliberadamente diferente do Opportunity Engine
(DADO/ESTIMATIVA/INFERENCIA/HIPOTESE, ver poe.models): comissão é um domínio
mais simples — cada campo numérico só precisa dizer se é confirmado (achamos
na tabela pública do programa), estimado (calculamos a partir de algo
parecido) ou desconhecido (não achamos, não inventamos). Usar o enum de
4 valores do Opportunity Engine aqui seria forçar uma distinção
(inferência vs hipótese) que não faz sentido para "quanto paga de comissão".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from poe.models import ProductCandidate

_STATUS_ORDER = {"CONFIRMADO": 0, "ESTIMADO": 1, "DESCONHECIDO": 2}


class DataStatus(str, Enum):
    CONFIRMADO = "CONFIRMADO"
    ESTIMADO = "ESTIMADO"
    DESCONHECIDO = "DESCONHECIDO"


def worst_status(statuses: list[DataStatus]) -> DataStatus:
    """O status mais fraco entre vários — usado para propagar incerteza em cálculos."""
    if not statuses:
        return DataStatus.DESCONHECIDO
    return max(statuses, key=lambda s: _STATUS_ORDER[s.value])


class CommissionType(str, Enum):
    PERCENTUAL = "percentual"
    FIXO = "fixo"
    MISTO = "misto"


@dataclass
class TrackedValue:
    """Um número com seu próprio nível de confiança — nunca preenchido 'pra completar'."""

    value: Optional[float]
    status: DataStatus
    source_url: Optional[str] = None
    note: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status == DataStatus.DESCONHECIDO and self.value is not None:
            raise ValueError("TrackedValue: value deve ser None quando status é DESCONHECIDO")
        if self.status != DataStatus.DESCONHECIDO and self.value is None:
            raise ValueError(f"TrackedValue: value é obrigatório quando status é {self.status.value}")

    @staticmethod
    def unknown(note: Optional[str] = None) -> "TrackedValue":
        return TrackedValue(value=None, status=DataStatus.DESCONHECIDO, note=note)

    def is_known(self) -> bool:
        return self.status != DataStatus.DESCONHECIDO


@dataclass
class CommissionInfo:
    """Termos de comissão de um programa de afiliado para um produto/categoria.

    Pesquisado manualmente (WebSearch em tabelas públicas de comissão) — ver
    manual_source.py. Quando um campo não é publicamente documentado, deve
    ficar TrackedValue.unknown(), nunca um chute.
    """

    network_name: str
    commission_type: CommissionType
    commission_percent: TrackedValue = field(default_factory=TrackedValue.unknown)
    commission_fixed_brl: TrackedValue = field(default_factory=TrackedValue.unknown)
    cookie_duration_days: TrackedValue = field(default_factory=TrackedValue.unknown)
    epc_brl: TrackedValue = field(default_factory=TrackedValue.unknown)
    direct_costs_brl: TrackedValue = field(default_factory=TrackedValue.unknown)
    payout_terms: Optional[str] = None
    restrictions: list[str] = field(default_factory=list)
    category: Optional[str] = None
    collected_at: Optional[str] = None
    source_url: Optional[str] = None
    source_name: Optional[str] = None


@dataclass
class CommissionEstimate:
    """Resultado do cálculo de comissão bruta/líquida para uma venda (Seção 8)."""

    gross_commission_brl: Optional[float]
    net_commission_brl: Optional[float]
    status: DataStatus
    basis: str
    assumptions: list[str] = field(default_factory=list)


@dataclass
class AffiliateOffer:
    """Liga um ProductCandidate do Opportunity Engine a uma oferta de afiliado."""

    candidate: ProductCandidate
    commission: CommissionInfo
    estimate: CommissionEstimate
