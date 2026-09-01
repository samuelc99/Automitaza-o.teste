from poe.affiliate.models import CommissionInfo, CommissionType, DataStatus, TrackedValue
from poe.affiliate.network import AffiliateNetwork
from poe.affiliate.run import build_affiliate_offers
from poe.models import PriceInfo, ProductCandidate


class FakeNetwork(AffiliateNetwork):
    name = "fake_network"

    def __init__(self, known_names):
        self.known_names = known_names

    def lookup_commission(self, candidate):
        if candidate.name not in self.known_names:
            return None
        return CommissionInfo(
            network_name="Fake",
            commission_type=CommissionType.PERCENTUAL,
            commission_percent=TrackedValue(0.10, DataStatus.CONFIRMADO),
        )


def make_candidate(name):
    return ProductCandidate(name=name, category="c", seed_keyword="", price=PriceInfo(min_brl=100.0))


def test_build_offers_skips_candidates_without_match():
    candidates = [make_candidate("Produto A"), make_candidate("Produto B")]
    network = FakeNetwork(known_names={"Produto A"})

    offers, warnings = build_affiliate_offers(candidates, network)

    assert len(offers) == 1
    assert offers[0].candidate.name == "Produto A"
    assert offers[0].estimate.gross_commission_brl == 10.0
    assert len(warnings) == 1
    assert "Produto B" in warnings[0]


def test_build_offers_empty_when_no_matches():
    candidates = [make_candidate("Produto X")]
    network = FakeNetwork(known_names=set())

    offers, warnings = build_affiliate_offers(candidates, network)

    assert offers == []
    assert len(warnings) == 1
