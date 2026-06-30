"""Schemas for issue payloads returned by ``GET /repos/{owner}/{repo}/issues``."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, HttpUrl

from src.schemas.user import UserSummary


class IssueLabel(BaseModel):
    id: int
    name: str
    color: str
    default: bool
    description: str | None = None


class GithubIssue(BaseModel):
    """A single issue.

    The list endpoint also returns pull requests (a documented GitHub quirk);
    those items carry a ``pull_request`` key, kept here so tests can tell the
    two apart instead of failing on "unexpected" rows.
    """

    id: int
    node_id: str
    number: int
    title: str
    user: UserSummary
    state: Literal["open", "closed"]
    locked: bool
    comments: int
    html_url: HttpUrl
    labels: list[IssueLabel]
    assignee: UserSummary | None = None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None
    body: str | None = None
    pull_request: dict[str, Any] | None = None
