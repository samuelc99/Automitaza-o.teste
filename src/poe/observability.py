"""Observabilidade (Seção 10).

Logger padrão da aplicação + registro estruturado por execução (JSONL), para
que seja possível responder no futuro "o sistema está realmente melhorando?"
comparando execuções: qual fonte foi consultada, quando, quantas evidências
voltaram, quantos erros, quanto tempo levou, quais produtos foram
descartados e por quê.
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("poe")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


@dataclass
class SourceCallLog:
    source_name: str
    started_at: str
    duration_seconds: float
    items_returned: int
    errors: list[str] = field(default_factory=list)
    skipped_reason: str | None = None

    def as_log_line(self) -> str:
        if self.skipped_reason:
            return f"[{self.source_name}] pulado: {self.skipped_reason}"
        err = f", {len(self.errors)} erro(s)" if self.errors else ""
        return (
            f"[{self.source_name}] {self.items_returned} item(ns) em "
            f"{self.duration_seconds:.2f}s{err}"
        )


@dataclass
class RunLog:
    run_started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_calls: list[SourceCallLog] = field(default_factory=list)
    candidates_found: int = 0
    candidates_eliminated: int = 0
    elimination_reasons: list[str] = field(default_factory=list)

    def record_source_call(self, log: SourceCallLog) -> None:
        self.source_calls.append(log)
        logger.info(log.as_log_line())

    def write_jsonl(self, path: str | Path = "data/logs/runs.jsonl") -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(self), ensure_ascii=False) + "\n")


@contextmanager
def timed_source_call(run_log: RunLog, source_name: str):
    """Uso: with timed_source_call(run_log, 'mercadolivre_trends') as ctx: ...

    `ctx` é um dict mutável — preencha ctx['items_returned'], ctx['errors'],
    ctx['skipped_reason'] dentro do bloco. O tempo e o registro no RunLog são
    automáticos, mesmo se o bloco lançar (o log ainda é gravado antes de
    propagar a exceção).
    """
    started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    ctx: dict = {"items_returned": 0, "errors": [], "skipped_reason": None}
    try:
        yield ctx
    finally:
        duration = time.monotonic() - t0
        log = SourceCallLog(
            source_name=source_name,
            started_at=started_at,
            duration_seconds=round(duration, 3),
            items_returned=ctx["items_returned"],
            errors=ctx["errors"],
            skipped_reason=ctx["skipped_reason"],
        )
        run_log.record_source_call(log)
