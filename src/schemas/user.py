"""Schemas for GitHub user payloads.

Field lists follow the official REST API v3 docs for ``GET /users/{username}``.
``UserSummary`` mirrors the "simple user" object GitHub embeds into repos,
issues and search results.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl


class UserSummary(BaseModel):
    """The trimmed user object embedded in other resources."""

    login: str
    id: int
    node_id: str
    avatar_url: HttpUrl
    html_url: HttpUrl
    url: HttpUrl
    type: Literal["User", "Organization", "Bot"]
    site_admin: bool


class GithubUser(UserSummary):
    """Full public profile returned by ``GET /users/{username}``.

    ``blog`` is typed as ``str`` rather than ``HttpUrl``: GitHub returns an empty
    string (not null) when the field is unset, and accepts values without a scheme.
    """

    name: str | None = None
    company: str | None = None
    blog: str | None = None
    location: str | None = None
    email: str | None = None
    bio: str | None = None
    public_repos: int
    public_gists: int
    followers: int
    following: int
    created_at: datetime
    updated_at: datetime
