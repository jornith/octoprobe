"""Transport-level HTTP client: authentication, timeouts, retries and logging.

Endpoint semantics live in :mod:`src.client.github_client`; this module only
knows how to talk HTTP to an API host.
"""

import logging
import time
from types import TracebackType

import httpx

logger = logging.getLogger("octoprobe.client")

DEFAULT_TIMEOUT_SECONDS = 10.0
GITHUB_API_VERSION = "2022-11-28"
CONNECT_RETRIES = 2


class RateLimitExceededError(Exception):
    """Raised when GitHub reports an exhausted rate limit (403/429).

    Carries ``retry_after`` (seconds) so callers can decide whether to wait or abort.
    """

    def __init__(self, response: httpx.Response, retry_after: int | None) -> None:
        self.response = response
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exhausted for {response.request.url}, retry after {retry_after}s"
        )


class BaseClient:
    """Thin wrapper around ``httpx.Client``.

    * sends GitHub media-type and API-version headers on every request;
    * attaches a ``Bearer`` token when one is configured;
    * retries transient connection failures at transport level;
    * logs method, URL, status code and elapsed time for every call;
    * converts rate-limit refusals into :class:`RateLimitExceededError`.
    """

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "octoprobe-tests",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
            transport=httpx.HTTPTransport(retries=CONNECT_RETRIES),
        )

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        started = time.perf_counter()
        response = self._client.request(method, path, **kwargs)
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "%s %s -> %d in %.0f ms (ratelimit remaining: %s)",
            method,
            response.request.url,
            response.status_code,
            elapsed_ms,
            response.headers.get("x-ratelimit-remaining", "n/a"),
        )
        self._raise_on_rate_limit(response)
        return response

    @staticmethod
    def _raise_on_rate_limit(response: httpx.Response) -> None:
        """Detect the rate-limit signature GitHub documents for 403/429 responses.

        A plain 403 (e.g. access denied) must pass through untouched, so the check
        requires either ``Retry-After`` or an exhausted ``x-ratelimit-remaining``.
        """
        if response.status_code not in (403, 429):
            return
        retry_after = response.headers.get("retry-after")
        remaining = response.headers.get("x-ratelimit-remaining")
        if retry_after is None and remaining != "0":
            return
        raise RateLimitExceededError(
            response, int(retry_after) if retry_after is not None else None
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BaseClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
