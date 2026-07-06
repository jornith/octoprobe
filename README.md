# octoprobe

[![tests](https://github.com/jornith/octoprobe/actions/workflows/tests.yml/badge.svg)](https://github.com/jornith/octoprobe/actions/workflows/tests.yml)
[![nightly](https://github.com/jornith/octoprobe/actions/workflows/nightly.yml/badge.svg)](https://github.com/jornith/octoprobe/actions/workflows/nightly.yml)

The GitHub REST API mostly does what its docs say. octoprobe is about the places it does not. It holds `api.github.com` to what a consumer can see from outside, and pins four spots where the live behavior disagrees with the documented intuition, so a change on GitHub's side shows up here as a failed test instead of a surprise in some client.

I have no access to GitHub's code, so every assertion sits on what crosses the wire: status codes, headers, response shape, limits.

## The client

Two layers. `BaseClient` owns transport: bearer auth, a 10-second timeout, connection retries, request logging, and a typed `RateLimitExceededError`. `GithubClient` puts one method per endpoint on top and returns the raw `httpx.Response`. The tests decide what a valid answer is.

Folding status handling into the client made the negative tests impossible to write, so the client stays without an opinion on payloads. The pydantic schemas do their checking inside the tests, where a mismatch surfaces as a field-level diff rather than a swallowed exception.

## What surprised me

Four places where the live API left the docs behind. Each has a test that fails if GitHub changes it, and the nightly run is what notices.

**A wrong method returns 404, not 405.** `DELETE` on a read-only route does not tell you the method is unsupported. It answers 404 and hides which methods the route has. `test_unsupported_method_is_masked_as_404`.

**`per_page` is clamped, not rejected.** Ask for `per_page=100000` and you get 200 with the page capped at 100 and no error, not the 422 I expected. `test_oversized_per_page_is_clamped_not_rejected`.

**A broken Basic auth header is ignored.** Send a malformed `Authorization: Basic ...` and GitHub does not fail the request. It drops the retired scheme and serves you as anonymous. `test_retired_basic_scheme_is_ignored`.

**Search stops at 1000.** Page past the first 1000 search results and you get 422, whatever the total count claims. `test_search_beyond_first_1000_results_yields_422`.

## Test layers

The fast tests (contract, plus schema validation on the happy paths) and the medium tests (negative cases, rate-limit headers, respx-mocked 403/429) run on every push. The slow regression set, including the pagination edges, runs on a nightly cron. Markers: `smoke`, `contract`, `negative`, `rate_limit`, `regression`.

## Running it

Needs Python 3.11+.

```bash
git clone https://github.com/jornith/octoprobe.git
cd octoprobe
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # optional: a personal access token
pytest
```

It runs without a token: the authenticated-only checks skip themselves and the rest use the anonymous 60 req/hour tier. A token raises the ceiling to 5000 and unlocks the tier-comparison test.

```bash
pytest -m smoke        # positive happy paths
pytest -m contract     # pact consumer + live provider verification
pytest -m negative     # auth failures, 404s, hostile input, method masking
pytest -m rate_limit   # header contract + mocked 403/429 handling
pytest -m regression   # the full nightly set
```

## The contract test, without a broker

`tests/contract/test_user_contract.py` closes the pact loop on its own. The consumer side writes `pacts/octoprobe-github-rest-api.json` against a mock server; the provider side then verifies that pact against the live `api.github.com`. A real microservice estate would put a Pact Broker between those two steps and let the provider team verify from their own pipeline. GitHub does not consume our pact, so the direct check is the honest stand-in.

## Reports

```bash
pytest --alluredir=allure-results
allure serve allure-results   # needs the allure CLI
```

Both workflows upload `allure-results` as a build artifact.

## Layout

```
src/
  client/      transport (BaseClient) and endpoint methods (GithubClient)
  schemas/     pydantic models: user, repo, issue, error envelope
  config.py    pydantic-settings, reads .env
tests/
  contract/    pact consumer + provider verification
  positive/    happy paths with schema validation
  negative/    401/404/422, hostile input, method masking
  rate_limit/  live header checks + respx-mocked 403/429
```

## License

MIT
