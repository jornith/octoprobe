"""Schemas for repository payloads and repository search responses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl

from src.schemas.user import UserSummary


class LicenseSummary(BaseModel):
    key: str
    name: str
    spdx_id: str | None = None
    url: HttpUrl | None = None


class GithubRepo(BaseModel):
    """Repository object from ``GET /repos/{owner}/{repo}`` and search items.

    ``language`` and ``license`` stay optional: plenty of real repositories
    (including GitHub's own ``octocat/Hello-World``) carry null there.
    """

    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: UserSummary
    html_url: HttpUrl
    url: HttpUrl
    description: str | None = None
    fork: bool
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime | None = None
    homepage: str | None = None
    size: int
    stargazers_count: int
    watchers_count: int
    language: str | None = None
    forks_count: int
    open_issues_count: int
    license: LicenseSummary | None = None
    visibility: Literal["public", "private", "internal"]
    default_branch: str
    archived: bool
    disabled: bool


class RepoSearchResponse(BaseModel):
    """Envelope of ``GET /search/repositories``."""

    total_count: int
    incomplete_results: bool
    items: list[GithubRepo]
