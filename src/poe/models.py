"""Modelos de dados centrais do Product Opportunity Engine.

Distinção obrigatória (ver Seção 3 do briefing do projeto):
- DADO: informação encontrada em uma fonte, com URL rastreável.
- ESTIMATIVA: cálculo derivado de dados disponíveis (deve declarar premissas).
- INFERENCIA: conclusão lógica baseada em sinais indiretos.
- HIPOTESE: possibilidade ainda não validada.

Nenhum número deve entrar no sistema sem um desses rótulos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class EvidenceType(str, Enum):
    DADO = "DADO"
    ESTIMATIVA = "ESTIMATIVA"
    INFERENCIA = "INFERENCIA"
    HIPOTESE = "HIPOTESE"


class Dimension(str, Enum):
    DEMANDA = "demanda"
    CRESCIMENTO = "crescimento"
    CONCORRENCIA = "concorrencia"
    MARGEM = "margem"
    LOGISTICA = "logistica"
    MARKETING = "marketing"
    RISCO = "risco"


@dataclass
class Evidence:
    dimension: Dimension
    claim: str
    evidence_type: EvidenceType
    strength: float = 0.5
    """Quão fortemente esta evidência sustenta a dimensão, de 0.0 a 1.0.

    Julgamento explícito de quem coletou a evidência (o agente, ao pesquisar).
    Não é calculado por NLP mágico — é uma avaliação transparente e auditável,
    documentada em `claim`/`note` para que outra pessoa possa discordar dela.
    """
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    collected_at: Optional[str] = None
    note: Optional[str] = None

    # Estrutura opcional (Seção 6 — "qualidade das evidências"). Quando a
    # evidência tem um número real por trás (não só prosa em `claim`), vale
    # preenchê-los — permite auditar/comparar sem reparsear texto livre.
    value: Optional[float] = None
    unit: Optional[str] = None
    methodology: Optional[str] = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"strength deve estar entre 0.0 e 1.0, recebido {self.strength}")

    def is_verifiable(self) -> bool:
        return self.evidence_type == EvidenceType.DADO and bool(self.source_url)

    def credibility_multiplier(self) -> float:
        """Desconta a força da evidência conforme o quão especulativo é o tipo."""
        return {
            EvidenceType.DADO: 1.0 if self.source_url else 0.8,
            EvidenceType.ESTIMATIVA: 0.85,
            EvidenceType.INFERENCIA: 0.7,
            EvidenceType.HIPOTESE: 0.4,
        }[self.evidence_type]


@dataclass
class PriceInfo:
    min_brl: float
    max_brl: Optional[float] = None
    evidence_type: EvidenceType = EvidenceType.DADO
    source_url: Optional[str] = None
    note: Optional[str] = None

    @property
    def representative(self) -> float:
        if self.max_brl is not None:
            return (self.min_brl + self.max_brl) / 2
        return self.min_brl


@dataclass
class RiskFlag:
    name: str
    description: str
    severity: str = "media"  # baixa | media | alta


@dataclass
class ProductCandidate:
    name: str
    category: str
    seed_keyword: str
    price: PriceInfo
    evidences: list[Evidence] = field(default_factory=list)
    risk_flags: list[RiskFlag] = field(default_factory=list)
    hard_flags: list[str] = field(default_factory=list)
    collected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None

    # Conteúdo narrativo estruturado (Seções 11, 12, 13) — dicts livres porque
    # o valor está no conteúdo qualitativo, não em cálculo sobre eles.
    marketing_analysis: Optional[dict] = None
    competition_analysis: Optional[dict] = None
    margin_analysis: Optional[dict] = None

    def evidences_for(self, dimension: Dimension) -> list[Evidence]:
        return [e for e in self.evidences if e.dimension == dimension]

    def independent_sources(self) -> set[str]:
        return {e.source_name or e.source_url for e in self.evidences if e.source_name or e.source_url}


@dataclass
class DimensionScore:
    dimension: Dimension
    points: float
    max_points: float
    rationale: str
    evidence_type_used: EvidenceType


@dataclass
class ScoreBreakdown:
    dimension_scores: list[DimensionScore]
    penalties_applied: list[tuple[str, float]]
    raw_total: float
    final_total: float

    def as_dict(self) -> dict:
        return {
            "dimensoes": {d.dimension.value: d.points for d in self.dimension_scores},
            "penalidades": dict(self.penalties_applied),
            "raw_total": self.raw_total,
            "final_total": self.final_total,
        }


class Confidence(str, Enum):
    ALTA = "Alta"
    MEDIA = "Média"
    BAIXA = "Baixa"


@dataclass
class ScoredProduct:
    candidate: ProductCandidate
    score: ScoreBreakdown
    confidence: Confidence
    confidence_rationale: str
    eliminated: bool = False
    elimination_reason: Optional[str] = None
    audit_notes: list[str] = field(default_factory=list)
