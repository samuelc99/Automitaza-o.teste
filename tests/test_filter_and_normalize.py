from poe.models import Evidence, Dimension, EvidenceType, PriceInfo, ProductCandidate
from poe.pipeline.filter import apply_hard_filters
from poe.pipeline.normalize import dedupe, flag_inconsistencies


def make_candidate(name, price_min, price_max=None, hard_flags=None, n_evidences=0):
    evidences = [
        Evidence(Dimension.DEMANDA, f"claim {i}", EvidenceType.DADO, source_url="https://x.com")
        for i in range(n_evidences)
    ]
    return ProductCandidate(
        name=name,
        category="c",
        seed_keyword="k",
        price=PriceInfo(min_brl=price_min, max_brl=price_max),
        hard_flags=hard_flags or [],
        evidences=evidences,
    )


def test_price_above_limit_is_eliminated():
    cand = make_candidate("Produto Caro", 200.0)
    approved, eliminated = apply_hard_filters([cand], price_hard_limit=150.0)
    assert approved == []
    assert len(eliminated) == 1
    assert "150" in eliminated[0][1]


def test_price_within_limit_is_approved():
    cand = make_candidate("Produto Ok", 90.0)
    approved, eliminated = apply_hard_filters([cand], price_hard_limit=150.0)
    assert approved == [cand]
    assert eliminated == []


def test_hard_flag_eliminates_regardless_of_price():
    cand = make_candidate("Produto Ilegal", 50.0, hard_flags=["produto_ilegal_ou_proibido"])
    approved, eliminated = apply_hard_filters([cand], price_hard_limit=150.0)
    assert approved == []
    assert len(eliminated) == 1


def test_dedupe_keeps_candidate_with_more_evidence():
    a = make_candidate("Mini Massageador Portátil", 50.0, n_evidences=1)
    b = make_candidate("Mini massageador portatil", 55.0, n_evidences=3)
    kept, log = dedupe([a, b])
    assert len(kept) == 1
    assert kept[0].name == "Mini massageador portatil"
    assert len(log) == 1


def test_flag_inconsistencies_swaps_inverted_price():
    cand = make_candidate("Produto", price_min=100.0, price_max=50.0, n_evidences=1)
    warnings = flag_inconsistencies([cand])
    assert cand.price.min_brl == 50.0
    assert cand.price.max_brl == 100.0
    assert len(warnings) == 1
