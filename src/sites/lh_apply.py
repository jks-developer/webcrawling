"""Adapter for the LH 청약플러스 (apply.lh.or.kr) 공고문 boards.

Site: https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=<menuId>
Boards covered (one yaml entry per ``mi`` value):
- ``mi=1026`` — 임대주택 (국민/매입/공공임대/특별공급)
- ``mi=1027`` — 분양주택 (공공분양 + 특별공급)

Notes:
- Cold-session GET works; no session warmup or Referer needed.
- Each row exposes ``<a class="wrtancInfoBtn" data-id1=panId data-id2=ccrCnntSysDsCd
  data-id3=uppAisTpCd data-id4=aisTpCd>``. Detail page is reached via GET
  ``selectWrtancInfo.do?panId=..&ccrCnntSysDsCd=..&uppAisTpCd=..&aisTpCd=..&mi=..``.
- Title sits in the anchor's ``<span>`` with an optional ``<em class="day">``
  marker like "1일전" that must be stripped.
- Region (td[3]) values are full-form like ``서울특별시``/``경기도``/``대구광역시 외``.
  Date column (td[5]) is ``YYYY.MM.DD``; normalized to ``YYYY-MM-DD``.
- Optional ``allowed_regions`` keyword filters rows whose region clearly
  belongs to a non-listed area. Substring match with fail-open for missing /
  multi-area markers (see :func:`region_passes`).
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from src.sites.base import Post, SiteAdapter, region_passes

LIST_DATE_PATTERN = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2})$")
DETAIL_BASE = (
    "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do"
)
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)
DEFAULT_TIMEOUT = 15


class LHApply(SiteAdapter):
    """LH 청약플러스 list-board adapter (임대 / 분양 공통)."""

    def __init__(
        self,
        key: str,
        url: str,
        selectors: dict[str, str] | None = None,
        allowed_regions: list[str] | None = None,
        user_agent: str = DEFAULT_UA,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.key = key
        self.url = url
        self._selectors = selectors or {}
        self._allowed_regions = list(allowed_regions) if allowed_regions else None
        self._user_agent = user_agent
        self._timeout = timeout
        self._mi = _extract_mi(url)

    def fetch(self) -> list[Post]:
        html = self._load_html()
        soup = BeautifulSoup(html, "lxml")
        posts: list[Post] = []
        for tr in soup.select("table tbody tr"):
            anchor = tr.select_one("a.wrtancInfoBtn")
            if anchor is None:
                continue
            pan_id = (anchor.get("data-id1") or "").strip()
            ccr = (anchor.get("data-id2") or "").strip()
            upp = (anchor.get("data-id3") or "").strip()
            ais = (anchor.get("data-id4") or "").strip()
            if not pan_id:
                continue
            title = _extract_title(anchor)
            if not title:
                continue
            tds = tr.find_all("td")
            region = tds[3].get_text(strip=True) if len(tds) > 3 else ""
            if not region_passes(region, self._allowed_regions):
                continue
            date = (
                _normalize_date(tds[5].get_text(strip=True))
                if len(tds) > 5
                else ""
            )
            posts.append(
                Post(
                    id=pan_id,
                    title=title,
                    url=_detail_url(pan_id, ccr, upp, ais, self._mi),
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
            r.encoding = "utf-8"
            return r.text
        path = self.url[len("file://"):] if self.url.startswith("file://") else self.url
        return Path(path).read_text(encoding="utf-8")


def _extract_title(anchor) -> str:
    span = anchor.find("span")
    if span is None:
        return anchor.get_text(strip=True)
    # Remove the "1일전" / "n일전" / new-marker em before reading the text.
    for em in span.find_all("em"):
        em.decompose()
    return span.get_text(strip=True)


def _normalize_date(raw: str) -> str:
    m = LIST_DATE_PATTERN.match(raw.strip())
    if not m:
        return ""
    yyyy, mm, dd = m.groups()
    return f"{yyyy}-{mm}-{dd}"


def _extract_mi(url: str) -> str:
    """Pull the menu id (``mi``) param out of the list URL; '' if absent."""
    try:
        qs = parse_qs(urlparse(url).query)
    except ValueError:
        return ""
    values = qs.get("mi", [])
    return values[0] if values else ""


def _detail_url(pan_id: str, ccr: str, upp: str, ais: str, mi: str) -> str:
    params = [
        f"panId={pan_id}",
        f"ccrCnntSysDsCd={ccr}",
        f"uppAisTpCd={upp}",
        f"aisTpCd={ais}",
    ]
    if mi:
        params.append(f"mi={mi}")
    return f"{DETAIL_BASE}?" + "&".join(params)
