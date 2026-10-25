"""Authentication for the Garmin Connect Personal API.

Flow (confirmed live, see docs/api-reference.md):
  1. POST the API key to the token endpoint with `Authorization: ApiKey <key>`.
  2. The response body is a raw JWT (text/plain) -- that IS the bearer token.
  3. The JWT's `exp` claim gives its lifetime (~24h). No refresh token; re-mint on expiry.

Secrets (the API key and the JWT) are never logged.
"""

import base64
import json
import os
from pathlib import Path

import requests

TOKEN_URL = (
    "https://personal.connectapi.garmin.com"
    "/personalapitoken-service/personal-api/personal-api-key/token"
)
KEY_FILES = [
    Path("connect-personal-api-key"),
    Path.home() / ".config" / "garmin" / "connect-personal-api-key",
]
TIMEOUT = 30  # seconds


def load_api_key():
    """Resolve the API key: env var first, then the known key files."""
    env_key = os.environ.get("GARMIN_PERSONAL_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()
    for path in KEY_FILES:
        if path.is_file():
            key = path.read_text().strip()
            if key:
                return key
    checked = ["GARMIN_PERSONAL_API_KEY env var"] + [str(p) for p in KEY_FILES]
    raise RuntimeError("No Garmin API key found. Checked: " + ", ".join(checked))


def _jwt_exp(token):
    """Return the `exp` (unix seconds) from a JWT payload, or None if unreadable."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)  # pad to a multiple of 4
        claims = json.loads(base64.urlsafe_b64decode(payload))
        return int(claims["exp"])
    except Exception:
        return None


def mint_token(api_key=None, session=None):
    """Exchange the API key for a bearer JWT.

    Returns (token, exp) where exp is unix seconds or None.
    """
    api_key = api_key or load_api_key()
    http = session or requests
    resp = http.post(
        TOKEN_URL,
        headers={"Authorization": f"ApiKey {api_key}"},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    token = resp.text.strip()
    if not token:
        raise RuntimeError("Token endpoint returned an empty body.")
    return token, _jwt_exp(token)
