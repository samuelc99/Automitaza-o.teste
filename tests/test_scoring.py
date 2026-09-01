from poe.models import Dimension, Evidence, EvidenceType, PriceInfo, ProductCandidate
from poe.scoring.score import compute_score, score_dimension

WEIGHTS = {
    "demanda": 25,
    "crescimento": 20,
    "concorrencia": 15,
    "margem": 15,
    "logistica": 10,
    "marketing": 10,
    "risco": 5,
}


def make_candidate(evidences=None):
    return ProductCandidate(
        name="Produto Teste",
        category="teste",
        seed_keyword="teste",
        price=PriceInfo(min_brl=50.0),
        evidences=evidences or [],
    )


def test_dimension_with_no_evidence_scores_zero():
    cand = make_candidate()
    ds = score_dimension(cand, Dimension.DEMANDA, 25)
    assert ds.points == 0.0
    assert "insuficientes" in ds.rationale.lower()


def test_dado_evidence_with_full_strength_scores_near_max():
    cand = make_candidate(
        [
            Evidence(
                dimension=Dimension.DEMANDA,
                claim="Produto com alta procura confirmada",
                evidence_type=EvidenceType.DADO,
                strength=1.0,
                source_url="https://example.com/fonte",
            )
        ]
    )
    ds = score_dimension(cand, Dimension.DEMANDA, 25)
    assert ds.points == 25.0


def test_hipotese_evidence_is_heavily_discounted():
    cand = make_candidate(
        [
            Evidence(
                dimension=Dimension.CRESCIMENTO,
                claim="Pode estar crescendo",
                evidence_type=EvidenceType.HIPOTESE,
                strength=1.0,
            )
        ]
    )
    ds = score_dimension(cand, Dimension.CRESCIMENTO, 20)
    # credibility_multiplier para HIPOTESE é 0.4
    assert ds.points == 8.0


def test_compute_score_sums_all_dimensions():
    cand = make_candidate(
        [
            Evidence(
                dimension=Dimension.DEMANDA,
                claim="x",
                evidence_type=EvidenceType.DADO,
                strength=1.0,
                source_url="https://example.com",
            )
        ]
    )
    score = compute_score(cand, WEIGHTS)
    assert score.raw_total == 25.0
    assert score.final_total == 25.0  # penalidades ainda não aplicadas neste módulo
