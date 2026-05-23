from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.messenger import (
    MAX_MESSAGE_LEN,
    format_summary,
    send_message,
    send_summary,
    split_chunks,
)
from src.sites.base import Post


def _post(pid: str, title: str, site: str = "example", url: str = "https://x.test/p") -> Post:
    return Post(id=pid, title=title, url=f"{url}/{pid}", date="2026-05-23", site_key=site)


# ---------------- format_summary ----------------

def test_format_summary_groups_by_site():
    posts = [
        _post("1", "A", site="s1"),
        _post("2", "B", site="s2"),
        _post("3", "C", site="s1"),
    ]
    out = format_summary(posts, site_names={"s1": "사이트1", "s2": "사이트2"})
    assert "(3건)" in out
    assert "[사이트1]" in out
    assert "[사이트2]" in out
    # A and C grouped under 사이트1
    assert out.index("사이트1") < out.index("A")
    assert out.index("A") < out.index("C")
    assert out.index("사이트2") > out.index("C")


def test_format_summary_escapes_html_in_title():
    posts = [_post("1", "<script>alert(1)</script>")]
    out = format_summary(posts)
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_format_summary_uses_key_when_no_name_mapping():
    out = format_summary([_post("1", "T", site="sitekey")])
    assert "[sitekey]" in out


# ---------------- split_chunks ----------------

def test_split_chunks_short_passthrough():
    assert split_chunks("hi") == ["hi"]


def test_split_chunks_breaks_on_newlines():
    line = "x" * 100
    text = "\n".join([line] * 50)  # ~ 5000+ chars
    chunks = split_chunks(text, limit=1000)
    assert all(len(c) <= 1000 for c in chunks)
    # All lines preserved
    rejoined = "\n".join(chunks)
    assert rejoined.replace("\n", "") == text.replace("\n", "")


def test_split_chunks_default_limit_is_within_telegram_cap():
    assert MAX_MESSAGE_LEN <= 4096


# ---------------- send_message ----------------

def test_send_message_rejects_empty_credentials():
    with pytest.raises(ValueError):
        send_message("hi", token="", chat_id="123")
    with pytest.raises(ValueError):
        send_message("hi", token="t", chat_id="")


@patch("src.messenger.requests.post")
def test_send_message_posts_expected_payload(mock_post: MagicMock):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"ok": True, "result": {}},
        raise_for_status=lambda: None,
    )
    send_message("안녕", token="TOK", chat_id="CID")
    args, kwargs = mock_post.call_args
    assert "/botTOK/sendMessage" in args[0]
    payload = kwargs["json"]
    assert payload["chat_id"] == "CID"
    assert payload["text"] == "안녕"
    assert payload["parse_mode"] == "HTML"
    assert payload["disable_web_page_preview"] is True


@patch("src.messenger.requests.post")
def test_send_message_raises_on_api_error(mock_post: MagicMock):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"ok": False, "description": "bad chat"},
        raise_for_status=lambda: None,
    )
    with pytest.raises(RuntimeError, match="Telegram API error"):
        send_message("x", token="t", chat_id="c")


# ---------------- send_summary ----------------

@patch("src.messenger.requests.post")
def test_send_summary_returns_zero_for_no_posts(mock_post: MagicMock):
    assert send_summary([], token="t", chat_id="c") == 0
    mock_post.assert_not_called()


@patch("src.messenger.requests.post")
def test_send_summary_sends_one_message_for_short_summary(mock_post: MagicMock):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"ok": True, "result": {}},
        raise_for_status=lambda: None,
    )
    n = send_summary([_post("1", "Hello")], token="t", chat_id="c")
    assert n == 1
    assert mock_post.call_count == 1
