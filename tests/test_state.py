from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.state import MAX_PER_SITE, State, load_state, save_state


def test_load_missing_file_returns_empty_state(tmp_path: Path):
    state = load_state(tmp_path / "does_not_exist.json")
    assert state.to_dict() == {}


def test_load_empty_file_returns_empty_state(tmp_path: Path):
    p = tmp_path / "empty.json"
    p.write_text("", encoding="utf-8")
    state = load_state(p)
    assert state.to_dict() == {}


def test_load_invalid_json_raises(tmp_path: Path):
    p = tmp_path / "invalid.json"
    p.write_text("not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_state(p)


def test_load_non_object_root_raises(tmp_path: Path):
    p = tmp_path / "array.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError):
        load_state(p)


def test_mark_and_is_seen():
    s = State()
    assert not s.is_seen("site", "a")
    s.mark_seen("site", ["a", "b"])
    assert s.is_seen("site", "a")
    assert s.is_seen("site", "b")
    assert not s.is_seen("site", "c")


def test_mark_seen_is_idempotent_and_preserves_order():
    s = State()
    s.mark_seen("site", ["a", "b"])
    s.mark_seen("site", ["b", "c"])  # b is dup
    assert s.to_dict()["site"] == ["a", "b", "c"]


def test_filter_unseen():
    s = State({"site": ["a", "b"]})
    assert s.filter_unseen("site", ["a", "c", "d"]) == ["c", "d"]
    assert s.filter_unseen("other_site", ["x"]) == ["x"]


def test_cap_evicts_oldest():
    s = State()
    ids = [f"id{i}" for i in range(MAX_PER_SITE + 5)]
    s.mark_seen("site", ids)
    stored = s.to_dict()["site"]
    assert len(stored) == MAX_PER_SITE
    assert stored[0] == "id5"           # oldest 5 evicted
    assert stored[-1] == f"id{MAX_PER_SITE + 4}"


def test_save_then_load_roundtrip(tmp_path: Path):
    p = tmp_path / "state.json"
    s = State()
    s.mark_seen("site_a", ["1", "2"])
    s.mark_seen("site_b", ["x"])
    save_state(s, p)

    loaded = load_state(p)
    assert loaded.to_dict() == {"site_a": ["1", "2"], "site_b": ["x"]}


def test_save_creates_parent_dirs(tmp_path: Path):
    p = tmp_path / "nested" / "dir" / "state.json"
    save_state(State({"k": ["v"]}), p)
    assert p.exists()
    assert json.loads(p.read_text(encoding="utf-8")) == {"k": ["v"]}


def test_save_uses_utf8_and_preserves_korean(tmp_path: Path):
    p = tmp_path / "state.json"
    save_state(State({"청약": ["가나다"]}), p)
    text = p.read_text(encoding="utf-8")
    assert "청약" in text
    assert "가나다" in text
