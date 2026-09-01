from poe.collectors.base import match_keyword
from poe.collectors.mercadolivre import MercadoLivreTrendsSource, parse_trends_response, _segment_for_index
from poe.collectors.meli_auth import MeliAuthClient, MeliAuthError
from poe.models import Dimension, EvidenceType, PriceInfo, ProductCandidate


class FakeAuth:
    def __init__(self, token="FAKE_TOKEN", raise_error=None):
        self._token = token
        self._raise_error = raise_error

    def get_access_token(self):
        if self._raise_error:
            raise self._raise_error
        return self._token


def make_http_get(responses):
    calls = []

    def fake_get(url, headers):
        calls.append((url, headers))
        return responses[len(calls) - 1]

    fake_get.calls = calls
    return fake_get


def make_candidate(name, seed_keyword=""):
    return ProductCandidate(
        name=name, category="c", seed_keyword=seed_keyword, price=PriceInfo(min_brl=50.0)
    )


# --- parse_trends_response / segmentação ---


def test_segment_boundaries():
    assert _segment_for_index(0) == "maior_crescimento"
    assert _segment_for_index(9) == "maior_crescimento"
    assert _segment_for_index(10) == "mais_buscado"
    assert _segment_for_index(29) == "mais_buscado"
    assert _segment_for_index(30) == "mais_popular"
    assert _segment_for_index(49) == "mais_popular"


def test_parse_trends_response_skips_items_without_keyword():
    raw = [{"keyword": "fone bluetooth", "url": "https://x"}, {"url": "https://y"}]
    parsed = parse_trends_response(raw)
    assert len(parsed) == 1
    assert parsed[0].keyword == "fone bluetooth"


# --- match_keyword ---


def test_match_keyword_substring_both_directions():
    cand = make_candidate("Bebedouro automático para gatos", seed_keyword="bebedouro automático gato")
    assert match_keyword("bebedouro automatico", cand)
    assert match_keyword("Bebedouro Automático Para Gatos Furacão Pet", cand)


def test_match_keyword_no_match():
    cand = make_candidate("Mini liquidificador portátil", seed_keyword="mini liquidificador")
    assert not match_keyword("sérum vitamina c", cand)


# --- MercadoLivreTrendsSource.enrich ---


def test_enrich_adds_evidence_on_match():
    responses = [(200, [{"keyword": "bebedouro automatico gato", "url": "https://ml/x"}])]
    source = MercadoLivreTrendsSource(auth=FakeAuth(), http_get=make_http_get(responses), backoff_seconds=0)
    cand = make_candidate("Bebedouro automático para gatos", seed_keyword="bebedouro automático gato")

    result = source.enrich([cand])

    assert result.evidences_added == 1
    assert result.candidates_matched == 1
    assert len(cand.evidences) == 1
    ev = cand.evidences[0]
    assert ev.evidence_type == EvidenceType.DADO
    assert ev.dimension == Dimension.CRESCIMENTO  # posição 0 = segmento maior_crescimento
    assert ev.value == 1.0


def test_enrich_no_match_adds_nothing():
    responses = [(200, [{"keyword": "panela eletrica", "url": "https://ml/x"}])]
    source = MercadoLivreTrendsSource(auth=FakeAuth(), http_get=make_http_get(responses), backoff_seconds=0)
    cand = make_candidate("Sérum vitamina C", seed_keyword="sérum vitamina c")

    result = source.enrich([cand])

    assert result.evidences_added == 0
    assert result.candidates_matched == 0
    assert cand.evidences == []


def test_enrich_handles_auth_error_gracefully():
    source = MercadoLivreTrendsSource(
        auth=FakeAuth(raise_error=MeliAuthError("token expirado")), http_get=make_http_get([]), backoff_seconds=0
    )
    cand = make_candidate("Produto")

    result = source.enrich([cand])

    assert result.evidences_added == 0
    assert result.skipped_reason is not None
    assert "autenticação" in result.skipped_reason.lower()
    assert cand.evidences == []  # não quebrou, não poluiu o candidato


def test_enrich_handles_invalid_response_shape():
    responses = [(200, {"not": "a list"})]
    source = MercadoLivreTrendsSource(auth=FakeAuth(), http_get=make_http_get(responses), backoff_seconds=0)
    cand = make_candidate("Produto")

    result = source.enrich([cand])

    assert result.evidences_added == 0
    assert result.skipped_reason is not None


def test_enrich_handles_empty_trends_list():
    responses = [(200, [])]
    source = MercadoLivreTrendsSource(auth=FakeAuth(), http_get=make_http_get(responses), backoff_seconds=0)
    cand = make_candidate("Produto")

    result = source.enrich([cand])

    assert result.evidences_added == 0
    assert result.skipped_reason is not None


def test_enrich_retries_once_on_429_then_succeeds():
    responses = [
        (429, {"message": "rate limited"}),
        (200, [{"keyword": "produto x", "url": "https://ml/x"}]),
    ]
    http_get = make_http_get(responses)
    source = MercadoLivreTrendsSource(auth=FakeAuth(), http_get=http_get, backoff_seconds=0, max_retries_on_429=1)
    cand = make_candidate("Produto X", seed_keyword="produto x")

    result = source.enrich([cand])

    assert len(http_get.calls) == 2
    assert result.evidences_added == 1


def test_enrich_gives_up_after_max_retries_on_429():
    responses = [(429, {"message": "rate limited"}), (429, {"message": "rate limited"})]
    source = MercadoLivreTrendsSource(
        auth=FakeAuth(), http_get=make_http_get(responses), backoff_seconds=0, max_retries_on_429=1
    )
    cand = make_candidate("Produto")

    result = source.enrich([cand])

    assert result.evidences_added == 0
    assert result.skipped_reason is not None
    assert "429" in result.skipped_reason


def test_enrich_handles_unexpected_http_error():
    responses = [(500, {"message": "internal error"})]
    source = MercadoLivreTrendsSource(auth=FakeAuth(), http_get=make_http_get(responses), backoff_seconds=0)
    cand = make_candidate("Produto")

    result = source.enrich([cand])

    assert result.evidences_added == 0
    assert result.skipped_reason is not None
    assert "500" in result.skipped_reason
