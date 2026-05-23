"""Telegram Bot API messenger.

- `send_message`  : raw single-message send with HTML parse mode
- `format_summary`: format a list of posts into one HTML message
- `split_chunks`  : break a long message into Telegram-safe chunks
- `send_summary`  : convenience -- format + split + send
"""
from __future__ import annotations

from html import escape

import requests

from src.sites.base import Post

API_BASE = "https://api.telegram.org"
MAX_MESSAGE_LEN = 4000  # Telegram allows 4096; leave headroom for safety
DEFAULT_TIMEOUT = 15


def send_message(
    text: str,
    token: str,
    chat_id: str,
    *,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> None:
    """POST one message to Telegram. Raises on API error."""
    if not token or not chat_id:
        raise ValueError("token and chat_id must be non-empty")
    r = requests.post(
        f"{API_BASE}/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        },
        timeout=timeout,
    )
    r.raise_for_status()
    body = r.json()
    if not body.get("ok"):
        raise RuntimeError(f"Telegram API error: {body}")


def format_summary(
    posts: list[Post],
    site_names: dict[str, str] | None = None,
    header: str = "📋 오늘의 신규 공고",
) -> str:
    """Group posts by site_key and render an HTML summary message."""
    site_names = site_names or {}
    by_site: dict[str, list[Post]] = {}
    for p in posts:
        by_site.setdefault(p.site_key, []).append(p)

    total = sum(len(v) for v in by_site.values())
    lines: list[str] = [f"{header} ({total}건)"]
    for site_key, group in by_site.items():
        name = site_names.get(site_key, site_key)
        lines.append("")
        lines.append(f"<b>[{escape(name)}]</b>")
        for p in group:
            title = escape(p.title)
            url = escape(p.url, quote=True)
            line = f'• <a href="{url}">{title}</a>'
            if p.date:
                line += f" <i>({escape(p.date)})</i>"
            lines.append(line)
    return "\n".join(lines)


def split_chunks(text: str, limit: int = MAX_MESSAGE_LEN) -> list[str]:
    """Split text by line boundaries so each chunk <= limit chars."""
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in text.split("\n"):
        line_len = len(line) + 1  # +1 for newline
        if current_len + line_len > limit and current:
            chunks.append("\n".join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len
    if current:
        chunks.append("\n".join(current))
    return chunks


def send_summary(
    posts: list[Post],
    token: str,
    chat_id: str,
    site_names: dict[str, str] | None = None,
) -> int:
    """Format `posts` and send to Telegram. Returns number of messages sent."""
    if not posts:
        return 0
    text = format_summary(posts, site_names=site_names)
    chunks = split_chunks(text)
    for chunk in chunks:
        send_message(chunk, token, chat_id)
    return len(chunks)
