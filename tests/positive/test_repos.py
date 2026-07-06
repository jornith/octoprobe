"""Positive scenarios for ``GET /repos/{owner}/{repo}`` and the issues list."""

import pytest

from src.schemas.issue import GithubIssue
from src.schemas.repo import GithubRepo
from tests.conftest import BUSY_REPO, KNOWN_REPO

pytestmark = [pytest.mark.smoke, pytest.mark.regression]


def test_get_repo_matches_schema(api_client):
    owner, name = KNOWN_REPO
    response = api_client.get_repo(owner, name)

    assert response.status_code == 200
    repo = GithubRepo.model_validate(response.json())
    assert repo.full_name == f"{owner}/{name}"
    assert repo.owner.login == owner
    assert repo.private is False
    assert repo.visibility == "public"


def test_list_issues_matches_schema(api_client):
    owner, name = BUSY_REPO
    response = api_client.list_issues(owner, name, per_page=5)

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert 0 < len(payload) <= 5
    issues = [GithubIssue.model_validate(item) for item in payload]
    # The endpoint returns open issues by default.
    assert all(issue.state == "open" for issue in issues)


def test_list_issues_exposes_pagination_links(api_client):
    owner, name = BUSY_REPO
    response = api_client.list_issues(owner, name, per_page=1)

    assert response.status_code == 200
    # cpython has far more than one open issue, so a next page must exist.
    assert 'rel="next"' in response.headers.get("link", "")
