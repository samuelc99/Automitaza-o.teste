import pytest

from poe.affiliate.models import DataStatus, TrackedValue, worst_status


def test_tracked_value_known_requires_value():
    with pytest.raises(ValueError):
        TrackedValue(value=None, status=DataStatus.CONFIRMADO)


def test_tracked_value_unknown_requires_no_value():
    with pytest.raises(ValueError):
        TrackedValue(value=10.0, status=DataStatus.DESCONHECIDO)


def test_tracked_value_unknown_factory():
    tv = TrackedValue.unknown(note="não encontrado")
    assert tv.value is None
    assert tv.status == DataStatus.DESCONHECIDO
    assert not tv.is_known()


def test_tracked_value_is_known():
    tv = TrackedValue(value=0.08, status=DataStatus.CONFIRMADO)
    assert tv.is_known()


def test_worst_status_picks_least_certain():
    assert worst_status([DataStatus.CONFIRMADO, DataStatus.ESTIMADO]) == DataStatus.ESTIMADO
    assert worst_status([DataStatus.CONFIRMADO, DataStatus.DESCONHECIDO]) == DataStatus.DESCONHECIDO
    assert worst_status([DataStatus.CONFIRMADO, DataStatus.CONFIRMADO]) == DataStatus.CONFIRMADO


def test_worst_status_empty_list_is_desconhecido():
    assert worst_status([]) == DataStatus.DESCONHECIDO
