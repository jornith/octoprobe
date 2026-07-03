"""Live checks of the rate-limit contract: headers and tier differences.

``GET /rate_limit`` itself does not count against the quota, which makes the
tier-comparison test safe to run on every push.
"""

import time

import pytest

from tests.conftest import KNOWN_USER

pytestmark = [pytest.mark.rate_limit, pytest.mark.regression]

RATE_LIMIT_HEADERS = (
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-reset",
    "x-ratelimit-used",
)


def test_rate_limit_headers_present_and_numeric(api_client):
    response = api_client.get_user(KNOWN_USER)

    assert response.status_code == 200
    for header in RATE_LIMIT_HEADERS:
        assert header in response.headers, f"missing {header}"
        assert response.headers[header].isdigit(), f"{header} must be an integer"


def test_rate_limit_header_values_are_consistent(api_client):
    response = api_client.get_user(KNOWN_USER)

    limit = int(response.headers["x-ratelimit-limit"])
    remaining = int(response.headers["x-ratelimit-remaining"])
    used = int(response.headers["x-ratelimit-used"])
    reset_at = int(response.headers["x-ratelimit-reset"])

    assert remaining <= limit
    assert used + remaining == limit
    # The reset moment lies in the future, at most one hour away (plus clock skew).
    assert time.time() - 60 < reset_at < time.time() + 3660


def test_authenticated_tier_is_larger_than_anonymous(authed_client, unauth_client):
    authed_core = authed_client.get_rate_limit().json()["resources"]["core"]
    anonymous_core = unauth_client.get_rate_limit().json()["resources"]["core"]

    # Documented tiers: 60/hour anonymous, 5000/hour with a personal token.
    assert anonymous_core["limit"] == 60
    assert authed_core["limit"] >= 1000
    assert authed_core["limit"] > anonymous_core["limit"]
