"""GitHub REST API v3 endpoint methods.

Every method returns a raw ``httpx.Response``: response validation is a test
concern, and hiding status codes behind the client would make negative
scenarios impossible to express.
"""

import httpx

from src.client.base_client import BaseClient


class GithubClient(BaseClient):
    def get_user(self, username: str) -> httpx.Response:
        return self.request("GET", f"/users/{username}")

    def get_repo(self, owner: str, repo: str) -> httpx.Response:
        return self.request("GET", f"/repos/{owner}/{repo}")

    def list_issues(self, owner: str, repo: str, **params) -> httpx.Response:
        return self.request("GET", f"/repos/{owner}/{repo}/issues", params=params)

    def search_repositories(self, query: str, **params) -> httpx.Response:
        return self.request("GET", "/search/repositories", params={"q": query, **params})

    def get_rate_limit(self) -> httpx.Response:
        return self.request("GET", "/rate_limit")
