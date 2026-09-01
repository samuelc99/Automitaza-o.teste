import json

import pytest

from poe.collectors.base import EnrichmentResult, EvidenceEnricher
from poe.models import Dimension, Evidence, EvidenceType
from poe.pipeline.run import run_pipeline

EVIDENCE = {
    "candidates": [
        {
            "name": "Produto Teste Hibrido",
            "category": "teste",
            "seed_keyword": "produto teste",
            "price_brl": {"min": 50.0, "type": "DADO", "source_url": "https://example.com"},
            "evidences": [
                {
                    "dimension": "demanda",
                    "claim": "evidencia manual",
                    "type": "DADO",
                    "strength": 0.6,
                    "source_url": "https://example.com",
                }
            ],
        }
    ]
}


class FakeEnricherThatAdds(EvidenceEnricher):
    name = "fake_enricher_ok"

    def enrich(self, candidates):
        result = EnrichmentResult(source_name=self.name, candidates_checked=len(candidates))
        for cand in candidates:
            cand.evidences.append(
                Evidence(
                    dimension=Dimension.CRESCIMENTO,
                    claim="crescimento detectado via fonte fake",
                    evidence_type=EvidenceType.DADO,
                    strength=0.7,
                    source_name="fake",
                )
            )
            result.evidences_added += 1
            result.candidates_matched += 1
        return result


class FakeEnricherThatSkips(EvidenceEnricher):
    name = "fake_enricher_skips"

    def enrich(self, candidates):
        result = EnrichmentResult(source_name=self.name, candidates_checked=len(candidates))
        result.skipped_reason = "credenciais ausentes (simulado)"
        return result


class FakeEnricherThatErrors(EvidenceEnricher):
    name = "fake_enricher_errors"

    def enrich(self, candidates):
        result = EnrichmentResult(source_name=self.name, candidates_checked=len(candidates))
        result.errors.append("erro simulado de rede")
        return result


@pytest.fixture
def evidence_file(tmp_path):
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(EVIDENCE), encoding="utf-8")
    return path


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "history.db"


def test_manual_mode_unaffected_by_new_enrichers_param(evidence_file, db_path):
    """Sem passar `enrichers`, comportamento idêntico ao pipeline original."""
    result = run_pipeline(evidence_file, db_path=db_path)
    assert len(result.scored) == 1
    assert len(result.scored[0].candidate.evidences) == 1  # só a evidência manual


def test_hybrid_mode_merges_manual_and_enricher_evidence(evidence_file, db_path):
    result = run_pipeline(evidence_file, db_path=db_path, enrichers=[FakeEnricherThatAdds()])

    cand = result.scored[0].candidate
    assert len(cand.evidences) == 2  # manual + enricher
    dims = {e.dimension for e in cand.evidences}
    assert Dimension.DEMANDA in dims
    assert Dimension.CRESCIMENTO in dims


def test_enricher_skip_reason_becomes_warning_not_crash(evidence_file, db_path):
    result = run_pipeline(evidence_file, db_path=db_path, enrichers=[FakeEnricherThatSkips()])

    assert len(result.scored) == 1  # pipeline não quebrou
    assert any("credenciais ausentes" in w for w in result.warnings)


def test_enricher_error_becomes_warning_not_crash(evidence_file, db_path):
    result = run_pipeline(evidence_file, db_path=db_path, enrichers=[FakeEnricherThatErrors()])

    assert len(result.scored) == 1
    assert any("erro simulado de rede" in w for w in result.warnings)


def test_run_log_records_source_calls(evidence_file, db_path):
    result = run_pipeline(evidence_file, db_path=db_path, enrichers=[FakeEnricherThatAdds()])

    source_names = [c.source_name for c in result.run_log.source_calls]
    assert "evidence_file" in source_names
    assert "fake_enricher_ok" in source_names
    assert result.run_log.candidates_found == 1


def test_evidence_history_is_persisted(evidence_file, db_path):
    from poe.storage.db import HistoryStore

    run_pipeline(evidence_file, db_path=db_path, enrichers=[FakeEnricherThatAdds()])

    history = HistoryStore(db_path).evidence_history_for("Produto Teste Hibrido")
    assert len(history) == 2
    dimensions = {h["dimension"] for h in history}
    assert "demanda" in dimensions
    assert "crescimento" in dimensions
