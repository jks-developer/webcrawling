from __future__ import annotations

from src.filter import apply_filter
from src.sites.base import Post


def _post(title: str, pid: str = "1") -> Post:
    return Post(id=pid, title=title, url="http://x", date="2026-05-23", site_key="s")


def test_empty_filters_keep_all():
    posts = [_post("청약 모집공고"), _post("당첨자 발표")]
    assert apply_filter(posts, [], []) == posts


def test_include_only_keeps_matches():
    posts = [_post("청약 1순위 모집"), _post("그냥 공지")]
    result = apply_filter(posts, ["청약"], [])
    assert [p.title for p in result] == ["청약 1순위 모집"]


def test_exclude_only_drops_matches():
    posts = [_post("청약 1순위 모집"), _post("당첨자 발표")]
    result = apply_filter(posts, [], ["당첨자"])
    assert [p.title for p in result] == ["청약 1순위 모집"]


def test_include_and_exclude_combine_with_and():
    posts = [
        _post("청약 1순위 모집"),       # include yes, exclude no  -> keep
        _post("청약 당첨자 발표"),       # include yes, exclude yes -> drop
        _post("그냥 공지"),              # include no               -> drop
    ]
    result = apply_filter(posts, ["청약"], ["당첨자"])
    assert [p.title for p in result] == ["청약 1순위 모집"]


def test_case_insensitive_matching():
    posts = [_post("NEW Application opens")]
    assert apply_filter(posts, ["application"], []) == posts
    assert apply_filter(posts, [], ["APPLICATION"]) == []


def test_substring_matching():
    posts = [_post("재청약공고문")]
    assert apply_filter(posts, ["청약"], []) == posts


def test_empty_keyword_strings_are_ignored():
    posts = [_post("anything")]
    # 빈 문자열은 모든 문자열의 부분문자열이라 잘못 동작할 수 있어 무시되어야 함
    assert apply_filter(posts, [""], []) == posts
    assert apply_filter(posts, [], [""]) == posts
