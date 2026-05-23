from __future__ import annotations

from pathlib import Path

import pytest

from src.sites.example_site import ExampleSite

FIXTURE = Path(__file__).parent / "fixtures" / "sample.html"

SELECTORS = {
    "row": "tr.item",
    "title": "a.title",
    "link": "a.title@href",
    "id": "a.title@data-id",
    "date": "td.date",
}


def _build() -> ExampleSite:
    return ExampleSite(key="example", url=str(FIXTURE), selectors=SELECTORS)


def test_fetch_returns_all_rows():
    posts = _build().fetch()
    assert len(posts) == 3


def test_post_fields_populated():
    posts = _build().fetch()
    first = posts[0]
    assert first.id == "1001"
    assert first.title == "청약 1순위 모집공고 (○○ 아파트)"
    assert first.url == "https://example.com/p/1001"
    assert first.date == "2026-05-23"
    assert first.site_key == "example"


def test_ids_are_unique_for_distinct_rows():
    posts = _build().fetch()
    assert len({p.id for p in posts}) == len(posts)


def test_file_url_prefix_is_accepted():
    site = ExampleSite(key="example", url=f"file://{FIXTURE}", selectors=SELECTORS)
    assert len(site.fetch()) == 3


def test_id_falls_back_to_url_when_id_selector_missing():
    sel = {k: v for k, v in SELECTORS.items() if k != "id"}
    posts = ExampleSite(key="example", url=str(FIXTURE), selectors=sel).fetch()
    assert posts[0].id == posts[0].url


def test_missing_required_selector_raises():
    with pytest.raises(ValueError, match="missing"):
        ExampleSite(key="example", url=str(FIXTURE), selectors={"row": "x"})
