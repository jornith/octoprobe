"""Positive scenarios for ``GET /search/repositories``."""

import pytest

from src.schemas.repo import RepoSearchResponse

pytestmark = [pytest.mark.smoke, pytest.mark.regression]


def test_search_repositories_matches_schema(api_client):
    response = api_client.search_repositories("language:python stars:>50000")

    assert response.status_code == 200
    result = RepoSearchResponse.model_validate(response.json())
    assert result.total_count > 0
    assert result.items, "search for hugely popular python repos must return items"


def test_search_results_respect_the_query(api_client):
    response = api_client.search_repositories("language:python stars:>50000", per_page=10)

    result = RepoSearchResponse.model_validate(response.json())
    assert len(result.items) <= 10
    for repo in result.items:
        assert repo.stargazers_count > 50_000
        assert repo.private is False


def test_search_reports_total_count_stable_shape(api_client):
    response = api_client.search_repositories("nonexistent-repo-name-a1b2c3d4e5")

    # Zero hits is a valid, well-formed response, not an error.
    assert response.status_code == 200
    result = RepoSearchResponse.model_validate(response.json())
    assert result.total_count == 0
    assert result.items == []
