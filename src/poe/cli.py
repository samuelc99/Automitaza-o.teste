"""CLI do Product Opportunity Engine.

Uso:
    python -m poe.cli run data/evidence_2026-08-31.json
    python -m poe.cli run data/evidence_2026-08-31.json --meli-trends
    python -m poe.cli history
"""

from __future__ import annotations

import argparse
import sys

from poe.config_env import load_env
from poe.pipeline.run import run_pipeline
from poe.storage.db import HistoryStore
from poe.affiliate.models import DataStatus


def cmd_run(args: argparse.Namespace) -> None:
    enrichers = []
    if args.meli_trends:
        from poe.collectors.mercadolivre import build_meli_trends_source_from_env

        source = build_meli_trends_source_from_env(category_id=args.meli_category)
        if source is not None:
            enrichers.append(source)

    result = run_pipeline(
        args.evidence_file, config_path=args.config, db_path=args.db, enrichers=enrichers or None
    )

    print(f"\n=== Execução (run_id={result.run_id}) ===")
    print(f"Candidatos aprovados e pontuados: {len(result.scored) - len(result.eliminated)}")
    print(f"Candidatos eliminados: {len(result.eliminated)}")

    if result.run_log.source_calls:
        print("\n--- Fontes consultadas ---")
        for call in result.run_log.source_calls:
            print(f"  {call.as_log_line()}")

    if result.warnings:
        print("\n--- Avisos do pipeline ---")
        for w in result.warnings:
            print(f"  ! {w}")

    print("\n--- Ranking (por score final) ---")
    for sp in result.scored:
        status = "ELIMINADO" if sp.eliminated else ""
        reason = f" [{sp.elimination_reason}]" if sp.eliminated else ""
        print(
            f"  {sp.score.final_total:6.1f} pts | {sp.confidence.value:6s} | "
            f"{sp.candidate.name} {status}{reason}"
        )


def cmd_affiliate(args: argparse.Namespace) -> None:
    from poe.affiliate.manual_source import AffiliateInfoFileCollector
    from poe.affiliate.run import build_affiliate_offers
    from poe.collectors.evidence_file import EvidenceFileCollector

    candidates = EvidenceFileCollector(args.evidence_file).collect()
    network = AffiliateInfoFileCollector(args.affiliate_file)
    offers, warnings = build_affiliate_offers(candidates, network)

    print(f"\n=== Affiliate Economics ({len(offers)}/{len(candidates)} candidatos com oferta encontrada) ===\n")
    for offer in offers:
        est = offer.estimate
        gross = f"R${est.gross_commission_brl:.2f}" if est.gross_commission_brl is not None else "?"
        net = f"R${est.net_commission_brl:.2f}" if est.net_commission_brl is not None else "?"
        badge = {
            DataStatus.CONFIRMADO: "CONFIRMADO",
            DataStatus.ESTIMADO: "ESTIMADO",
            DataStatus.DESCONHECIDO: "DESCONHECIDO",
        }[est.status]
        print(f"  {offer.candidate.name}")
        print(f"    Rede: {offer.commission.network_name} | Status: {badge}")
        print(f"    Comissão bruta: {gross} | líquida: {net}")
        print(f"    Base do cálculo: {est.basis}")
        if offer.commission.restrictions:
            print(f"    Restrições: {'; '.join(offer.commission.restrictions)}")
        print()

    if warnings:
        print("--- Sem oferta de afiliado encontrada ---")
        for w in warnings:
            print(f"  ! {w}")


def cmd_history(args: argparse.Namespace) -> None:
    store = HistoryStore(args.db)

    print("--- Produtos recorrentes (apareceram em >=2 execuções) ---")
    recurring = store.recurring_products(min_appearances=2)
    if not recurring:
        print("  Nenhum ainda (é necessário rodar o pipeline mais de uma vez).")
    for r in recurring:
        print(
            f"  {r['name_normalized']}: {r['appearances']} execuções, "
            f"score médio {r['avg_score']:.1f}, máximo {r['max_score']:.1f}"
        )

    print("\n--- Categorias por score médio ---")
    for c in store.top_categories():
        print(f"  {c['category']}: {c['n']} produto(s), score médio {c['avg_score']:.1f}")


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    load_env()

    parser = argparse.ArgumentParser(description="Product Opportunity Engine")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--db", default="data/history.db")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Roda o pipeline sobre um arquivo de evidências")
    p_run.add_argument("evidence_file")
    p_run.add_argument(
        "--meli-trends",
        action="store_true",
        help="Enriquece candidatos com a API oficial de tendências do Mercado Livre "
        "(requer MELI_CLIENT_ID/MELI_CLIENT_SECRET/MELI_REFRESH_TOKEN no ambiente/.env). "
        "Opt-in — sem esta flag, o comportamento é idêntico ao modo manual.",
    )
    p_run.add_argument(
        "--meli-category",
        default=None,
        help="ID de categoria do Mercado Livre (ex.: MLB1430) para tendências específicas de categoria. "
        "Sem isso, usa tendências do site inteiro (MLB).",
    )
    p_run.set_defaults(func=cmd_run)

    p_hist = sub.add_parser("history", help="Consulta o histórico acumulado")
    p_hist.set_defaults(func=cmd_history)

    p_aff = sub.add_parser(
        "affiliate", help="Calcula comissão bruta/líquida por candidato a partir de um arquivo de comissões"
    )
    p_aff.add_argument("evidence_file")
    p_aff.add_argument("affiliate_file")
    p_aff.set_defaults(func=cmd_affiliate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
