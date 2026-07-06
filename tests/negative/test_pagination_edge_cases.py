"""Pagination boundaries: clamping, tolerance and the search results cap.

Marked ``regression`` only: these run in the nightly full pass, matching the
slow layer of the test pyramid described in the README.
"""

import pytest

from src.schemas.error import GithubErrorResponse
from tests.conftest import BUSY_REPO

pytestmark = [pytest.mark.regression]


def test_oversized_per_page_is_clamped_not_rejected(api_client):
    """GitHub silently clamps per_page to 100 instead of returning 422 (observed live)."""
    owner, name = BUSY_REPO
    response = api_client.list_issues(owner, name, per_page=100_000)

    assert response.status_code == 200
    assert len(response.json()) <= 100


def test_negative_page_number_is_tolerated(api_client):
    owner, name = BUSY_REPO
    response = api_client.list_issues(owner, name, page=-1, per_page=5)

    # Observed live: the API treats a negative page as the first page.
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_search_beyond_first_1000_results_yields_422(api_client):
    """Search exposes only the first 1000 results; page 200 x 100 sits far beyond."""
    response = api_client.search_repositories("python", page=200, per_page=100)

    assert response.status_code == 422
    error = GithubErrorResponse.model_validate(response.json())
    assert "first 1000 search results" in error.message
    # The cap refusal carries no ``errors`` list, unlike query-validation 422s;
    # the documentation link is the only machine-actionable hint.
    assert error.documentation_url is not None
