"""Title-based include/exclude keyword filtering.

Rule:
- match is case-insensitive substring.
- if `include` is empty, every post passes the include stage.
- a post is kept iff (include stage passed) AND (no exclude keyword matches).
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

from src.sites.base import Post


def apply_filter(
    posts: Iterable[Post],
    include: Sequence[str],
    exclude: Sequence[str],
) -> list[Post]:
    include_norm = [k.lower() for k in include if k]
    exclude_norm = [k.lower() for k in exclude if k]

    kept: list[Post] = []
    for post in posts:
        title_lc = post.title.lower()
        if include_norm and not any(k in title_lc for k in include_norm):
            continue
        if any(k in title_lc for k in exclude_norm):
            continue
        kept.append(post)
    return kept
