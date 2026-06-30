"""Positive scenarios for ``GET /users/{username}``."""

import pytest

from src.schemas.user import GithubUser
from tests.conftest import KNOWN_USER

pytestmark = [pytest.mark.smoke, pytest.mark.regression]


def test_get_known_user_matches_schema(api_client):
    response = api_client.get_user(KNOWN_USER)

    assert response.status_code == 200
    user = GithubUser.model_validate(response.json())
    assert user.login == KNOWN_USER
    assert user.type == "User"
    assert user.id > 0


def test_get_user_sanity_fields(api_client):
    response = api_client.get_user(KNOWN_USER)

    user = GithubUser.model_validate(response.json())
    # octocat has existed since 2011; counters can only be non-negative.
    assert user.created_at.year == 2011
    assert user.public_repos >= 0
    assert user.followers >= 0
    assert str(user.html_url) == f"https://github.com/{KNOWN_USER}"


def test_get_user_returns_json_media_type(api_client):
    response = api_client.get_user(KNOWN_USER)

    assert response.headers["content-type"].startswith("application/json")
