import pytest

from poe.config_env import MissingCredentialsError, get_meli_credentials


def test_get_meli_credentials_returns_none_when_missing(monkeypatch):
    monkeypatch.delenv("MELI_CLIENT_ID", raising=False)
    monkeypatch.delenv("MELI_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("MELI_REFRESH_TOKEN", raising=False)

    assert get_meli_credentials(required=False) is None


def test_get_meli_credentials_raises_when_required_and_missing(monkeypatch):
    monkeypatch.delenv("MELI_CLIENT_ID", raising=False)
    monkeypatch.delenv("MELI_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("MELI_REFRESH_TOKEN", raising=False)

    with pytest.raises(MissingCredentialsError, match="MELI_CLIENT_ID"):
        get_meli_credentials(required=True)


def test_get_meli_credentials_reads_all_fields(monkeypatch):
    monkeypatch.setenv("MELI_CLIENT_ID", "cid")
    monkeypatch.setenv("MELI_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("MELI_REFRESH_TOKEN", "rtoken")
    monkeypatch.setenv("MELI_SITE_ID", "MLA")

    creds = get_meli_credentials(required=True)

    assert creds.client_id == "cid"
    assert creds.client_secret == "csecret"
    assert creds.refresh_token == "rtoken"
    assert creds.site_id == "MLA"


def test_get_meli_credentials_defaults_site_id(monkeypatch):
    monkeypatch.setenv("MELI_CLIENT_ID", "cid")
    monkeypatch.setenv("MELI_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("MELI_REFRESH_TOKEN", "rtoken")
    monkeypatch.delenv("MELI_SITE_ID", raising=False)

    creds = get_meli_credentials(required=True)

    assert creds.site_id == "MLB"


def test_partial_credentials_treated_as_missing(monkeypatch):
    monkeypatch.setenv("MELI_CLIENT_ID", "cid")
    monkeypatch.delenv("MELI_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("MELI_REFRESH_TOKEN", raising=False)

    assert get_meli_credentials(required=False) is None
