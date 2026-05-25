"""Minimal CDSE OAuth2 client_credentials helper.

PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.
"""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_local_env() -> None:
    """Load a local .env if present, without requiring one."""
    load_dotenv(PROJECT_ROOT / ".env")


def _missing_credentials_message() -> str:
    return (
        "Missing CDSE_CLIENT_ID and/or CDSE_CLIENT_SECRET. "
        "Define them as environment variables, or create a local uncommitted .env "
        "from .env.example."
    )


def get_cdse_token(timeout_seconds: int = 30) -> str:
    load_local_env()
    client_id = os.getenv("CDSE_CLIENT_ID")
    client_secret = os.getenv("CDSE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(_missing_credentials_message())

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=timeout_seconds,
    )

    if response.status_code in (400, 401):
        raise RuntimeError(
            "CDSE authentication failed. Check CDSE_CLIENT_ID/CDSE_CLIENT_SECRET "
            f"and OAuth client status. HTTP {response.status_code}: {response.text[:500]}"
        )

    if response.status_code == 429:
        raise RuntimeError(
            "CDSE token request was rate limited. Reuse tokens during runs and retry later. "
            f"HTTP 429: {response.text[:500]}"
        )

    if not response.ok:
        raise RuntimeError(
            f"CDSE authentication returned HTTP {response.status_code}: {response.text[:500]}"
        )

    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("CDSE authentication response did not include access_token.")

    return token


def decode_jwt_payload_unverified(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    padded = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")))
    except (ValueError, json.JSONDecodeError):
        return {}


def main() -> int:
    try:
        token = get_cdse_token()
    except RuntimeError as exc:
        print(f"Auth: FAIL - {exc}")
        return 2

    payload = decode_jwt_payload_unverified(token)
    expires_at = payload.get("exp")
    if isinstance(expires_at, int):
        seconds_left = max(0, expires_at - int(time.time()))
        print(f"Auth: OK - token received, expires in about {seconds_left // 60} minutes.")
    else:
        print("Auth: OK - token received.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
