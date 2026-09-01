"""Busca de B-roll com licença de uso comercial verificada.

Pexels e Pixabay: uso comercial livre, sem exigência de crédito por vídeo
(confirmado nos termos de cada plataforma — ver README). Isso substitui a
ideia original (baixar corte de vídeo do YouTube), que tinha problema real
de direito autoral (ver README, seção Content Engine).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Callable, Optional

from poe.content.models import StockClip

HttpGet = Callable[[str, dict], tuple[int, object]]


class StockFootageError(Exception):
    pass


def _default_http_get(url: str, headers: dict, timeout: float = 15.0) -> tuple[int, object]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {}
        return e.code, body
    except urllib.error.URLError as e:
        raise StockFootageError(f"Falha de rede ao chamar {url}: {e}") from e


class StockFootageProvider(ABC):
    name: str

    @abstractmethod
    def search(self, query: str) -> Optional[StockClip]:
        """Retorna o melhor clipe encontrado para a busca, ou None (Seção 25 — nunca inventar)."""
        raise NotImplementedError


class PexelsProvider(StockFootageProvider):
    name = "pexels"
    _BASE_URL = "https://api.pexels.com/v1/videos/search"

    def __init__(self, api_key: str, http_get: Optional[HttpGet] = None):
        self.api_key = api_key
        self._http_get = http_get or _default_http_get

    def search(self, query: str) -> Optional[StockClip]:
        url = f"{self._BASE_URL}?{urllib.parse.urlencode({'query': query, 'orientation': 'portrait', 'per_page': 5})}"
        status, body = self._http_get(url, {"Authorization": self.api_key})
        if status != 200:
            raise StockFootageError(f"Pexels retornou HTTP {status}: {body}")

        videos = body.get("videos", [])
        if not videos:
            return None

        video = videos[0]
        best_file = _best_video_file(video.get("video_files", []))
        if best_file is None:
            return None

        return StockClip(
            url=best_file["link"],
            source_name="Pexels",
            source_page_url=video.get("url", ""),
            width=best_file.get("width", 0),
            height=best_file.get("height", 0),
            attribution=(video.get("user") or {}).get("name"),
        )


class PixabayProvider(StockFootageProvider):
    name = "pixabay"
    _BASE_URL = "https://pixabay.com/api/videos/"

    def __init__(self, api_key: str, http_get: Optional[HttpGet] = None):
        self.api_key = api_key
        self._http_get = http_get or _default_http_get

    def search(self, query: str) -> Optional[StockClip]:
        params = {"key": self.api_key, "q": query, "per_page": 5}
        url = f"{self._BASE_URL}?{urllib.parse.urlencode(params)}"
        status, body = self._http_get(url, {})
        if status != 200:
            raise StockFootageError(f"Pixabay retornou HTTP {status}: {body}")

        hits = body.get("hits", [])
        if not hits:
            return None

        hit = hits[0]
        videos = hit.get("videos", {})
        best = videos.get("large") or videos.get("medium") or videos.get("small")
        if not best:
            return None

        return StockClip(
            url=best["url"],
            source_name="Pixabay",
            source_page_url=hit.get("pageURL", ""),
            width=best.get("width", 0),
            height=best.get("height", 0),
            attribution=hit.get("user"),
        )


def _best_video_file(video_files: list[dict]) -> Optional[dict]:
    """Prefere vertical (retrato) e qualidade hd/sd, nessa ordem."""
    if not video_files:
        return None
    portrait = [f for f in video_files if f.get("height", 0) > f.get("width", 0)]
    candidates = portrait or video_files
    hd = [f for f in candidates if f.get("quality") == "hd"]
    return (hd or candidates)[0]
