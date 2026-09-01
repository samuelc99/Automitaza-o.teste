from poe.affiliate.economics import compute_commission_estimate, compute_gross_commission, compute_net_commission
from poe.affiliate.models import CommissionInfo, CommissionType, DataStatus, TrackedValue


def make_commission(**overrides):
    defaults = dict(
        network_name="Rede Teste",
        commission_type=CommissionType.PERCENTUAL,
        commission_percent=TrackedValue.unknown(),
        commission_fixed_brl=TrackedValue.unknown(),
        cookie_duration_days=TrackedValue.unknown(),
        epc_brl=TrackedValue.unknown(),
        direct_costs_brl=TrackedValue.unknown(),
    )
    defaults.update(overrides)
    return CommissionInfo(**defaults)


def test_gross_commission_percentual_known():
    commission = make_commission(commission_percent=TrackedValue(0.08, DataStatus.CONFIRMADO))
    estimate = compute_gross_commission(100.0, commission)
    assert estimate.gross_commission_brl == 8.0
    assert estimate.status == DataStatus.CONFIRMADO


def test_gross_commission_percentual_unknown():
    commission = make_commission(commission_percent=TrackedValue.unknown())
    estimate = compute_gross_commission(100.0, commission)
    assert estimate.gross_commission_brl is None
    assert estimate.status == DataStatus.DESCONHECIDO


def test_gross_commission_fixo_known():
    commission = make_commission(
        commission_type=CommissionType.FIXO,
        commission_fixed_brl=TrackedValue(15.0, DataStatus.CONFIRMADO),
    )
    estimate = compute_gross_commission(100.0, commission)
    assert estimate.gross_commission_brl == 15.0


def test_gross_commission_fixo_unknown():
    commission = make_commission(commission_type=CommissionType.FIXO)
    estimate = compute_gross_commission(100.0, commission)
    assert estimate.gross_commission_brl is None
    assert estimate.status == DataStatus.DESCONHECIDO


def test_gross_commission_misto_both_known():
    commission = make_commission(
        commission_type=CommissionType.MISTO,
        commission_percent=TrackedValue(0.05, DataStatus.CONFIRMADO),
        commission_fixed_brl=TrackedValue(3.0, DataStatus.ESTIMADO),
    )
    estimate = compute_gross_commission(100.0, commission)
    assert estimate.gross_commission_brl == 8.0  # 5 + 3
    assert estimate.status == DataStatus.ESTIMADO  # pior dos dois


def test_gross_commission_misto_one_known_one_unknown():
    commission = make_commission(
        commission_type=CommissionType.MISTO,
        commission_percent=TrackedValue(0.05, DataStatus.CONFIRMADO),
        commission_fixed_brl=TrackedValue.unknown(),
    )
    estimate = compute_gross_commission(100.0, commission)
    assert estimate.gross_commission_brl == 5.0
    assert "desconhecido" in estimate.basis.lower()


def test_gross_commission_misto_both_unknown():
    commission = make_commission(commission_type=CommissionType.MISTO)
    estimate = compute_gross_commission(100.0, commission)
    assert estimate.gross_commission_brl is None
    assert estimate.status == DataStatus.DESCONHECIDO


def test_net_commission_with_known_costs():
    commission = make_commission(
        commission_percent=TrackedValue(0.10, DataStatus.CONFIRMADO),
        direct_costs_brl=TrackedValue(2.0, DataStatus.CONFIRMADO),
    )
    estimate = compute_commission_estimate(100.0, commission)
    assert estimate.gross_commission_brl == 10.0
    assert estimate.net_commission_brl == 8.0
    assert estimate.status == DataStatus.CONFIRMADO


def test_net_commission_with_unknown_costs_stays_unknown():
    commission = make_commission(commission_percent=TrackedValue(0.10, DataStatus.CONFIRMADO))
    estimate = compute_commission_estimate(100.0, commission)
    assert estimate.gross_commission_brl == 10.0
    assert estimate.net_commission_brl is None
    assert estimate.status == DataStatus.DESCONHECIDO


def test_net_commission_never_called_when_gross_unknown():
    commission = make_commission()  # tudo desconhecido
    gross = compute_gross_commission(100.0, commission)
    net = compute_net_commission(gross, commission)
    assert net.gross_commission_brl is None
    assert net.net_commission_brl is None
