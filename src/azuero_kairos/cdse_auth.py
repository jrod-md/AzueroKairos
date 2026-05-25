"""CDSE OAuth helpers for official Azuero Kairós data runs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request


TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
    "protocol/openid-connect/token"
)


class CDSEAuthError(RuntimeError):
    """Raised when CDSE authentication cannot complete safely."""


@dataclass(frozen=True)
class CDSEToken:
    """In-memory CDSE token response."""

    access_token: str
    token_type: str
    expires_in: int | None = None

    @property
    def authorization_header(self) -> str:
        return f"{self.token_type} {self.access_token}"


def get_cdse_token(
    *,
    client_id: str | None = None,
    client_secret: str | None = None,
    timeout_seconds: float = 30.0,
) -> CDSEToken:
    """Request a CDSE OAuth access token using client credentials."""

    resolved_client_id = client_id or os.getenv("CDSE_CLIENT_ID")
    resolved_client_secret = client_secret or os.getenv("CDSE_CLIENT_SECRET")

    if not resolved_client_id or not resolved_client_secret:
        raise CDSEAuthError(
            "Missing CDSE_CLIENT_ID or CDSE_CLIENT_SECRET environment variable."
        )

    body = parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": resolved_client_id,
            "client_secret": resolved_client_secret,
        }
    ).encode("utf-8")

    token_request = request.Request(
        TOKEN_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )

    try:
        with request.urlopen(token_request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise CDSEAuthError(
            f"CDSE token request failed with HTTP {exc.code}."
        ) from exc
    except error.URLError as exc:
        raise CDSEAuthError(f"CDSE token request failed: {exc.reason}.") from exc
    except TimeoutError as exc:
        raise CDSEAuthError("CDSE token request timed out.") from exc
    except json.JSONDecodeError as exc:
        raise CDSEAuthError("CDSE token response was not valid JSON.") from exc

    return _parse_token_payload(payload)


def _parse_token_payload(payload: dict[str, Any]) -> CDSEToken:
    access_token = payload.get("access_token")
    token_type = payload.get("token_type", "Bearer")
    expires_in = payload.get("expires_in")

    if not isinstance(access_token, str) or not access_token:
        raise CDSEAuthError("CDSE token response did not include an access token.")

    if not isinstance(token_type, str) or not token_type:
        token_type = "Bearer"

    if not isinstance(expires_in, int):
        expires_in = None

    return CDSEToken(
        access_token=access_token,
        token_type=token_type,
        expires_in=expires_in,
    )
