"""Gerador do relatório TOP 5 no formato da Seção 23.

Este módulo só formata. As decisões de qual produto ficou em qual posição, e
por quê (Seção 14 exige julgamento crítico, não só ranquear por score), e as
narrativas de "melhor oportunidade" / "maior risco" / "próximo passo" (Seções
15, 22-23) devem ser escritas por quem revisa os candidatos — o
`ReportEntry.motivo_top5` é obrigatório e não tem valor default de propósito:
força uma decisão explícita em vez de um texto genérico gerado por código.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from poe.models import ScoredProduct

_MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]


@dataclass
class ReportEntry:
    scored: ScoredProduct
    motivo_top5: str
    riscos_destacados: list[str] = field(default_factory=list)


@dataclass
class BestOpportunity:
    nome: str
    motivo: str
    pontos_fortes: list[str]
    pontos_fracos: list[str]
    informacoes_faltando: list[str]
    principal_risco: str
    proximo_teste: str


def _fmt_price(candidate) -> str:
    p = candidate.price
    if p.max_brl and p.max_brl != p.min_brl:
        return f"R${p.min_brl:.2f} - R${p.max_brl:.2f}"
    return f"R${p.min_brl:.2f}"


def _fmt_dimension_line(scored: ScoredProduct, dim_name: str) -> str:
    for ds in scored.score.dimension_scores:
        if ds.dimension.value == dim_name:
            return f"{ds.points:.1f}/{ds.max_points:.0f} — {ds.rationale}"
    return "Dados insuficientes para confirmar."


def _render_entry(rank: int, entry: ReportEntry) -> str:
    sp = entry.scored
    cand = sp.candidate
    medal = _MEDALS[rank] if rank < len(_MEDALS) else f"{rank + 1}º"

    lines = [
        f"## {medal} {cand.name}",
        "",
        f"**Score:** {sp.score.final_total:.1f}/100 (bruto: {sp.score.raw_total:.1f}, "
        f"penalidades: -{sp.score.raw_total - sp.score.final_total:.1f})",
        f"**Confiança:** {sp.confidence.value} — {sp.confidence_rationale}",
        f"**Categoria:** {cand.category}",
        f"**Preço:** {_fmt_price(cand)} "
        f"({cand.price.evidence_type.value}{', fonte: ' + cand.price.source_url if cand.price.source_url else ''})",
        f"**Demanda:** {_fmt_dimension_line(sp, 'demanda')}",
        f"**Crescimento:** {_fmt_dimension_line(sp, 'crescimento')}",
        f"**Concorrência:** {_fmt_dimension_line(sp, 'concorrencia')}",
        f"**Margem:** {_fmt_dimension_line(sp, 'margem')}",
        f"**Logística:** {_fmt_dimension_line(sp, 'logistica')}",
        f"**Marketing:** {_fmt_dimension_line(sp, 'marketing')}",
        f"**Risco:** {_fmt_dimension_line(sp, 'risco')}",
        "",
        "### Por que está aqui?",
        entry.motivo_top5,
        "",
        "### Evidências",
    ]

    if cand.evidences:
        for ev in cand.evidences:
            src = f" ([{ev.source_name or 'fonte'}]({ev.source_url}))" if ev.source_url else (
                f" ({ev.source_name})" if ev.source_name else ""
            )
            lines.append(f"- **[{ev.evidence_type.value}/{ev.dimension.value}]** {ev.claim}{src}")
    else:
        lines.append("- Dados insuficientes para confirmar.")

    lines += ["", "### Riscos"]
    all_risks = list(entry.riscos_destacados)
    for rf in cand.risk_flags:
        all_risks.append(f"{rf.name} (severidade {rf.severity}): {rf.description}")
    for note in sp.audit_notes:
        all_risks.append(f"[auditoria] {note}")
    if all_risks:
        lines += [f"- {r}" for r in all_risks]
    else:
        lines.append("- Nenhum risco relevante identificado nas evidências coletadas.")

    lines += ["", "### Ideias de marketing"]
    ma = cand.marketing_analysis or {}
    if ma.get("hooks"):
        lines.append("**Hooks possíveis:**")
        lines += [f"- {h}" for h in ma["hooks"]]
    if ma.get("first_second"):
        lines.append(f"\n**Primeiro segundo do anúncio:** {ma['first_second']}")
    if ma.get("objections"):
        lines.append("\n**Objeções e respostas:**")
        for o in ma["objections"]:
            lines.append(f"- *{o.get('objection')}* → {o.get('response')}")
    if not ma:
        lines.append("Dados insuficientes para confirmar — análise de marketing não coletada.")

    lines.append("")
    return "\n".join(lines)


def render_report(
    entries: list[ReportEntry],
    best: BestOpportunity,
    biggest_risk: str,
    next_step: str,
) -> str:
    out = ["# TOP 5 OPORTUNIDADES", ""]
    for i, entry in enumerate(entries):
        out.append(_render_entry(i, entry))
        out.append("---")
        out.append("")

    out += [
        "# 🏆 MELHOR OPORTUNIDADE",
        "",
        f"## {best.nome}",
        "",
        best.motivo,
        "",
        "**Pontos fortes:**",
        *[f"- {p}" for p in best.pontos_fortes],
        "",
        "**Pontos fracos:**",
        *[f"- {p}" for p in best.pontos_fracos],
        "",
        "**Informações ainda faltando:**",
        *[f"- {p}" for p in best.informacoes_faltando],
        "",
        f"**Principal risco:** {best.principal_risco}",
        "",
        f"**Próximo teste recomendado:** {best.proximo_teste}",
        "",
        "# ⚠️ MAIOR RISCO",
        "",
        biggest_risk,
        "",
        "# 🔎 PRÓXIMO PASSO",
        "",
        next_step,
        "",
    ]

    return "\n".join(out)
