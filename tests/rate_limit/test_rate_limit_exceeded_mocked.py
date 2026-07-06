"""Client behaviour on rate-limit refusals, simulated with respx.

Exhausting the real quota in CI would block every other test for an hour, so
these scenarios run against mocked transport only.
"""

import httpx
import pytest
import respx

from src.client.base_client import RateLimitExceededError
from src.client.github_client import GithubClient

pytestmark = [pytest.mark.rate_limit, pytest.mark.regression]

BASE_URL = "https://api.github.com"


@respx.mock
def test_403_with_retry_after_raises_typed_error():
    respx.get(f"{BASE_URL}/users/octocat").mock(
        return_value=httpx.Response(
            403,
            headers={"Retry-After": "42", "x-ratelimit-remaining": "0"},
            json={"message": "API rate limit exceeded"},
        )
    )

    with GithubClient(base_url=BASE_URL) as client, pytest.raises(RateLimitExceededError) as exc:
        client.get_user("octocat")

    assert exc.value.retry_after == 42
    assert exc.value.response.status_code == 403


@respx.mock
def test_429_secondary_limit_raises_typed_error():
    respx.get(f"{BASE_URL}/rate_limit").mock(
        return_value=httpx.Response(
            429,
            headers={"Retry-After": "60"},
            json={"message": "You have exceeded a secondary rate limit"},
        )
    )

    with GithubClient(base_url=BASE_URL) as client, pytest.raises(RateLimitExceededError) as exc:
        client.get_rate_limit()

    assert exc.value.retry_after == 60


@respx.mock
def test_plain_403_passes_through_untouched():
    """A 403 without the rate-limit signature (no Retry-After, quota not exhausted)
    must reach the caller as a normal response."""
    respx.get(f"{BASE_URL}/users/octocat").mock(
        return_value=httpx.Response(
            403,
            headers={"x-ratelimit-remaining": "4999"},
            json={"message": "Forbidden"},
        )
    )

    with GithubClient(base_url=BASE_URL) as client:
        response = client.get_user("octocat")

    assert response.status_code == 403
