"""OpenAI call-site resilience — tenacity backoff with an explicit, log-friendly error taxonomy."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

import httpx
from openai import APIError, APITimeoutError, RateLimitError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

P = ParamSpec("P")
R = TypeVar("R")


class OpenAIInvocationError(Exception):
    """Base class for retried OpenAI failures that bubbled past tenacity."""


class OpenAITransientError(OpenAIInvocationError):
    """Timeouts, 5xx, or network faults — safe to retry at a higher layer."""


class OpenAIRateLimitedError(OpenAIInvocationError):
    """Vendor rate limit — surface Retry-After semantics upstream when present."""


class OpenAIQuotaError(OpenAIInvocationError):
    """Billing / quota exhaustion — operator intervention required."""


class OpenAIClientError(OpenAIInvocationError):
    """Non-retryable 4xx (except rate limit) — prompt or integration bug."""


def classify_openai_exception(exc: BaseException) -> OpenAIInvocationError:
    if isinstance(exc, RateLimitError):
        return OpenAIRateLimitedError(str(exc))
    if isinstance(exc, APITimeoutError) or isinstance(exc, httpx.TimeoutException):
        return OpenAITransientError(str(exc))
    if isinstance(exc, APIError):
        status = getattr(exc, "status_code", None)
        if status == 429:
            return OpenAIRateLimitedError(str(exc))
        if status is not None and 500 <= int(status) < 600:
            return OpenAITransientError(str(exc))
        code = getattr(exc, "code", None)
        if code in {"insufficient_quota", "billing_hard_limit_reached"}:
            return OpenAIQuotaError(str(exc))
        return OpenAIClientError(str(exc))
    if isinstance(exc, (httpx.TransportError, httpx.HTTPError)):
        return OpenAITransientError(str(exc))
    return OpenAITransientError(str(exc))


def _retryable_openai_exception(exc: BaseException) -> bool:
    if isinstance(exc, (RateLimitError, APITimeoutError)):
        return True
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError, httpx.WriteError)):
        return True
    if isinstance(exc, APIError):
        status = getattr(exc, "status_code", None)
        return status is not None and int(status) >= 500
    return False


def openai_retry(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    """Decorator for async OpenAI/LangChain calls with jittered exponential backoff."""

    return retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=0.5, max=8),
        retry=retry_if_exception(_retryable_openai_exception),
    )(fn)
