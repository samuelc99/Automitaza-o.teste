"""Collector que carrega candidatos a partir de um arquivo JSON de evidências.

Este é o mecanismo principal de entrada de dados reais no MVP: como Mercado
Livre e Amazon.com.br bloqueiam explicitamente crawlers de IA via robots.txt,
e a Shopee só entrega dados via JS (sem HTML estático utilizável), a coleta
de evidências reais é feita pelo agente via WebSearch/WebFetch em sessão
interativa, e o resultado é salvo neste formato JSON. O pipeline determinístico
(normalização, score, auditoria, histórico) roda por cima disso.

Ver data/evidence_template.json para o schema esperado.
"""

from __future__ import annotations

import json
from pathlib import Path

from poe.collectors.base import EvidenceSource
from poe.models import Evidence, EvidenceType, Dimension, PriceInfo, ProductCandidate, RiskFlag


class EvidenceFileValidationError(Exception):
    pass


class EvidenceFileCollector(EvidenceSource):
    name = "evidence_file"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def collect(self) -> list[ProductCandidate]:
        if not self.path.exists():
            raise EvidenceFileValidationError(f"Arquivo de evidências não encontrado: {self.path}")

        raw = json.loads(self.path.read_text(encoding="utf-8"))
        candidates: list[ProductCandidate] = []

        for i, item in enumerate(raw.get("candidates", [])):
            candidates.append(self._parse_candidate(item, index=i))

        return candidates

    def _parse_candidate(self, item: dict, index: int) -> ProductCandidate:
        try:
            price_raw = item["price_brl"]
            price = PriceInfo(
                min_brl=float(price_raw["min"]),
                max_brl=float(price_raw["max"]) if price_raw.get("max") is not None else None,
                evidence_type=EvidenceType(price_raw.get("type", "DADO")),
                source_url=price_raw.get("source_url"),
                note=price_raw.get("note"),
            )
        except KeyError as e:
            raise EvidenceFileValidationError(
                f"candidates[{index}] ({item.get('name', '?')}): campo obrigatório ausente em price_brl: {e}"
            )
        except ValueError as e:
            raise EvidenceFileValidationError(f"candidates[{index}]: {e}")

        evidences: list[Evidence] = []
        for j, ev in enumerate(item.get("evidences", [])):
            try:
                evidences.append(
                    Evidence(
                        dimension=Dimension(ev["dimension"]),
                        claim=ev["claim"],
                        evidence_type=EvidenceType(ev["type"]),
                        strength=float(ev.get("strength", 0.5)),
                        source_name=ev.get("source_name"),
                        source_url=ev.get("source_url"),
                        collected_at=ev.get("collected_at"),
                        note=ev.get("note"),
                        value=ev.get("value"),
                        unit=ev.get("unit"),
                        methodology=ev.get("methodology"),
                    )
                )
            except KeyError as e:
                raise EvidenceFileValidationError(
                    f"candidates[{index}].evidences[{j}]: campo obrigatório ausente: {e}"
                )
            except ValueError as e:
                raise EvidenceFileValidationError(f"candidates[{index}].evidences[{j}]: {e}")

        risk_flags = [
            RiskFlag(name=rf["name"], description=rf["description"], severity=rf.get("severity", "media"))
            for rf in item.get("risk_flags", [])
        ]

        if not item.get("name"):
            raise EvidenceFileValidationError(f"candidates[{index}]: campo 'name' é obrigatório")
        if not item.get("category"):
            raise EvidenceFileValidationError(f"candidates[{index}] ({item['name']}): campo 'category' é obrigatório")

        return ProductCandidate(
            name=item["name"],
            category=item["category"],
            seed_keyword=item.get("seed_keyword", ""),
            price=price,
            evidences=evidences,
            risk_flags=risk_flags,
            hard_flags=item.get("hard_flags", []),
            notes=item.get("notes"),
            marketing_analysis=item.get("marketing_analysis"),
            competition_analysis=item.get("competition_analysis"),
            margin_analysis=item.get("margin_analysis"),
        )
