"""Adapter for the SH Seoul Housing & Communities Corp. bulletin board.

Site: https://www.i-sh.co.kr/main/lay2/program/S1T294C297/www/brd/m_247/list.do
Notes:
- Detail links use ``onclick="javascript:getDetailView('SEQ');return false;"``
  with ``href="#"``. The post list lives in the second ``<table>`` on the page.
- The detail page is reachable via GET ``view.do?seq=<seq>`` (confirmed).
- Dates render as ``YYYY-MM-DD`` already, no normalization needed.
"""
from __future__ import annotations

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from src.sites.base import Post, SiteAdapter

ONCLICK_PATTERN = re.compile(r"getDetailView\('(\d+)'\)")
DETAIL_BASE = (
    "https://www.i-sh.co.kr/main/lay2/program/S1T294C297/www/brd/m_247/view.do"
)
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)
DEFAULT_TIMEOUT = 15


class SHSeoul(SiteAdapter):
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
        # The post list is the table whose rows carry getDetailView() handlers.
        post_table = None
        for table in soup.find_all("table"):
            if table.find("a", onclick=ONCLICK_PATTERN):
                post_table = table
                break
        if post_table is None:
            return []

        posts: list[Post] = []
        rows = post_table.select("tbody tr") or post_table.find_all("tr")[1:]
        for tr in rows:
            anchor = tr.find("a", onclick=ONCLICK_PATTERN)
            if anchor is None:
                continue
            m = ONCLICK_PATTERN.search(anchor.get("onclick") or "")
            if not m:
                continue
            seq = m.group(1)
            title = anchor.get_text(strip=True)
            if not title:
                continue
            tds = tr.find_all("td")
            date = tds[3].get_text(strip=True) if len(tds) >= 4 else ""
            posts.append(
                Post(
                    id=seq,
                    title=title,
                    url=f"{DETAIL_BASE}?seq={seq}",
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
