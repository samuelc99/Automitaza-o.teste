from poe.models import Dimension, Evidence, EvidenceType, PriceInfo, ProductCandidate, Confidence
from poe.scoring.confidence import compute_confidence

CONFIG = {"min_sources_for_alta": 3, "min_dado_ratio_for_alta": 0.5, "min_sources_for_media": 2}


def make_candidate(evidences):
    return ProductCandidate(name="p", category="c", seed_keyword="k", price=PriceInfo(min_brl=10), evidences=evidences)


def test_no_evidence_is_low_confidence():
    conf, _ = compute_confidence(make_candidate([]), CONFIG)
    assert conf == Confidence.BAIXA


def test_many_sources_and_dado_ratio_is_high_confidence():
    evs = [
        Evidence(Dimension.DEMANDA, "a", EvidenceType.DADO, source_url="https://a.com", source_name="a"),
        Evidence(Dimension.CRESCIMENTO, "b", EvidenceType.DADO, source_url="https://b.com", source_name="b"),
        Evidence(Dimension.MARGEM, "c", EvidenceType.DADO, source_url="https://c.com", source_name="c"),
    ]
    conf, _ = compute_confidence(make_candidate(evs), CONFIG)
    assert conf == Confidence.ALTA


def test_high_score_but_only_hipotese_is_low_confidence():
    evs = [Evidence(Dimension.DEMANDA, "a", EvidenceType.HIPOTESE, source_name="chute")]
    conf, rationale = compute_confidence(make_candidate(evs), CONFIG)
    assert conf == Confidence.BAIXA
    assert "insuficiente" in rationale.lower() or "fonte" in rationale.lower()
