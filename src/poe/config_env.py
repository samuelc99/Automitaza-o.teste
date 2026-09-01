"""Carregamento de credenciais via variáveis de ambiente (Seção 4).

Nunca hardcode Client ID/Secret/tokens. `.env` fica fora do controle de
versão (ver .gitignore); `.env.example` documenta as chaves esperadas.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv as _load_dotenv
except ImportError:  # pragma: no cover - só ocorre se a dependência não foi instalada
    _load_dotenv = None


def load_env(path: str = ".env") -> None:
    """Carrega o .env para os_environ, se python-dotenv estiver disponível e o arquivo existir.

    Silencioso se o arquivo não existir (é opcional — modo manual não precisa dele).
    """
    if _load_dotenv is not None:
        _load_dotenv(dotenv_path=path, override=False)


@dataclass
class MeliCredentials:
    client_id: str
    client_secret: str
    refresh_token: str
    site_id: str = "MLB"


class MissingCredentialsError(Exception):
    pass


def get_meli_credentials(required: bool = False) -> MeliCredentials | None:
    """Lê MELI_CLIENT_ID / MELI_CLIENT_SECRET / MELI_REFRESH_TOKEN / MELI_SITE_ID do ambiente.

    Por padrão (required=False) retorna None se algo estiver faltando, para
    que o chamador decida degradar graciosamente (Seção 5). Com required=True,
    levanta MissingCredentialsError com uma mensagem acionável.
    """
    client_id = os.environ.get("MELI_CLIENT_ID", "").strip()
    client_secret = os.environ.get("MELI_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("MELI_REFRESH_TOKEN", "").strip()
    site_id = os.environ.get("MELI_SITE_ID", "MLB").strip() or "MLB"

    missing = [
        name
        for name, val in [
            ("MELI_CLIENT_ID", client_id),
            ("MELI_CLIENT_SECRET", client_secret),
            ("MELI_REFRESH_TOKEN", refresh_token),
        ]
        if not val
    ]

    if missing:
        if required:
            raise MissingCredentialsError(
                f"Variáveis de ambiente ausentes: {', '.join(missing)}. "
                f"Veja .env.example — registre uma aplicação em "
                f"developers.mercadolivre.com.br e gere um refresh_token via OAuth "
                f"(README.md tem o passo a passo)."
            )
        return None

    return MeliCredentials(
        client_id=client_id, client_secret=client_secret, refresh_token=refresh_token, site_id=site_id
    )
