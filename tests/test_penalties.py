from poe.models import PriceInfo, ProductCandidate, RiskFlag, ScoreBreakdown
from poe.scoring.penalties import apply_penalties

CONFIG = {
    "produto_fragil": 8,
    "mercado_saturado": 15,
    "max_total_penalty": 60,
}


def make_score(raw_total=80.0):
    return ScoreBreakdown(dimension_scores=[], penalties_applied=[], raw_total=raw_total, final_total=raw_total)


def make_candidate(risk_flags):
    return ProductCandidate(
        name="p",
        category="c",
        seed_keyword="k",
        price=PriceInfo(min_brl=50.0),
        risk_flags=risk_flags,
    )


def test_known_flag_deducted_from_total():
    cand = make_candidate([RiskFlag(name="produto_fragil", description="quebra fácil")])
    score, warnings = apply_penalties(cand, make_score(80.0), CONFIG)
    assert score.final_total == 72.0
    assert warnings == []


def test_unknown_flag_produces_warning_and_no_deduction():
    cand = make_candidate([RiskFlag(name="flag_inventada", description="x")])
    score, warnings = apply_penalties(cand, make_score(80.0), CONFIG)
    assert score.final_total == 80.0
    assert len(warnings) == 1
    assert "flag_inventada" in warnings[0]


def test_penalties_capped_at_max_total():
    cand = make_candidate(
        [RiskFlag(name="mercado_saturado", description="x")] * 5  # 5x15=75 > 60
    )
    score, warnings = apply_penalties(cand, make_score(80.0), CONFIG)
    assert score.final_total == 20.0  # 80 - 60 (teto)
    assert any("excederam o teto" in w for w in warnings)


def test_score_never_goes_below_zero():
    cand = make_candidate([RiskFlag(name="mercado_saturado", description="x")])
    score, _ = apply_penalties(cand, make_score(5.0), CONFIG)
    assert score.final_total == 0.0
