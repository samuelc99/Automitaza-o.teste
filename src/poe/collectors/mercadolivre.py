"""Fonte de evidência: Mercado Livre — endpoint oficial /trends.

Endpoint verificado na documentação oficial (developers.mercadolivre.com.br,
"Tendências", consultada em 2026-08-31, direto na fonte primária):

    GET https://api.mercadolibre.com/trends/{SITE_ID}
    GET https://api.mercadolibre.com/trends/{SITE_ID}/{CATEGORY_ID}
    Header: Authorization: Bearer $ACCESS_TOKEN

Devolve até 50 objetos {"keyword": ..., "url": ...}, atualizados
semanalmente: os 10 primeiros são os termos com MAIOR CRESCIMENTO de busca,
os 20 seguintes são os MAIS BUSCADOS, e os 20 últimos são os MAIS POPULARES
da semana. Isso é sinal real de demanda/crescimento de um TERMO DE BUSCA —
não é um produto com preço.

Por isso esta classe é um EvidenceEnricher, não um EvidenceSource: ela não
cria ProductCandidate (não tem preço nem identidade de produto para isso),
ela anexa Evidence a candidatos já existentes cujo nome/seed_keyword bate com
um termo em tendência (ver base.match_keyword).

O endpoint de busca livre por palavra-chave (/sites/$SITE_ID/search?q=...)
NÃO está mais documentado para uso geral — a doc atual só lista busca por
seller_id/nickname (catálogo de um vendedor específico). Por isso este
projeto não tenta obter preço/concorrência via API neste momento (ver
README.md - Limitações).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

from poe.collectors.base import EnrichmentResult, EvidenceEnricher, match_keyword
from poe.collectors.meli_auth import MeliAuthClient, MeliAuthError
from poe.models import Dimension, Evidence, EvidenceType, ProductCandidate

TRENDS_BASE_URL = "https://api.mercadolibre.com/trends"

HttpGet = Callable[[str, dict], tuple[int, object]]


class MeliApiError(Exception):
    """Erro não-fatal de chamada à API (rede, JSON inválido, status inesperado)."""


def _default_http_get(url: str, headers: dict, timeout: float = 15.0) -> tuple[int, object]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {"error": "unknown", "message": str(e)}
        return e.code, body
    except urllib.error.URLError as e:
        raise MeliApiError(f"Falha de rede ao chamar {url}: {e}") from e


@dataclass
class TrendItem:
    keyword: str
    url: Optional[str]
    segment: str  # "maior_crescimento" | "mais_buscado" | "mais_popular"
    rank: int  # posição 1-based dentro do segmento


def _segment_for_index(i: int) -> str:
    if i < 10:
        return "maior_crescimento"
    if i < 30:
        return "mais_buscado"
    return "mais_popular"


def parse_trends_response(raw_items: list[dict]) -> list[TrendItem]:
    parsed = []
    counters = {"maior_crescimento": 0, "mais_buscado": 0, "mais_popular": 0}
    for i, item in enumerate(raw_items[:50]):
        segment = _segment_for_index(i)
        counters[segment] += 1
        keyword = item.get("keyword", "")
        if not keyword:
            continue
        parsed.append(TrendItem(keyword=keyword, url=item.get("url"), segment=segment, rank=counters[segment]))
    return parsed


_SEGMENT_TO_DIMENSION = {
    "maior_crescimento": Dimension.CRESCIMENTO,
    "mais_buscado": Dimension.DEMANDA,
    "mais_popular": Dimension.DEMANDA,
}

_SEGMENT_STRENGTH = {
    "maior_crescimento": 0.75,
    "mais_buscado": 0.65,
    "mais_popular": 0.55,
}

_SEGMENT_LABEL = {
    "maior_crescimento": "maior crescimento de busca",
    "mais_buscado": "mais buscado",
    "mais_popular": "mais popular da semana",
}


class MercadoLivreTrendsSource(EvidenceEnricher):
    name = "mercadolivre_trends"

    def __init__(
        self,
        auth: MeliAuthClient,
        site_id: str = "MLB",
        category_id: Optional[str] = None,
        http_get: Optional[HttpGet] = None,
        base_url: str = TRENDS_BASE_URL,
        max_retries_on_429: int = 1,
        backoff_seconds: float = 2.0,
    ):
        self.auth = auth
        self.site_id = site_id
        self.category_id = category_id
        self._http_get = http_get or _default_http_get
        self._base_url = base_url
        self._max_retries_on_429 = max_retries_on_429
        self._backoff_seconds = backoff_seconds

    def _url(self) -> str:
        if self.category_id:
            return f"{self._base_url}/{self.site_id}/{self.category_id}"
        return f"{self._base_url}/{self.site_id}"

    def _fetch_raw(self) -> list[dict]:
        try:
            access_token = self.auth.get_access_token()
        except MeliAuthError as e:
            raise MeliApiError(f"Falha de autenticação: {e}") from e

        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        url = self._url()

        attempts = 0
        while True:
            status, body = self._http_get(url, headers)
            if status == 200:
                if not isinstance(body, list):
                    raise MeliApiError(f"Resposta inesperada de {url} (esperava lista, veio {type(body).__name__}).")
                return body
            if status == 429 and attempts < self._max_retries_on_429:
                attempts += 1
                if self._backoff_seconds > 0:
                    time.sleep(self._backoff_seconds)
                continue
            error_msg = body.get("message") if isinstance(body, dict) else str(body)
            raise MeliApiError(f"HTTP {status} ao chamar {url}: {error_msg}")

    def enrich(self, candidates: list[ProductCandidate]) -> EnrichmentResult:
        result = EnrichmentResult(source_name=self.name, candidates_checked=len(candidates))
        t0 = time.monotonic()

        try:
            raw_items = self._fetch_raw()
        except MeliApiError as e:
            result.skipped_reason = str(e)
            result.duration_seconds = time.monotonic() - t0
            return result

        trend_items = parse_trends_response(raw_items)
        if not trend_items:
            result.skipped_reason = "Resposta da API não continha termos de tendência (lista vazia)."
            result.duration_seconds = time.monotonic() - t0
            return result

        collected_at = datetime.now(timezone.utc).isoformat()
        matched_candidate_names: set[str] = set()

        for trend in trend_items:
            for cand in candidates:
                if not match_keyword(trend.keyword, cand):
                    continue
                dimension = _SEGMENT_TO_DIMENSION[trend.segment]
                evidence = Evidence(
                    dimension=dimension,
                    claim=(
                        f"Termo '{trend.keyword}' aparece na posição {trend.rank} do segmento "
                        f"'{_SEGMENT_LABEL[trend.segment]}' nas tendências oficiais do Mercado Livre "
                        f"({self.site_id}{'/' + self.category_id if self.category_id else ''})."
                    ),
                    evidence_type=EvidenceType.DADO,
                    strength=_SEGMENT_STRENGTH[trend.segment],
                    source_name="Mercado Livre Trends API (oficial)",
                    source_url=trend.url or f"https://api.mercadolibre.com/trends/{self.site_id}",
                    collected_at=collected_at,
                    value=float(trend.rank),
                    unit=f"posição no segmento '{trend.segment}' (1-{10 if trend.segment == 'maior_crescimento' else 20})",
                    methodology=(
                        "Mercado Livre Trends API oficial, atualização semanal. Casamento produto<->termo "
                        "por substring normalizada (heurística — pode haver falso positivo em termos genéricos)."
                    ),
                    note="Evidência anexada automaticamente por MercadoLivreTrendsSource.",
                )
                cand.evidences.append(evidence)
                result.evidences_added += 1
                matched_candidate_names.add(cand.name)

        result.candidates_matched = len(matched_candidate_names)
        result.duration_seconds = time.monotonic() - t0
        return result


def build_meli_trends_source_from_env(category_id: Optional[str] = None) -> Optional[MercadoLivreTrendsSource]:
    """Constrói a fonte a partir de variáveis de ambiente; None se faltar credencial.

    Uso típico no CLI/scripts: se voltar None, apenas não adicione a fonte à
    lista de enrichers — o pipeline continua funcionando normalmente em modo
    manual (Seção 5).
    """
    from poe.config_env import get_meli_credentials
    from poe.observability import logger

    creds = get_meli_credentials(required=False)
    if creds is None:
        logger.warning(
            "MELI_CLIENT_ID/MELI_CLIENT_SECRET/MELI_REFRESH_TOKEN não configurados — "
            "pulando fonte Mercado Livre Trends (modo manual continua ativo)."
        )
        return None

    auth = MeliAuthClient(
        client_id=creds.client_id, client_secret=creds.client_secret, refresh_token=creds.refresh_token
    )
    return MercadoLivreTrendsSource(auth=auth, site_id=creds.site_id, category_id=category_id)
