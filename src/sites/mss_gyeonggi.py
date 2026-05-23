"""Adapter for the Gyeonggi MSS bulletin board.

Site: https://www.mss.go.kr/site/gyeonggi/ex/bbs/List.do?cbIdx=323
Notes:
- Detail page URLs are not in <a href>; <a> uses "#view" and the real
  reference is in the onclick attribute as
  ``doBbsFView('<cbIdx>','<bcIdx>', ...)``.
- We rebuild ``View.do?cbIdx=...&bcIdx=...`` for the message link.
- Date cells are rendered as ``YYYY.MM.DD``; normalized to ``YYYY-MM-DD``.
"""
from __future__ import annotations

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from src.sites.base import Post, SiteAdapter

ONCLICK_PATTERN = re.compile(r"doBbsFView\('(\d+)','(\d+)'")
DETAIL_BASE = "https://www.mss.go.kr/site/gyeonggi/ex/bbs/View.do"
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)
DEFAULT_TIMEOUT = 15


class MssGyeonggi(SiteAdapter):
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
        # selectors accepted for dispatcher API symmetry; unused
        self._selectors = selectors or {}
        self._user_agent = user_agent
        self._timeout = timeout

    def fetch(self) -> list[Post]:
        html = self._load_html()
        soup = BeautifulSoup(html, "lxml")
        posts: list[Post] = []
        for tr in soup.select("table tbody tr"):
            onclick = tr.get("onclick") or ""
            m = ONCLICK_PATTERN.search(onclick)
            if not m:
                continue
            cb_idx, bc_idx = m.group(1), m.group(2)
            anchor = tr.select_one("td.subject a")
            if anchor is None:
                continue
            title = anchor.get_text(strip=True)
            if not title:
                continue
            tds = tr.select("td")
            raw_date = tds[4].get_text(strip=True) if len(tds) >= 5 else ""
            date = raw_date.replace(".", "-")
            posts.append(
                Post(
                    id=bc_idx,
                    title=title,
                    url=f"{DETAIL_BASE}?cbIdx={cb_idx}&bcIdx={bc_idx}",
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
