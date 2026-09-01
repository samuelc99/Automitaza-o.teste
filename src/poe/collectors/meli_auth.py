"""Cliente OAuth2 para a API oficial do Mercado Livre.

Fluxo e endpoints verificados na documentação oficial (developers.mercadolivre.com.br,
seção "Autenticação e Autorização", consultada em 2026-08-31):

    POST https://api.mercadolibre.com/oauth/token
    Content-Type: application/x-www-form-urlencoded
    grant_type=refresh_token&client_id=...&client_secret=...&refresh_token=...

Detalhes confirmados na doc oficial (não presumidos):
- access_token expira em 21600s (6h).
- refresh_token é de USO ÚNICO — cada refresh devolve um novo refresh_token,
  que precisa ser persistido/usado na próxima chamada (o antigo não funciona
  mais depois de usado uma vez).
- Erros documentados: invalid_client (client_id/secret errado),
  invalid_grant (code/refresh_token inválido, expirado, revogado, ou
  enviado no fluxo errado).

Este módulo só implementa o fluxo de refresh (grant_type=refresh_token) —
o fluxo inicial de autorização (grant_type=authorization_code, que exige um
navegador e login do usuário) é um passo manual único, documentado no
README, feito fora do sistema.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional

TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
_ACCESS_TOKEN_TTL_SECONDS = 21600  # 6h, conforme doc oficial
_REFRESH_SAFETY_MARGIN_SECONDS = 60  # renova um pouco antes de expirar de verdade


class MeliAuthError(Exception):
    """Erro de autenticação/autorização (client inválido, grant inválido, rede, etc.)."""


HttpPost = Callable[[str, dict], tuple[int, dict]]


def _default_http_post(url: str, form_data: dict, timeout: float = 15.0) -> tuple[int, dict]:
    """POST application/x-www-form-urlencoded, devolve (status_code, json_body).

    Implementação padrão via urllib (sem dependência nova). Testes devem
    injetar um `http_post` fake em vez de bater na rede de verdade.
    """
    import urllib.parse

    encoded = urllib.parse.urlencode(form_data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=encoded,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {"error": "unknown", "message": str(e)}
        return e.code, body
    except urllib.error.URLError as e:
        raise MeliAuthError(f"Falha de rede ao chamar {url}: {e}") from e


@dataclass
class _CachedToken:
    access_token: str
    expires_at: float  # time.monotonic() timestamp


class MeliAuthClient:
    """Gerencia o ciclo de vida do access_token via refresh_token.

    Uso:
        client = MeliAuthClient(client_id, client_secret, refresh_token)
        token = client.get_access_token()  # renova automaticamente quando necessário
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        http_post: Optional[HttpPost] = None,
        token_url: str = TOKEN_URL,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self._refresh_token = refresh_token
        self._http_post = http_post or _default_http_post
        self._token_url = token_url
        self._cached: Optional[_CachedToken] = None

    def get_access_token(self) -> str:
        if self._cached is not None and time.monotonic() < self._cached.expires_at:
            return self._cached.access_token
        return self._refresh()

    def _refresh(self) -> str:
        status, body = self._http_post(
            self._token_url,
            {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self._refresh_token,
            },
        )

        if status != 200:
            error_code = body.get("error", "unknown_error")
            message = body.get("message") or body.get("error_description") or str(body)
            raise MeliAuthError(f"Falha ao renovar token (HTTP {status}, {error_code}): {message}")

        access_token = body.get("access_token")
        expires_in = body.get("expires_in", _ACCESS_TOKEN_TTL_SECONDS)
        new_refresh_token = body.get("refresh_token")

        if not access_token:
            raise MeliAuthError(f"Resposta de token sem 'access_token': {body}")

        if new_refresh_token:
            # refresh_token é de uso único — o antigo já não serve mais.
            self._refresh_token = new_refresh_token

        self._cached = _CachedToken(
            access_token=access_token,
            expires_at=time.monotonic() + max(0, expires_in - _REFRESH_SAFETY_MARGIN_SECONDS),
        )
        return access_token

    @property
    def current_refresh_token(self) -> str:
        """O refresh_token mais recente — persista isto se quiser reusar entre execuções."""
        return self._refresh_token
