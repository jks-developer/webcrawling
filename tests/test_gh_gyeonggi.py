from __future__ import annotations

from pathlib import Path

from src.sites.gh_gyeonggi import GHGyeonggi

FIXTURE = Path(__file__).parent / "fixtures" / "gh_gyeonggi_sample.html"


def _build() -> GHGyeonggi:
    return GHGyeonggi(key="gh_gyeonggi", url=str(FIXTURE))


def test_fetch_returns_nonempty():
    posts = _build().fetch()
    assert len(posts) >= 1


def test_post_fields_are_populated():
    posts = _build().fetch()
    for p in posts:
        assert p.id, "post id should not be empty"
        assert p.id.isdigit(), f"post id should be digits, got {p.id!r}"
        assert p.title, "title should not be empty"
        assert p.url.startswith("https://www.gh.or.kr/"), p.url
        assert f"articleNo={p.id}" in p.url
        assert p.site_key == "gh_gyeonggi"


def test_date_is_normalized_to_iso():
    posts = _build().fetch()
    for p in posts:
        if not p.date:
            continue
        parts = p.date.split("-")
        assert len(parts) == 3, f"unexpected date format: {p.date}"
        assert len(parts[0]) == 4 and parts[0].startswith("20")
        assert len(parts[1]) == 2 and parts[1].isdigit()
        assert len(parts[2]) == 2 and parts[2].isdigit()


def test_ids_unique():
    posts = _build().fetch()
    ids = [p.id for p in posts]
    assert len(set(ids)) == len(ids), "duplicate post ids found"


def test_file_url_prefix_accepted():
    site = GHGyeonggi(key="gh_gyeonggi", url=f"file://{FIXTURE}")
    assert len(site.fetch()) >= 1
