"""Invalid identifiers, hostile path values and unsupported HTTP methods."""

import pytest

from src.schemas.error import GithubErrorResponse
from tests.conftest import KNOWN_USER

pytestmark = [pytest.mark.negative, pytest.mark.regression]


def test_missing_user_yields_404_with_error_body(api_client):
    response = api_client.get_user("no-such-user-a1b2c3d4e5f6a7b8")

    assert response.status_code == 404
    error = GithubErrorResponse.model_validate(response.json())
    assert error.message == "Not Found"


def test_missing_repo_yields_404(api_client):
    response = api_client.get_repo("octocat", "no-such-repo-a1b2c3d4e5")

    assert response.status_code == 404
    GithubErrorResponse.model_validate(response.json())


@pytest.mark.parametrize(
    "hostile_username",
    [
        pytest.param("'; DROP TABLE users;--", id="sql-injection"),
        pytest.param("<script>alert(1)</script>", id="xss-payload"),
        pytest.param("{{7*7}}", id="template-injection"),
        pytest.param("user name with spaces", id="whitespace"),
        pytest.param("тест-юзер-кириллица", id="non-ascii"),
    ],
)
def test_hostile_path_values_never_hit_500(api_client, hostile_username):
    """The API must treat garbage identifiers as plain lookups that miss.

    Anything in the 5xx range would mean the payload reached an interpreter.
    """
    response = api_client.get_user(hostile_username)

    assert response.status_code == 404
    assert response.status_code < 500


def test_unsupported_method_is_masked_as_404(api_client):
    """GitHub answers 404 rather than 405 for unsupported methods on existing
    routes, hiding which verbs a resource supports (observed live; RFC 9110
    would also permit a 405 here).
    """
    response = api_client.request("DELETE", f"/users/{KNOWN_USER}")

    assert response.status_code == 404
