"""Generic CSS-selector-based site adapter.

The adapter takes a URL (http(s):// or local file path) and a selector
mapping, and emits `Post` objects.  Selectors use a simple
``css-selector[@attr]`` syntax: if ``@attr`` is present, the attribute
value is extracted; otherwise the element's text content is used.
"""
from __future__ import annotations

from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

from src.sites.base import Post, SiteAdapter

DEFAULT_UA = "webcrawling-notifier/0.1 (+https://github.com/jks-developer/webcrawling)"
DEFAULT_TIMEOUT = 15


class ExampleSite(SiteAdapter):
    def __init__(
        self,
        key: str,
        url: str,
        selectors: dict[str, str],
        user_agent: str = DEFAULT_UA,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        missing = {"row", "title", "link"} - selectors.keys()
        if missing:
            raise ValueError(f"selectors missing required keys: {sorted(missing)}")
        self.key = key
        self.url = url
        self._sel = selectors
        self._user_agent = user_agent
        self._timeout = timeout

    def fetch(self) -> list[Post]:
        html = self._load_html()
        soup = BeautifulSoup(html, "lxml")
        posts: list[Post] = []
        for row in soup.select(self._sel["row"]):
            title = _extract(row, self._sel["title"])
            url = _extract(row, self._sel["link"])
            if not title or not url:
                continue
            pid = _extract(row, self._sel.get("id", "")) or url
            date = _extract(row, self._sel.get("date", ""))
            posts.append(Post(id=pid, title=title, url=url, date=date, site_key=self.key))
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


def _extract(element: Tag, spec: str) -> str:
    if not spec:
        return ""
    if "@" in spec:
        selector, _, attr = spec.rpartition("@")
    else:
        selector, attr = spec, None
    target = element.select_one(selector) if selector else element
    if target is None:
        return ""
    if attr:
        value = target.get(attr, "")
        return value if isinstance(value, str) else " ".join(value)
    return target.get_text(strip=True)
