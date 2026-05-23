"""Unit tests for the applyhome.co.kr adapters (APT and Remndr boards)."""
from __future__ import annotations

from pathlib import Path

from src.sites.applyhome import ApplyhomeApt, ApplyhomeRemndr

FIX = Path("tests/fixtures")
APT_URL = f"file://{FIX / 'applyhome_apt_sample.html'}"
REMNDR_URL = f"file://{FIX / 'applyhome_remndr_sample.html'}"


def test_apt_fetches_all_rows():
    posts = ApplyhomeApt(key="applyhome_apt", url=APT_URL).fetch()
    # The fixture is a page of 10 rows; allow ≥5 to keep the test stable
    # across page-size config drift.
    assert len(posts) >= 5


def test_apt_first_post_has_expected_fields():
    posts = ApplyhomeApt(key="applyhome_apt", url=APT_URL).fetch()
    p = posts[0]
    assert p.id == "2026000219"
    assert p.title == "호반써밋 풍무Ⅱ"
    assert p.url == (
        "https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancDetail.do"
        "?houseManageNo=2026000219&pblancNo=2026000219"
    )
    assert p.date == "2026-05-22"
    assert p.site_key == "applyhome_apt"


def test_apt_title_does_not_include_new_image_alt():
    posts = ApplyhomeApt(key="applyhome_apt", url=APT_URL).fetch()
    for p in posts:
        assert "NEW" not in p.title


def test_remndr_uses_remndr_specific_detail_url():
    posts = ApplyhomeRemndr(key="applyhome_remndr", url=REMNDR_URL).fetch()
    assert posts
    for p in posts:
        assert "selectAPTRemndrLttotPblancDetailView.do" in p.url
        assert "houseManageNo=" in p.url and "pblancNo=" in p.url


def test_remndr_first_post_has_expected_fields():
    posts = ApplyhomeRemndr(key="applyhome_remndr", url=REMNDR_URL).fetch()
    p = posts[0]
    assert p.id == "2026930017"
    assert p.title == "레이카운티"
    assert p.date == "2026-05-22"
    assert p.site_key == "applyhome_remndr"


def test_remndr_handles_multiple_category_rows():
    """Fixture contains '무순위(사후)' / '불법행위 재공급' / '취소후재공급'
    rows; verify each yields a parseable post with numeric id."""
    posts = ApplyhomeRemndr(key="applyhome_remndr", url=REMNDR_URL).fetch()
    assert len(posts) >= 5
    for p in posts:
        assert p.id.isdigit()
        assert p.title


def test_empty_table_returns_empty_list(tmp_path):
    empty = tmp_path / "empty.html"
    empty.write_text("<html><body><table></table></body></html>", encoding="utf-8")
    assert ApplyhomeApt(key="applyhome_apt", url=f"file://{empty}").fetch() == []


def test_region_filter_drops_non_allowed_rows():
    """allowed_regions=['서울','경기'] should drop e.g. ``강원``/``부산`` rows."""
    all_posts = ApplyhomeApt(key="applyhome_apt", url=APT_URL).fetch()
    filtered = ApplyhomeApt(
        key="applyhome_apt",
        url=APT_URL,
        allowed_regions=["서울", "경기"],
    ).fetch()
    # Fixture has non-수도권 rows (강원, etc.) — count must drop.
    assert len(filtered) < len(all_posts)
    assert filtered  # but not to zero


def test_region_filter_disabled_by_default():
    """Backward-compat: no allowed_regions => same result as before."""
    default = ApplyhomeApt(key="applyhome_apt", url=APT_URL).fetch()
    explicit_none = ApplyhomeApt(
        key="applyhome_apt", url=APT_URL, allowed_regions=None
    ).fetch()
    assert [p.id for p in default] == [p.id for p in explicit_none]


def test_remndr_region_filter_applies():
    all_posts = ApplyhomeRemndr(key="applyhome_remndr", url=REMNDR_URL).fetch()
    filtered = ApplyhomeRemndr(
        key="applyhome_remndr",
        url=REMNDR_URL,
        allowed_regions=["서울", "경기"],
    ).fetch()
    assert len(filtered) < len(all_posts)
    assert filtered
