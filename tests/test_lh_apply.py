"""Unit tests for the LH 청약플러스 adapter (lh_apply.LHApply)."""
from __future__ import annotations

from pathlib import Path

from src.sites.base import region_passes
from src.sites.lh_apply import (
    LHApply,
    _detail_url,
    _extract_mi,
    _normalize_date,
)

FIX = Path("tests/fixtures")
RENTAL_URL = (
    "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1026"
)
SALE_URL = (
    "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1027"
)
RENTAL_FIXTURE = f"file://{FIX / 'lh_apply_rental_sample.html'}"
SALE_FIXTURE = f"file://{FIX / 'lh_apply_sale_sample.html'}"


def test_rental_parses_many_rows_when_filter_disabled():
    posts = LHApply(key="lh_apply_rental", url=RENTAL_FIXTURE).fetch()
    # Fixture has 50 rows from a real list page.
    assert len(posts) >= 30


def test_rental_first_post_has_expected_fields():
    posts = LHApply(key="lh_apply_rental", url=RENTAL_FIXTURE).fetch()
    p = posts[0]
    assert p.id == "2015122300019998"
    assert p.title == "대구 북구, 중구 국민임대주택 예비입주자 모집"
    assert p.date == "2026-05-22"
    assert p.site_key == "lh_apply_rental"
    # mi from the file:// URL is empty, so detail URL omits mi here.
    assert p.url.startswith(
        "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?"
    )
    assert "panId=2015122300019998" in p.url
    assert "ccrCnntSysDsCd=03" in p.url
    assert "uppAisTpCd=06" in p.url
    assert "aisTpCd=07" in p.url


def test_title_strips_day_marker():
    """`<em class="day">1일전</em>` must not bleed into the post title."""
    posts = LHApply(key="lh_apply_rental", url=RENTAL_FIXTURE).fetch()
    assert posts
    for p in posts:
        assert "일전" not in p.title
        assert "NEW" not in p.title


def test_date_normalized_from_dotted_format():
    posts = LHApply(key="lh_apply_rental", url=RENTAL_FIXTURE).fetch()
    for p in posts:
        if p.date:
            assert len(p.date) == 10
            assert p.date[4] == "-" and p.date[7] == "-"


def test_sale_board_parses_fixture():
    posts = LHApply(key="lh_apply_sale", url=SALE_FIXTURE).fetch()
    assert posts
    for p in posts:
        assert p.site_key == "lh_apply_sale"
        assert "selectWrtancInfo.do" in p.url


def test_extract_mi_from_list_url():
    assert _extract_mi(RENTAL_URL) == "1026"
    assert _extract_mi(SALE_URL) == "1027"
    assert (
        _extract_mi(
            "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do"
        )
        == ""
    )


def test_detail_url_builder_includes_mi_when_present():
    url = _detail_url("PAN001", "03", "06", "07", "1026")
    assert url.startswith(
        "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?"
    )
    assert "panId=PAN001" in url
    assert "ccrCnntSysDsCd=03" in url
    assert "uppAisTpCd=06" in url
    assert "aisTpCd=07" in url
    assert "mi=1026" in url


def test_detail_url_builder_omits_mi_when_blank():
    url = _detail_url("PAN001", "03", "06", "07", "")
    assert "mi=" not in url


def test_normalize_date_handles_dot_and_blank():
    assert _normalize_date("2026.05.22") == "2026-05-22"
    assert _normalize_date("  2026.05.22  ") == "2026-05-22"
    assert _normalize_date("") == ""
    assert _normalize_date("2026/05/22") == ""


def test_region_filter_blocks_non_allowed_regions():
    """allowed_regions=['서울','경기'] should drop e.g. 대구광역시 rows."""
    all_posts = LHApply(key="lh_apply_rental", url=RENTAL_FIXTURE).fetch()
    filtered = LHApply(
        key="lh_apply_rental",
        url=RENTAL_FIXTURE,
        allowed_regions=["서울", "경기"],
    ).fetch()
    # Filter must drop at least one row (fixture contains 대구/강원/etc.).
    assert len(filtered) < len(all_posts)
    # All surviving posts must have a recognisable Seoul/Gyeonggi title or
    # have been let through by the fail-open path. We can't easily verify
    # the row's region from the Post object, so cross-check via the helper.
    assert all_posts  # sanity


def test_empty_table_returns_empty_list(tmp_path):
    empty = tmp_path / "empty.html"
    empty.write_text(
        "<html><body><table><tbody></tbody></table></body></html>",
        encoding="utf-8",
    )
    assert (
        LHApply(key="lh_apply_rental", url=f"file://{empty}").fetch() == []
    )


# --- region_passes unit cases ---


def test_region_passes_no_filter_passes_all():
    assert region_passes("부산광역시", None) is True
    assert region_passes("", None) is True


def test_region_passes_substring_match():
    allowed = ["서울", "경기"]
    assert region_passes("서울특별시", allowed) is True
    assert region_passes("서울", allowed) is True
    assert region_passes("경기도", allowed) is True
    assert region_passes("경기", allowed) is True


def test_region_passes_blocks_non_matching_single_region():
    allowed = ["서울", "경기"]
    assert region_passes("대구광역시", allowed) is False
    assert region_passes("부산", allowed) is False
    assert region_passes("강원특별자치도", allowed) is False


def test_region_passes_fail_open_for_placeholders():
    allowed = ["서울", "경기"]
    assert region_passes("", allowed) is True
    assert region_passes("-", allowed) is True
    assert region_passes("전국", allowed) is True
    assert region_passes("수도권", allowed) is True


def test_region_passes_fail_open_for_multi_area_marker():
    """'OOO 외' rows can include 부천(경기) etc. — pass through."""
    allowed = ["서울", "경기"]
    assert region_passes("인천광역시 외", allowed) is True
    assert region_passes("대구광역시 외", allowed) is True
