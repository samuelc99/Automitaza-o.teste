"""Interfaces base para fontes de evidência.

Duas responsabilidades distintas, porque nem toda fonte consegue "nascer" um
produto completo:

- EvidenceSource: cria ProductCandidate do zero (precisa, no mínimo, de nome
  e preço). Ex.: EvidenceFileCollector (evidências coletadas via WebSearch em
  sessão manual). O restante do pipeline (normalize/filter/score/audit/
  history) não precisa saber de onde os candidatos vieram.

- EvidenceEnricher: NÃO cria candidatos — anexa Evidence adicional a
  candidatos que já existem, casando por nome/seed_keyword. Existe porque
  algumas fontes reais (ex.: Mercado Livre /trends) dão sinal de
  demanda/crescimento para uma palavra-chave, mas não têm preço nem
  identidade de produto — não dá pra fingir que criam um ProductCandidate
  sozinhas (ver mercadolivre.py e README.md).

Quando uma nova fonte real tiver dados suficientes para preço + identidade de
produto (ex.: catálogo de um seller_id específico via API oficial), ela deve
implementar EvidenceSource. Quando só tiver sinal de popularidade/tendência
para enriquecer candidatos já conhecidos, implementa EvidenceEnricher.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from poe.models import Evidence, ProductCandidate


class EvidenceSource(ABC):
    name: str

    @abstractmethod
    def collect(self) -> list[ProductCandidate]:
        """Retorna candidatos a produto com suas evidências já anexadas."""
        raise NotImplementedError


# Alias de compatibilidade — código/testes escritos antes desta task usavam
# este nome. Mesma classe, dois nomes.
Collector = EvidenceSource


@dataclass
class EnrichmentResult:
    """Registro de observabilidade de uma chamada de enriquecimento (Seção 10)."""

    source_name: str
    candidates_checked: int = 0
    candidates_matched: int = 0
    evidences_added: int = 0
    errors: list[str] = field(default_factory=list)
    skipped_reason: str | None = None
    duration_seconds: float = 0.0

    def as_log_line(self) -> str:
        if self.skipped_reason:
            return f"[{self.source_name}] pulado: {self.skipped_reason}"
        return (
            f"[{self.source_name}] {self.candidates_matched}/{self.candidates_checked} candidatos "
            f"enriquecidos, {self.evidences_added} evidências adicionadas, "
            f"{len(self.errors)} erro(s), {self.duration_seconds:.2f}s"
        )


class EvidenceEnricher(ABC):
    name: str

    @abstractmethod
    def enrich(self, candidates: list[ProductCandidate]) -> EnrichmentResult:
        """Anexa Evidence aos candidatos que casarem com sinais desta fonte.

        Muta `candidates` in-place (appende em `candidate.evidences`) e
        retorna um EnrichmentResult para log/observabilidade. Nunca deve
        lançar exceção para erros de rede/auth/dados — deve capturar,
        registrar em `errors` ou `skipped_reason`, e devolver um resultado
        vazio, para que a ausência desta fonte nunca quebre o pipeline
        (Seção 5 — modo manual continua funcionando).
        """
        raise NotImplementedError


def match_keyword(keyword: str, candidate: ProductCandidate) -> bool:
    """Casamento por substring (normalizado), bidirecional, usado pelos enrichers.

    Heurística simples de propósito — documentar isso explicitamente evita
    fingir precisão que não existe. Ver normalize._normalize_name.
    """
    from poe.pipeline.normalize import _normalize_name

    kw = _normalize_name(keyword)
    name = _normalize_name(candidate.name)
    seed = _normalize_name(candidate.seed_keyword) if candidate.seed_keyword else ""

    if not kw:
        return False
    return kw in name or name in kw or (seed and (kw in seed or seed in kw))
