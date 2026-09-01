"""Gera o roteiro de um vídeo curto a partir do que o Opportunity Engine já
pesquisou (marketing_analysis de ProductCandidate) — não inventa gancho/
objeção novos, só reorganiza o que já foi levantado com evidência em
formato de cena (Seção 6/12 do BLUEPRINT.md — roteiro é original, não é
cópia de vídeo de terceiro, ver README sobre por que descartamos a ideia
de reaproveitar clipes do YouTube).
"""

from __future__ import annotations

import unicodedata

from poe.content.models import Scene, VideoScript
from poe.models import ProductCandidate

# Termos de busca em inglês tendem a achar mais B-roll no Pexels/Pixabay.
_CATEGORY_SEARCH_TERMS: dict[str, str] = {
    "pet": "cat drinking water pet",
    "cozinha": "kitchen gadget smoothie",
    "casa": "home cleaning floor",
    "limpeza": "cleaning floor mop",
    "beleza": "skincare routine face",
    "eletronicos": "wireless earphones lifestyle",
    "audio": "wireless earphones running",
}

_DEFAULT_SEARCH_TERM = "product unboxing lifestyle"


class ScriptGenerationError(Exception):
    pass


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).strip().lower()


def _guess_search_term(category: str) -> str:
    normalized = _normalize(category)
    for key, term in _CATEGORY_SEARCH_TERMS.items():
        if key in normalized:
            return term
    return _DEFAULT_SEARCH_TERM


def build_caption(candidate: ProductCandidate) -> str:
    hooks = (candidate.marketing_analysis or {}).get("hooks") or []
    first_line = hooks[0] if hooks else candidate.name
    return f"{first_line} 👀 Link na bio. #achadinhos #{_normalize(candidate.category).split('/')[0].strip().replace(' ', '')}"


def build_script(candidate: ProductCandidate) -> VideoScript:
    """Constrói um roteiro de cenas a partir do marketing_analysis já coletado.

    Levanta ScriptGenerationError se o candidato não tem marketing_analysis —
    isso é intencional: não geramos hook/objeção "genéricos" sem lastro
    (mesmo princípio de não inventar dado do Opportunity Engine).
    """
    ma = candidate.marketing_analysis
    if not ma or not ma.get("hooks"):
        raise ScriptGenerationError(
            f"'{candidate.name}' não tem marketing_analysis.hooks — rode a pesquisa do "
            f"Opportunity Engine primeiro (ver data/evidence_template.json)."
        )

    search_term = _guess_search_term(candidate.category)
    scenes: list[Scene] = []

    hooks = ma["hooks"]
    first_second = ma.get("first_second")
    scenes.append(
        Scene(
            on_screen_text=hooks[0],
            narration_text=first_second or hooks[0],
            search_query=search_term,
            kind="hook",
        )
    )

    for hook in hooks[1:3]:
        scenes.append(
            Scene(on_screen_text=hook, narration_text=hook, search_query=search_term, kind="fact")
        )

    objections = ma.get("objections") or []
    if objections:
        obj = objections[0]
        text = f"\"{obj.get('objection', '')}\""
        narration = obj.get("response", "")
        scenes.append(
            Scene(on_screen_text=text, narration_text=narration, search_query=search_term, kind="objection")
        )

    scenes.append(
        Scene(
            on_screen_text="Link na bio 🔗",
            narration_text="Deixei o link pra você conferir na bio.",
            search_query=search_term,
            kind="cta",
        )
    )

    return VideoScript(candidate_name=candidate.name, scenes=scenes, caption=build_caption(candidate))
