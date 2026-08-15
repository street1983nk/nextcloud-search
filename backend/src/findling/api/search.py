"""POST /search.

Skeleton for the RED step of plan 01-04 task 2: the wire models exist so the
test suite can import them, but the endpoint, the validation rules and the
container proof are still missing. The GREEN step fills them in.
"""

from fastapi import APIRouter
from pydantic import BaseModel

ROUTER = APIRouter()


class SearchRequest(BaseModel):
    """Request body of the search endpoint."""

    query: str
    limit: int = 20


class Hit(BaseModel):
    """One result in the wire format the PHP companion expects."""

    # fileId stays camelCase: the wire format belongs to the PHP side, and a
    # rename here would silently drop the field on the way out. The naming rules
    # of ruff are not part of the configured rule set, so a noqa directive would
    # itself be a lint error (RUF100); this comment carries the reason instead.
    fileId: int
    path: str
    title: str
    snippet: str
    highlights: list[tuple[int, int]]
    score: float
    mtime: int


def build_canary_hits(user_id: str) -> list[Hit]:
    """Placeholder. The GREEN step produces the container proof here."""
    del user_id
    return []
