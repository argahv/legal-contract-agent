"""Global rate limiting using slowapi — protects auth + expensive AI ingress paths."""

from fastapi import FastAPI
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def attach_rate_limit_state(app: FastAPI) -> None:
    """Wire limiter onto FastAPI app state (slowapi expects app.state.limiter)."""
    app.state.limiter = limiter  # pragma: allow slowapi internal contract
