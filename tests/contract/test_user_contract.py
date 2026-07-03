"""Consumer-driven contract for ``GET /users/{username}``.

The consumer records the fields we depend on against a pact mock server.
There's no Pact Broker for GitHub, so the provider side is verified directly
against the live API instead of being published for the provider to check.
"""

import json
from pathlib import Path
from urllib.parse import urlparse

import pytest
from pact import Pact, Verifier, match

from src.client.github_client import GithubClient
from src.schemas.user import GithubUser

pytestmark = [pytest.mark.contract, pytest.mark.regression]

CONSUMER = "octoprobe"
PROVIDER = "github-rest-api"
PACT_DIR = Path(__file__).resolve().parents[2] / "pacts"

ISO_INSTANT = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"


def _user_contract_body() -> dict:
    """Only the fields octoprobe consumes: a consumer contract stays minimal."""
    return {
        "login": match.string("octocat"),
        "id": match.integer(583231),
        "node_id": match.string("MDQ6VXNlcjU4MzIzMQ=="),
        "avatar_url": match.regex(
            "https://avatars.githubusercontent.com/u/583231?v=4", regex=r"https://.+"
        ),
        "html_url": match.regex(
            "https://github.com/octocat", regex=r"https://github\.com/.+"
        ),
        "url": match.regex(
            "https://api.github.com/users/octocat",
            regex=r"https://api\.github\.com/users/.+",
        ),
        "type": "User",
        "site_admin": match.boolean(False),
        "name": match.string("The Octocat"),
        "public_repos": match.integer(8),
        "public_gists": match.integer(8),
        "followers": match.integer(3938),
        "following": match.integer(9),
        "created_at": match.regex("2011-01-25T18:44:36Z", regex=ISO_INSTANT),
        "updated_at": match.regex("2024-01-01T00:00:00Z", regex=ISO_INSTANT),
    }


def _build_user_pact() -> Pact:
    pact = Pact(CONSUMER, PROVIDER).with_specification("V4")
    (
        pact.upon_receiving("a request for an existing user")
        .given("user octocat exists")
        .with_request("GET", "/users/octocat")
        .will_respond_with(200)
        .with_body(_user_contract_body(), content_type="application/json")
    )
    return pact


@pytest.fixture(scope="module")
def consumer_exchange():
    """Run the consumer side against the pact mock server and write the pact file."""
    pact = _build_user_pact()
    with pact.serve(raises=True) as server, GithubClient(base_url=str(server.url)) as client:
        response = client.get_user("octocat")
    PACT_DIR.mkdir(exist_ok=True)
    pact.write_file(PACT_DIR, overwrite=True)
    return response, PACT_DIR / f"{CONSUMER}-{PROVIDER}.json"


def test_client_fulfils_consumer_contract(consumer_exchange):
    response, _ = consumer_exchange

    assert response.status_code == 200
    user = GithubUser.model_validate(response.json())
    assert user.login == "octocat"


def test_pact_file_records_the_interaction(consumer_exchange):
    _, pact_path = consumer_exchange

    assert pact_path.exists()
    document = json.loads(pact_path.read_text())
    assert document["consumer"]["name"] == CONSUMER
    assert document["provider"]["name"] == PROVIDER
    descriptions = [i["description"] for i in document["interactions"]]
    assert "a request for an existing user" in descriptions


def test_provider_honours_contract_against_live_api(consumer_exchange, settings):
    """Provider-side verification, aimed straight at api.github.com.

    A broker-based setup would run this from the provider's pipeline instead;
    the comment in the module docstring covers the trade-off.
    """
    _, pact_path = consumer_exchange
    verifier = (
        Verifier(PROVIDER, host=urlparse(settings.base_url).hostname)
        .add_transport(url=settings.base_url)
        .add_source(pact_path)
        # GitHub refuses requests without a User-Agent (403 + HTML page),
        # and the pact core sends none by default.
        .add_custom_header("User-Agent", "octoprobe-pact-verifier")
        .add_custom_header("Accept", "application/vnd.github+json")
    )
    if settings.github_token:
        verifier.add_custom_header("Authorization", f"Bearer {settings.github_token}")

    verifier.verify()

    # ``verify`` raises on mismatch; an empty mismatch list is the green signal.
    assert verifier.results["errors"] == []
