import json

import pytest

from poe.affiliate.manual_source import AffiliateInfoFileCollector, AffiliateInfoValidationError
from poe.models import PriceInfo, ProductCandidate

OFFERS = {
    "offers": [
        {
            "match": {"candidate_name": "Bebedouro Automático Para Gatos"},
            "network_name": "Amazon Associates",
            "commission_type": "percentual",
            "commission_percent": {"value": 0.08, "status": "CONFIRMADO", "source_url": "https://x.com"},
            "cookie_duration_days": {"value": 24, "status": "CONFIRMADO"},
            "category": "pet",
        },
        {
            "match": {"category": "beleza"},
            "network_name": "Rede Beleza Afiliados",
            "commission_type": "percentual",
            "commission_percent": {"value": 0.12, "status": "ESTIMADO", "note": "estimado a partir de categoria similar"},
        },
    ]
}


def make_candidate(name, category):
    return ProductCandidate(name=name, category=category, seed_keyword="", price=PriceInfo(min_brl=50.0))


@pytest.fixture
def offers_file(tmp_path):
    path = tmp_path / "affiliate.json"
    path.write_text(json.dumps(OFFERS), encoding="utf-8")
    return path


def test_match_by_candidate_name(offers_file):
    collector = AffiliateInfoFileCollector(offers_file)
    cand = make_candidate("bebedouro automático para gatos", "pet / higiene")  # case/acento diferente de propósito

    commission = collector.lookup_commission(cand)

    assert commission is not None
    assert commission.network_name == "Amazon Associates"
    assert commission.commission_percent.value == 0.08


def test_match_by_category_fallback(offers_file):
    collector = AffiliateInfoFileCollector(offers_file)
    cand = make_candidate("Sérum Vitamina C Qualquer Marca", "beleza")

    commission = collector.lookup_commission(cand)

    assert commission is not None
    assert commission.network_name == "Rede Beleza Afiliados"


def test_no_match_returns_none(offers_file):
    collector = AffiliateInfoFileCollector(offers_file)
    cand = make_candidate("Produto Totalmente Diferente", "categoria-inexistente")

    assert collector.lookup_commission(cand) is None


def test_missing_file_raises_clear_error(tmp_path):
    collector = AffiliateInfoFileCollector(tmp_path / "nao-existe.json")
    cand = make_candidate("X", "Y")

    with pytest.raises(AffiliateInfoValidationError, match="não encontrado"):
        collector.lookup_commission(cand)


def test_missing_commission_type_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"offers": [{"match": {"category": "x"}, "network_name": "N"}]}), encoding="utf-8")
    collector = AffiliateInfoFileCollector(path)
    cand = make_candidate("X", "x")

    with pytest.raises(AffiliateInfoValidationError, match="commission_type"):
        collector.lookup_commission(cand)


def test_missing_match_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps({"offers": [{"network_name": "N", "commission_type": "percentual"}]}), encoding="utf-8"
    )
    collector = AffiliateInfoFileCollector(path)
    cand = make_candidate("X", "x")

    with pytest.raises(AffiliateInfoValidationError, match="match"):
        collector.lookup_commission(cand)


def test_unknown_fields_default_to_desconhecido(offers_file):
    collector = AffiliateInfoFileCollector(offers_file)
    cand = make_candidate("bebedouro automático para gatos", "pet")

    commission = collector.lookup_commission(cand)

    assert not commission.epc_brl.is_known()
    assert not commission.direct_costs_brl.is_known()
    assert not commission.commission_fixed_brl.is_known()
