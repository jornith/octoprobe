"""Authentication failure scenarios.

GitHub validates the Authorization header even on public endpoints: a broken
Bearer credential poisons the whole request instead of degrading to anonymous
access. The Basic scheme is the documented exception since its retirement in
2020: GitHub ignores it entirely.
"""

import pytest

from src.client.github_client import GithubClient
from src.schemas.error import GithubErrorResponse
from tests.conftest import KNOWN_USER

pytestmark = [pytest.mark.negative, pytest.mark.regression]


@pytest.mark.parametrize(
    "bad_token",
    [
        pytest.param("ghp_definitely_not_a_real_token_0000000000", id="invalid-token"),
        pytest.param("0123456789abcdef", id="malformed-token"),
        pytest.param("x", id="single-char-token"),
    ],
)
def test_bad_bearer_token_yields_401(settings, bad_token):
    with GithubClient(base_url=settings.base_url, token=bad_token) as client:
        response = client.get_user(KNOWN_USER)

    assert response.status_code == 401
    error = GithubErrorResponse.model_validate(response.json())
    assert error.message == "Bad credentials"
    assert error.status == "401"
    assert error.documentation_url is not None


def test_retired_basic_scheme_is_ignored(unauth_client):
    """Invalid Basic credentials do not fail the request: GitHub dropped Basic
    auth support and treats such requests as anonymous (observed live)."""
    response = unauth_client.request(
        "GET", f"/users/{KNOWN_USER}", headers={"Authorization": "Basic bm90OnJlYWw="}
    )

    assert response.status_code == 200
