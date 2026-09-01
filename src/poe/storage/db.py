"""Histórico persistente (Seção 17).

Permite responder, ao longo do tempo:
- quais produtos apareceram várias vezes;
- como o score de um produto mudou entre execuções;
- quais categorias aparecem mais no top do ranking.

SQLite simples e sem dependências externas — suficiente para o volume de
dados de um sistema de pesquisa manual/assistido. Migrar para Postgres é
trivial depois se o volume crescer (mesmo schema).
"""

from __future__ import annotations

import sqlite3
import unicodedata
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from poe.models import ScoredProduct

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT NOT NULL,
    seed_keywords TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    category TEXT,
    price_min REAL,
    price_max REAL,
    score_raw REAL,
    score_final REAL,
    confidence TEXT,
    eliminated INTEGER NOT NULL DEFAULT 0,
    elimination_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_products_name_normalized ON products(name_normalized);

CREATE TABLE IF NOT EXISTS risk_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    name TEXT,
    severity TEXT
);

CREATE TABLE IF NOT EXISTS evidences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    dimension TEXT,
    evidence_type TEXT,
    claim TEXT,
    strength REAL,
    value REAL,
    unit TEXT,
    source_name TEXT,
    source_url TEXT,
    collected_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_evidences_product_id ON evidences(product_id);
"""


def _normalize_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).strip().lower()


class HistoryStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def save_run(self, scored_products: list[ScoredProduct], seed_keywords: list[str], notes: str = "") -> int:
        with closing(sqlite3.connect(self.db_path)) as conn:
            cur = conn.execute(
                "INSERT INTO runs (run_at, seed_keywords, notes) VALUES (?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), ", ".join(seed_keywords), notes),
            )
            run_id = cur.lastrowid

            for sp in scored_products:
                cur = conn.execute(
                    """INSERT INTO products
                       (run_id, name, name_normalized, category, price_min, price_max,
                        score_raw, score_final, confidence, eliminated, elimination_reason)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run_id,
                        sp.candidate.name,
                        _normalize_name(sp.candidate.name),
                        sp.candidate.category,
                        sp.candidate.price.min_brl,
                        sp.candidate.price.max_brl,
                        sp.score.raw_total,
                        sp.score.final_total,
                        sp.confidence.value,
                        1 if sp.eliminated else 0,
                        sp.elimination_reason,
                    ),
                )
                product_id = cur.lastrowid
                for flag in sp.candidate.risk_flags:
                    conn.execute(
                        "INSERT INTO risk_flags (product_id, name, severity) VALUES (?, ?, ?)",
                        (product_id, flag.name, flag.severity),
                    )
                for ev in sp.candidate.evidences:
                    conn.execute(
                        """INSERT INTO evidences
                           (product_id, dimension, evidence_type, claim, strength, value, unit,
                            source_name, source_url, collected_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            product_id,
                            ev.dimension.value,
                            ev.evidence_type.value,
                            ev.claim,
                            ev.strength,
                            ev.value,
                            ev.unit,
                            ev.source_name,
                            ev.source_url,
                            ev.collected_at,
                        ),
                    )
            conn.commit()
            return run_id

    def history_for(self, product_name: str) -> list[dict]:
        norm = _normalize_name(product_name)
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT p.*, r.run_at FROM products p
                   JOIN runs r ON r.id = p.run_id
                   WHERE p.name_normalized = ?
                   ORDER BY r.run_at ASC""",
                (norm,),
            ).fetchall()
            return [dict(r) for r in rows]

    def evidence_history_for(self, product_name: str, dimension: str | None = None) -> list[dict]:
        """Evidências de um produto ao longo do tempo (T0 -> T1 -> T2...), ordenadas por execução.

        Base para detecção futura de tendência real (Seção 7) — não implementa
        nenhuma lógica de tendência aqui, só preserva o dado bruto no tempo.
        """
        norm = _normalize_name(product_name)
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            query = """SELECT e.*, p.name AS product_name, r.run_at
                       FROM evidences e
                       JOIN products p ON p.id = e.product_id
                       JOIN runs r ON r.id = p.run_id
                       WHERE p.name_normalized = ?"""
            params: list = [norm]
            if dimension:
                query += " AND e.dimension = ?"
                params.append(dimension)
            query += " ORDER BY r.run_at ASC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def recurring_products(self, min_appearances: int = 2) -> list[dict]:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT name_normalized, COUNT(DISTINCT run_id) AS appearances,
                          AVG(score_final) AS avg_score, MAX(score_final) AS max_score
                   FROM products
                   WHERE eliminated = 0
                   GROUP BY name_normalized
                   HAVING appearances >= ?
                   ORDER BY appearances DESC, avg_score DESC""",
                (min_appearances,),
            ).fetchall()
            return [dict(r) for r in rows]

    def top_categories(self, limit: int = 10) -> list[dict]:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT category, COUNT(*) AS n, AVG(score_final) AS avg_score
                   FROM products
                   WHERE eliminated = 0
                   GROUP BY category
                   ORDER BY avg_score DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
