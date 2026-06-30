"""Shared fixtures: configured API clients and well-known test data."""

import pytest

from src.client.github_client import GithubClient
from src.config import Settings, get_settings

# Stable public objects used as test data. GitHub maintains the first two;
# python/cpython gives the issue and pagination tests a busy, long-lived target.
KNOWN_USER = "octocat"
KNOWN_REPO = ("octocat", "Hello-World")
BUSY_REPO = ("python", "cpython")


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def unauth_client(settings: Settings):
    """Anonymous client: exercises the 60 req/hour tier."""
    with GithubClient(base_url=settings.base_url, timeout=settings.request_timeout) as client:
        yield client


@pytest.fixture(scope="session")
def authed_client(settings: Settings):
    """Token-authenticated client; skips dependants when no token is configured."""
    if not settings.github_token:
        pytest.skip("GITHUB_TOKEN is not set")
    with GithubClient(
        base_url=settings.base_url,
        token=settings.github_token,
        timeout=settings.request_timeout,
    ) as client:
        yield client


@pytest.fixture(scope="session")
def api_client(settings: Settings):
    """Best available client: authenticated when a token exists, anonymous otherwise.

    Most functional tests do not care about the auth tier, but preferring the
    token keeps CI clear of the anonymous rate limit.
    """
    with GithubClient(
        base_url=settings.base_url,
        token=settings.github_token,
        timeout=settings.request_timeout,
    ) as client:
        yield client
