"""Texto-pra-voz para a narração das cenas.

edge-tts usa as vozes neurais gratuitas do Microsoft Edge — sem API key,
sem cadastro, qualidade boa. Adaptador (mesmo padrão do resto do projeto)
pra poder trocar por outro provedor depois sem mudar o resto do pipeline.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path


class TTSError(Exception):
    pass


class TTSProvider(ABC):
    name: str

    @abstractmethod
    def synthesize(self, text: str, output_path: str | Path) -> None:
        """Gera um arquivo de áudio com a narração de `text` em `output_path`."""
        raise NotImplementedError


class EdgeTTSProvider(TTSProvider):
    name = "edge-tts"

    def __init__(self, voice: str = "pt-BR-FranciscaNeural"):
        self.voice = voice

    def synthesize(self, text: str, output_path: str | Path) -> None:
        try:
            import edge_tts
        except ImportError as e:
            raise TTSError(
                "Pacote 'edge-tts' não instalado. Rode: pip install edge-tts"
            ) from e

        async def _run():
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(str(output_path))

        try:
            asyncio.run(_run())
        except Exception as e:
            raise TTSError(f"Falha ao gerar narração via edge-tts: {e}") from e
