"""Shared service-account credentials for the non-browser API clients.

Four separate components call the Phase 1 REST API over HTTP rather than in
process: the FastMCP server (`src/mcp_server/mcp_app.py`), the Phase 3 ReAct
agent tools (`src/agents/tools.py`), the Phase 5 LangGraph agents
(`src/agents/multi_agent/agents.py`) and the Streamlit purchase-order button
(`src/ui/chat_streamlit/app.py`). Every one of them sent no credentials at all,
which worked only because `get_current_user` served unauthenticated requests as
the admin account. With that bypass removed they each need a real token, and
duplicating a login flow four times would be four places to get it wrong.

Deliberately a login against the real `/auth/login` endpoint rather than a
locally minted JWT: signing our own token here would need SECRET_KEY in every
client process and would skip the very code path being secured, so a broken
login would go unnoticed until a human tried it.

The token is cached for the process lifetime because it is valid for 24h
(ACCESS_TOKEN_EXPIRE_MINUTES) and these are long-lived processes. Callers are
expected to `invalidate()` and retry once on a 401 rather than pre-emptively
checking expiry -- the server is the authority on whether a token is still good.
"""

import os
import threading
import time
from typing import Dict, Optional

import requests

# Same default base URL the clients already use, and the same env var, so nothing
# needs new configuration to keep working.
_DEFAULT_API_BASE = "http://localhost:8000/api/v1"

# Matches the bootstrap account created by `ensure_default_user` at startup.
_DEFAULT_EMAIL = "admin@retail.com"
_DEFAULT_PASSWORD = "admin"

# How long to wait before retrying after a failed login. Without this, a backend
# that is down turns every single API call into an extra doomed HTTP round trip,
# which in the test suites (where the backend is absent and `requests` is mocked)
# means one connection attempt per assertion.
_RETRY_COOLDOWN_SECONDS = 15.0

_lock = threading.Lock()
_token: Optional[str] = None
_last_failure_at: float = 0.0


def _api_base() -> str:
    return os.getenv("API_BASE_URL", _DEFAULT_API_BASE).rstrip("/")


def _credentials() -> tuple:
    return (
        os.getenv("SERVICE_ACCOUNT_EMAIL", _DEFAULT_EMAIL),
        os.getenv("SERVICE_ACCOUNT_PASSWORD", _DEFAULT_PASSWORD),
    )


def invalidate() -> None:
    """Discard the cached token. Call this after the API answers 401."""
    global _token, _last_failure_at
    with _lock:
        _token = None
        _last_failure_at = 0.0  # a rejected token is a reason to retry now, not to back off


def get_token(force_refresh: bool = False) -> Optional[str]:
    """Return a bearer token, logging in if needed. None if login is not possible.

    Returns None rather than raising: an unreachable backend is already handled
    by each caller's own error path ("API unavailable"), and turning it into an
    exception here would convert a graceful degradation into a crash in the
    Streamlit UI and the agent tools.
    """
    global _token, _last_failure_at

    with _lock:
        if _token and not force_refresh:
            return _token
        if not force_refresh and _last_failure_at and (
            time.monotonic() - _last_failure_at < _RETRY_COOLDOWN_SECONDS
        ):
            return None

    email, password = _credentials()
    try:
        response = requests.post(
            f"{_api_base()}/auth/login",
            data={"username": email, "password": password},
            timeout=10,
        )
        if response.status_code != 200:
            with _lock:
                _last_failure_at = time.monotonic()
            return None
        token = response.json().get("access_token")
    except Exception:
        # Includes ConnectionError/Timeout when the API is not running, and any
        # JSON decoding failure from an unexpected response body.
        with _lock:
            _last_failure_at = time.monotonic()
        return None

    if not token:
        with _lock:
            _last_failure_at = time.monotonic()
        return None

    with _lock:
        _token = token
        _last_failure_at = 0.0
    return token


def auth_headers(force_refresh: bool = False) -> Dict[str, str]:
    """Authorization header for the service account, or `{}` if login failed.

    An empty dict keeps the outbound call well-formed; the API will answer 401 and
    the caller surfaces that, which is a far more honest outcome than pretending
    the request could not be attempted.
    """
    token = get_token(force_refresh=force_refresh)
    return {"Authorization": f"Bearer {token}"} if token else {}
