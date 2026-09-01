import pytest

from poe.collectors.meli_auth import MeliAuthClient, MeliAuthError


def make_http_post(responses):
    """responses: lista de (status, body) devolvidos em ordem a cada chamada."""
    calls = []

    def fake_post(url, form_data):
        calls.append((url, form_data))
        return responses[len(calls) - 1]

    fake_post.calls = calls
    return fake_post


def test_get_access_token_success():
    http_post = make_http_post([(200, {"access_token": "TOKEN1", "expires_in": 21600, "refresh_token": "R2"})])
    client = MeliAuthClient("id", "secret", "R1", http_post=http_post)

    token = client.get_access_token()

    assert token == "TOKEN1"
    assert client.current_refresh_token == "R2"  # refresh_token rotacionou
    assert http_post.calls[0][1]["grant_type"] == "refresh_token"
    assert http_post.calls[0][1]["refresh_token"] == "R1"


def test_access_token_is_cached_until_expiry():
    http_post = make_http_post([(200, {"access_token": "TOKEN1", "expires_in": 21600, "refresh_token": "R2"})])
    client = MeliAuthClient("id", "secret", "R1", http_post=http_post)

    client.get_access_token()
    client.get_access_token()
    client.get_access_token()

    assert len(http_post.calls) == 1  # não renovou de novo, usou o cache


def test_invalid_client_raises_meli_auth_error():
    http_post = make_http_post([(400, {"error": "invalid_client", "message": "client_id inválido"})])
    client = MeliAuthClient("bad_id", "bad_secret", "R1", http_post=http_post)

    with pytest.raises(MeliAuthError, match="invalid_client"):
        client.get_access_token()


def test_invalid_grant_raises_meli_auth_error():
    http_post = make_http_post([(400, {"error": "invalid_grant", "message": "refresh_token expirado"})])
    client = MeliAuthClient("id", "secret", "expired_token", http_post=http_post)

    with pytest.raises(MeliAuthError, match="invalid_grant"):
        client.get_access_token()


def test_response_without_access_token_raises():
    http_post = make_http_post([(200, {"scope": "read"})])
    client = MeliAuthClient("id", "secret", "R1", http_post=http_post)

    with pytest.raises(MeliAuthError, match="access_token"):
        client.get_access_token()


def test_refresh_token_not_rotated_keeps_old_one():
    http_post = make_http_post([(200, {"access_token": "TOKEN1", "expires_in": 21600})])
    client = MeliAuthClient("id", "secret", "R1", http_post=http_post)

    client.get_access_token()

    assert client.current_refresh_token == "R1"
