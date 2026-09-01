"""Cálculo de comissão bruta/líquida (BLUEPRINT.md, Seção 8):

    Comissão Bruta - Custos diretamente associados = Comissão Líquida

Não calcula CAC, ROI ou economia unitária completa (Seção 30) — isso depende
de dado de tráfego real que só existe a partir do Traffic Engine (fases bem
mais adiante). Este módulo só responde "quanto essa venda paga de comissão
segundo os termos publicados do programa".
"""

from __future__ import annotations

from poe.affiliate.models import CommissionEstimate, CommissionInfo, CommissionType, DataStatus, worst_status


def compute_gross_commission(price_brl: float, commission: CommissionInfo) -> CommissionEstimate:
    """Comissão bruta por venda, a partir do preço e dos termos do programa."""
    percent = commission.commission_percent
    fixed = commission.commission_fixed_brl

    if commission.commission_type == CommissionType.PERCENTUAL:
        if not percent.is_known():
            return CommissionEstimate(
                gross_commission_brl=None,
                net_commission_brl=None,
                status=DataStatus.DESCONHECIDO,
                basis="Tipo percentual, mas percentual de comissão não encontrado.",
                assumptions=[],
            )
        gross = round(price_brl * percent.value, 2)
        return CommissionEstimate(
            gross_commission_brl=gross,
            net_commission_brl=None,
            status=percent.status,
            basis=f"{percent.value * 100:.1f}% sobre preço de venda de R${price_brl:.2f}.",
            assumptions=[percent.note] if percent.note else [],
        )

    if commission.commission_type == CommissionType.FIXO:
        if not fixed.is_known():
            return CommissionEstimate(
                gross_commission_brl=None,
                net_commission_brl=None,
                status=DataStatus.DESCONHECIDO,
                basis="Tipo fixo, mas valor de comissão fixa não encontrado.",
                assumptions=[],
            )
        return CommissionEstimate(
            gross_commission_brl=fixed.value,
            net_commission_brl=None,
            status=fixed.status,
            basis=f"Comissão fixa de R${fixed.value:.2f} por venda.",
            assumptions=[fixed.note] if fixed.note else [],
        )

    # MISTO: soma o que estiver disponível; se nenhum dos dois for conhecido, desconhecido.
    if not percent.is_known() and not fixed.is_known():
        return CommissionEstimate(
            gross_commission_brl=None,
            net_commission_brl=None,
            status=DataStatus.DESCONHECIDO,
            basis="Tipo misto, mas nem percentual nem valor fixo foram encontrados.",
            assumptions=[],
        )

    percent_part = price_brl * percent.value if percent.is_known() else 0.0
    fixed_part = fixed.value if fixed.is_known() else 0.0
    gross = round(percent_part + fixed_part, 2)
    used_statuses = [s.status for s in (percent, fixed) if s.is_known()]
    basis_parts = []
    if percent.is_known():
        basis_parts.append(f"{percent.value * 100:.1f}% sobre R${price_brl:.2f}")
    else:
        basis_parts.append("percentual desconhecido (não incluído)")
    if fixed.is_known():
        basis_parts.append(f"R${fixed.value:.2f} fixo")
    else:
        basis_parts.append("valor fixo desconhecido (não incluído)")

    return CommissionEstimate(
        gross_commission_brl=gross,
        net_commission_brl=None,
        status=worst_status(used_statuses),
        basis="Misto: " + " + ".join(basis_parts) + ".",
        assumptions=[n for n in (percent.note, fixed.note) if n],
    )


def compute_net_commission(gross: CommissionEstimate, commission: CommissionInfo) -> CommissionEstimate:
    """Aplica custos diretamente associados (Seção 8) sobre uma estimativa de comissão bruta."""
    if gross.gross_commission_brl is None:
        return gross

    costs = commission.direct_costs_brl
    if not costs.is_known():
        return CommissionEstimate(
            gross_commission_brl=gross.gross_commission_brl,
            net_commission_brl=None,
            status=DataStatus.DESCONHECIDO,
            basis=gross.basis + " Custos diretamente associados desconhecidos — líquido não calculado.",
            assumptions=gross.assumptions,
        )

    net = round(gross.gross_commission_brl - costs.value, 2)
    return CommissionEstimate(
        gross_commission_brl=gross.gross_commission_brl,
        net_commission_brl=net,
        status=worst_status([gross.status, costs.status]),
        basis=gross.basis + f" Menos R${costs.value:.2f} de custos diretos = R${net:.2f} líquido.",
        assumptions=gross.assumptions + ([costs.note] if costs.note else []),
    )


def compute_commission_estimate(price_brl: float, commission: CommissionInfo) -> CommissionEstimate:
    """Atalho: bruta + líquida em uma chamada."""
    gross = compute_gross_commission(price_brl, commission)
    return compute_net_commission(gross, commission)
