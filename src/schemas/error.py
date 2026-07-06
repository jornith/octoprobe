"""Schema for GitHub error bodies (4xx responses)."""

from typing import Any

from pydantic import BaseModel


class GithubErrorResponse(BaseModel):
    """Error envelope GitHub attaches to 4xx responses.

    ``status`` arrives as a *string* (e.g. ``"404"``), matching current API
    behaviour. ``errors`` shows up on 422 validation failures only.
    """

    message: str
    documentation_url: str | None = None
    status: str | None = None
    errors: list[dict[str, Any]] | None = None
