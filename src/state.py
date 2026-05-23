"""Per-site 'already notified' bookkeeping.

The state file is a JSON object::

    {
      "<site_key>": ["<id1>", "<id2>", ...],   # oldest first
      ...
    }

Each site list is capped at `MAX_PER_SITE` to bound the file size; the
oldest ids are evicted first.  This is safe because boards only ever
move forward in time -- once an old post falls off the visible board,
its id will never appear in a fetch again, so we no longer need it.
"""
from __future__ import annotations

import json
from pathlib import Path

MAX_PER_SITE = 1000


class State:
    def __init__(self, data: dict[str, list[str]] | None = None) -> None:
        self._data: dict[str, list[str]] = {k: list(v) for k, v in (data or {}).items()}

    def is_seen(self, site_key: str, post_id: str) -> bool:
        return post_id in self._data.get(site_key, ())

    def mark_seen(self, site_key: str, post_ids: list[str]) -> None:
        existing = self._data.setdefault(site_key, [])
        seen = set(existing)
        for pid in post_ids:
            if pid not in seen:
                existing.append(pid)
                seen.add(pid)
        if len(existing) > MAX_PER_SITE:
            del existing[: len(existing) - MAX_PER_SITE]

    def filter_unseen(self, site_key: str, post_ids: list[str]) -> list[str]:
        seen = set(self._data.get(site_key, ()))
        return [pid for pid in post_ids if pid not in seen]

    def to_dict(self) -> dict[str, list[str]]:
        return {k: list(v) for k, v in self._data.items()}


def load_state(path: Path | str) -> State:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return State()
    raw = json.loads(p.read_text(encoding="utf-8") or "{}")
    if not isinstance(raw, dict):
        raise ValueError(f"state file {p} is not a JSON object")
    return State(raw)


def save_state(state: State, path: Path | str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(state.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
