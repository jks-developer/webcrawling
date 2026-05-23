"""Adapter for the Gyeonggi Housing & Urban Development Corp. (GH) board.

Site: https://www.gh.or.kr/gh/announcement-of-salerental001.do
Notes:
- The board lives in ``<table class="board-list-table">``. Each row has 7 td
  cells: [no, category, title+link, dept, date(YY.MM.DD), views, attach].
- Title anchor uses a relative href like
  ``?mode=view&articleNo=64865&article.offset=0&articleLimit=10``.
  We resolve it against the list URL and key the post by ``articleNo``.
- Dates render as ``YY.MM.DD``; normalized to ``20YY-MM-DD``.
"""
from __future__ import annotations

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from src.sites.base import Post, SiteAdapter

ARTICLE_NO_PATTERN = re.compile(r"articleNo=(\d+)")
DETAIL_BASE = "https://www.gh.or.kr/gh/announcement-of-salerental001.do"
DATE_PATTERN = re.compile(r"^(\d{2})\.(\d{2})\.(\d{2})$")
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)
DEFAULT_TIMEOUT = 15


class GHGyeonggi(SiteAdapter):
    def __init__(
        self,
        key: str,
        url: str,
        selectors: dict[str, str] | None = None,
        user_agent: str = DEFAULT_UA,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.key = key
        self.url = url
        self._selectors = selectors or {}
        self._user_agent = user_agent
        self._timeout = timeout

    def fetch(self) -> list[Post]:
        html = self._load_html()
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table", class_="board-list-table")
        if table is None:
            return []

        posts: list[Post] = []
        rows = table.select("tbody tr") or table.find_all("tr")[1:]
        for tr in rows:
            tds = tr.find_all("td")
            if len(tds) < 5:
                continue
            anchor = tds[2].find("a")
            if anchor is None:
                continue
            href = anchor.get("href") or ""
            m = ARTICLE_NO_PATTERN.search(href)
            if not m:
                continue
            article_no = m.group(1)
            title = anchor.get_text(strip=True)
            if not title:
                continue
            absolute_url = f"{DETAIL_BASE}?mode=view&articleNo={article_no}"
            date = _normalize_date(tds[4].get_text(strip=True))
            posts.append(
                Post(
                    id=article_no,
                    title=title,
                    url=absolute_url,
                    date=date,
                    site_key=self.key,
                )
            )
        return posts

    def _load_html(self) -> str:
        if self.url.startswith(("http://", "https://")):
            r = requests.get(
                self.url,
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
            r.raise_for_status()
            return r.text
        path = self.url[len("file://"):] if self.url.startswith("file://") else self.url
        return Path(path).read_text(encoding="utf-8")


def _normalize_date(raw: str) -> str:
    m = DATE_PATTERN.match(raw.strip())
    if not m:
        return ""
    yy, mm, dd = m.groups()
    return f"20{yy}-{mm}-{dd}"
