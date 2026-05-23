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


# Region strings that should fail-open: either we cannot tell which regions
# are included, or the post explicitly spans multiple areas. Used by
# adapters whose source board is nationwide (applyhome, LH).
REGION_FAIL_OPEN = {"", "-", "전국", "수도권", "공통"}


def region_passes(region: str, allowed: list[str] | None) -> bool:
    """Return True if a row's region column should pass the filter.

    Policy:
    - ``allowed`` is None or empty -> filter disabled, pass everything.
    - Empty / placeholder / nationwide markers (전국, 수도권, …) -> fail-open.
    - "OOO 외" multi-area markers -> fail-open (e.g. ``인천광역시 외`` can
      include 부천 which is 경기). Caller may filter further by title.
    - Otherwise: substring match against ``allowed`` (so ``서울`` matches
      both ``서울`` and ``서울특별시``).
    """
    if not allowed:
        return True
    r = region.strip()
    if r in REGION_FAIL_OPEN:
        return True
    if "외" in r:
        return True
    return any(k in r for k in allowed)
