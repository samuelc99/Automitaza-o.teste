"""Monta o vídeo final via ffmpeg: baixa B-roll, gera narração, sobrepõe
texto na tela, e concatena as cenas — formato vertical (1080x1920, padrão
TikTok).

Requer ffmpeg/ffprobe no PATH. Não tenta reimplementar processamento de
vídeo em Python — ffmpeg já faz isso bem, só orquestramos.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

from poe.content.models import RenderedScene, RenderedVideo, Scene, VideoScript
from poe.content.stock_footage import StockFootageProvider
from poe.content.tts import TTSProvider

WIDTH = 1080
HEIGHT = 1920
_DEFAULT_FONT = r"C:\Windows\Fonts\arial.ttf"
_MIN_SCENE_SECONDS = 2.5


class VideoBuildError(Exception):
    pass


def _require_ffmpeg() -> None:
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise VideoBuildError(f"'{tool}' não encontrado no PATH. Instale o ffmpeg antes de usar este módulo.")


def _download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)


def _ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise VideoBuildError(f"ffprobe falhou em {path}: {result.stderr}")
    return float(result.stdout.strip())


def _render_scene(
    scene: Scene,
    clip_path: Path,
    narration_path: Path,
    out_path: Path,
    text_file: Path,
    font_path: str,
) -> float:
    narration_duration = max(_ffprobe_duration(narration_path), _MIN_SCENE_SECONDS)
    text_file.write_text(scene.on_screen_text, encoding="utf-8")

    vf = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        f"drawtext=textfile='{text_file.as_posix()}':fontfile='{Path(font_path).as_posix()}':"
        f"fontsize=64:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=24:"
        f"x=(w-text_w)/2:y=h*0.72:line_spacing=12"
    )

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(clip_path),
        "-i", str(narration_path),
        "-vf", vf,
        "-map", "0:v", "-map", "1:a",
        "-t", f"{narration_duration:.2f}",
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise VideoBuildError(f"ffmpeg falhou na cena '{scene.kind}': {result.stderr[-2000:]}")
    return narration_duration


def _concat_scenes(scene_video_paths: list[Path], out_path: Path, work_dir: Path) -> None:
    filelist = work_dir / "filelist.txt"
    filelist.write_text("\n".join(f"file '{p.as_posix()}'" for p in scene_video_paths), encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(filelist), "-c", "copy", str(out_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise VideoBuildError(f"ffmpeg falhou ao concatenar cenas: {result.stderr[-2000:]}")


def build_video(
    script: VideoScript,
    footage_provider: StockFootageProvider,
    tts_provider: TTSProvider,
    output_path: str | Path,
    font_path: str = _DEFAULT_FONT,
    work_dir: Optional[str | Path] = None,
) -> RenderedVideo:
    _require_ffmpeg()
    if not Path(font_path).exists():
        raise VideoBuildError(f"Fonte não encontrada: {font_path}")

    warnings: list[str] = []
    tmp_ctx = tempfile.TemporaryDirectory() if work_dir is None else None
    work = Path(work_dir) if work_dir else Path(tmp_ctx.name)
    work.mkdir(parents=True, exist_ok=True)

    try:
        rendered_scenes: list[RenderedScene] = []
        scene_video_paths: list[Path] = []

        for i, scene in enumerate(script.scenes):
            clip = footage_provider.search(scene.search_query)
            if clip is None:
                warnings.append(f"Cena {i} ('{scene.kind}'): nenhum B-roll encontrado para '{scene.search_query}', cena pulada.")
                continue

            clip_path = work / f"clip_{i}.mp4"
            narration_path = work / f"narration_{i}.mp3"
            scene_out = work / f"scene_{i}.mp4"
            text_file = work / f"text_{i}.txt"

            _download(clip.url, clip_path)
            tts_provider.synthesize(scene.narration_text, narration_path)
            duration = _render_scene(scene, clip_path, narration_path, scene_out, text_file, font_path)

            rendered_scenes.append(
                RenderedScene(
                    scene=scene,
                    clip=clip,
                    video_path=str(scene_out),
                    narration_path=str(narration_path),
                    duration_seconds=duration,
                )
            )
            scene_video_paths.append(scene_out)

        if not scene_video_paths:
            raise VideoBuildError("Nenhuma cena foi renderizada — nenhum B-roll encontrado para nenhuma busca.")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _concat_scenes(scene_video_paths, output_path, work)

        return RenderedVideo(
            candidate_name=script.candidate_name,
            output_path=str(output_path),
            caption=script.caption,
            scenes=rendered_scenes,
            warnings=warnings,
        )
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()
