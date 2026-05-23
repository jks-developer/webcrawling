from __future__ import annotations

from pathlib import Path

import pytest

from src.config import SiteConfig
from src.crawler import build_adapter, fetch_all
from src.sites.example_site import ExampleSite

FIXTURE = Path(__file__).parent / "fixtures" / "sample.html"

SEL = {
    "row": "tr.item",
    "title": "a.title",
    "link": "a.title@href",
    "id": "a.title@data-id",
    "date": "td.date",
}


def _site(enabled: bool = True, adapter: str = "example_site.ExampleSite") -> SiteConfig:
    return SiteConfig(
        key="example",
        name="예시",
        adapter=adapter,
        url=str(FIXTURE),
        selectors=SEL,
        enabled=enabled,
    )


def test_build_adapter_dispatches_to_correct_class():
    adapter = build_adapter(_site())
    assert isinstance(adapter, ExampleSite)
    assert adapter.key == "example"


def test_build_adapter_rejects_bare_class_name():
    with pytest.raises(ValueError, match="module.ClassName"):
        build_adapter(_site(adapter="ExampleSite"))


def test_build_adapter_raises_on_missing_module():
    with pytest.raises(ModuleNotFoundError):
        build_adapter(_site(adapter="nonexistent_module.X"))


def test_build_adapter_raises_on_missing_class():
    with pytest.raises(AttributeError):
        build_adapter(_site(adapter="example_site.DoesNotExist"))


def test_fetch_all_skips_disabled_sites():
    results = fetch_all([_site(enabled=False)])
    assert results == []


def test_fetch_all_returns_posts_for_enabled_site():
    results = fetch_all([_site(enabled=True)])
    assert len(results) == 1
    r = results[0]
    assert r.site_key == "example"
    assert r.error is None
    assert len(r.posts) == 3


def test_fetch_all_captures_per_site_error_without_aborting():
    broken = SiteConfig(
        key="broken",
        name="broken",
        adapter="example_site.ExampleSite",
        url=str(FIXTURE.with_name("nonexistent.html")),
        selectors=SEL,
        enabled=True,
    )
    results = fetch_all([broken, _site()])
    assert len(results) == 2
    assert results[0].site_key == "broken"
    assert results[0].error is not None
    assert results[1].site_key == "example"
    assert results[1].error is None
    assert len(results[1].posts) == 3
