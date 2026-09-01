"""Orquestração do pipeline determinístico:

evidências (JSON) -> normalizar -> filtrar (preço/hard flags) -> pontuar ->
penalizar -> confiança -> auditoria -> histórico (SQLite)

A seleção do TOP 5 final e a redação do relatório (Seções 14-15, 22-23) ficam
fora daqui de propósito — exigem julgamento crítico que não deve ser
mecanizado (ver report/top5.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from poe.audit.auditor import audit_candidate
from poe.collectors.base import EvidenceEnricher
from poe.collectors.evidence_file import EvidenceFileCollector
from poe.models import Confidence, ProductCandidate, ScoredProduct
from poe.observability import RunLog, timed_source_call
from poe.pipeline.filter import apply_hard_filters
from poe.pipeline.normalize import dedupe, flag_inconsistencies
from poe.scoring.confidence import compute_confidence
from poe.scoring.penalties import apply_penalties
from poe.scoring.score import compute_score
from poe.storage.db import HistoryStore


@dataclass
class PipelineResult:
    scored: list[ScoredProduct]
    eliminated: list[tuple[ProductCandidate, str]]
    warnings: list[str]
    run_id: int | None
    run_log: RunLog = field(default_factory=RunLog)


def load_config(config_path: str | Path) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_pipeline(
    evidence_path: str | Path,
    config_path: str | Path = "config.yaml",
    db_path: str | Path = "data/history.db",
    save_history: bool = True,
    enrichers: list[EvidenceEnricher] | None = None,
) -> PipelineResult:
    """Modo manual (padrão): só `evidence_path`, comportamento idêntico a antes.
    Modo híbrido: passe `enrichers` (ex.: [MercadoLivreTrendsSource(...)]) para
    complementar as evidências do arquivo com fontes ao vivo, sem alterar o
    formato que o resto do pipeline recebe (Seção 5).
    """
    config = load_config(config_path)
    warnings: list[str] = []
    run_log = RunLog()

    with timed_source_call(run_log, "evidence_file") as ctx:
        candidates = EvidenceFileCollector(evidence_path).collect()
        ctx["items_returned"] = len(candidates)

    candidates, dedupe_log = dedupe(candidates)
    warnings += dedupe_log
    warnings += flag_inconsistencies(candidates)

    for enricher in enrichers or []:
        with timed_source_call(run_log, enricher.name) as ctx:
            enrich_result = enricher.enrich(candidates)
            ctx["items_returned"] = enrich_result.evidences_added
            ctx["errors"] = enrich_result.errors
            ctx["skipped_reason"] = enrich_result.skipped_reason
        if enrich_result.errors:
            warnings += [f"{enricher.name}: {e}" for e in enrich_result.errors]
        if enrich_result.skipped_reason:
            warnings.append(f"{enricher.name}: pulado — {enrich_result.skipped_reason}")

    approved, eliminated = apply_hard_filters(candidates, config["price"]["hard_limit_brl"])

    scored_products: list[ScoredProduct] = []
    for cand in approved:
        score = compute_score(cand, config["scoring"]["weights"])
        score, penalty_warnings = apply_penalties(cand, score, config["penalties"])
        warnings += penalty_warnings

        confidence, confidence_rationale = compute_confidence(cand, config["confidence"])

        audit_notes = audit_candidate(cand, score, confidence, config["price"]["hard_limit_brl"])

        scored_products.append(
            ScoredProduct(
                candidate=cand,
                score=score,
                confidence=confidence,
                confidence_rationale=confidence_rationale,
                eliminated=False,
                audit_notes=audit_notes,
            )
        )

    for cand, reason in eliminated:
        scored_products.append(
            ScoredProduct(
                candidate=cand,
                score=compute_score(cand, config["scoring"]["weights"]),
                confidence=Confidence.BAIXA,
                confidence_rationale="Produto eliminado antes da pontuação final.",
                eliminated=True,
                elimination_reason=reason,
            )
        )

    scored_products.sort(key=lambda sp: sp.score.final_total, reverse=True)

    run_log.candidates_found = len(candidates)
    run_log.candidates_eliminated = len(eliminated)
    run_log.elimination_reasons = [reason for _, reason in eliminated]

    run_id = None
    if save_history:
        seed_keywords = sorted({c.seed_keyword for c in candidates if c.seed_keyword})
        run_id = HistoryStore(db_path).save_run(scored_products, seed_keywords)

    return PipelineResult(
        scored=scored_products, eliminated=eliminated, warnings=warnings, run_id=run_id, run_log=run_log
    )
