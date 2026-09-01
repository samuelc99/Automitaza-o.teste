"""Modelos do Content Engine (fatia mínima de validação dos Módulos 4/6 do
BLUEPRINT.md — Offer/Creative — não é a visão completa deles, é o suficiente
pra produzir um vídeo real a partir do que o Opportunity Engine já pesquisou).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Scene:
    on_screen_text: str
    narration_text: str
    search_query: str
    """Termo de busca de B-roll (Pexels/Pixabay funcionam melhor em inglês)."""
    kind: str  # "hook" | "fact" | "objection" | "cta"


@dataclass
class VideoScript:
    candidate_name: str
    scenes: list[Scene]
    caption: str
    """Legenda/descrição sugerida para o post no TikTok."""


@dataclass
class StockClip:
    url: str
    """URL direta do arquivo de vídeo (download)."""
    source_name: str
    source_page_url: str
    width: int
    height: int
    attribution: Optional[str] = None
    """Nome do criador original — Pexels/Pixabay não exigem crédito, mas
    registramos mesmo assim por transparência/auditoria (Seção 40)."""


@dataclass
class RenderedScene:
    scene: Scene
    clip: StockClip
    video_path: str
    narration_path: str
    duration_seconds: float


@dataclass
class RenderedVideo:
    candidate_name: str
    output_path: str
    caption: str
    scenes: list[RenderedScene] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
