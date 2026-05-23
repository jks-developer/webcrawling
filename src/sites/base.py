"""Site adapter base types.

Each crawled site implements `SiteAdapter` and returns a list of `Post`.
The adapter is the only place that knows site-specific HTML structure;
the rest of the pipeline operates on `Post` objects only.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Post:
    id: str           # site-unique identifier (URL, board id, ...)
    title: str
    url: str
    date: str         # YYYY-MM-DD; empty string if unknown
    site_key: str     # key matching config/sites.yml entry


class SiteAdapter(ABC):
    """Adapter contract for one board on one site."""

    #: Identifier matching `sites.yml` entry; used as state bucket key.
    key: str

    @abstractmethod
    def fetch(self) -> list[Post]:
        """Return the current visible list of posts on the board.

        Implementations should:
        - Return newest-first if possible (caller does not require ordering).
        - Raise on transport/parse failures so the orchestrator can log per-site.
        - Not perform any deduplication; that is the orchestrator's job.
        """
