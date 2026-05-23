"""Adapter for the applyhome.co.kr (KAB Subscription HOME) bulletin boards.

Site: https://www.applyhome.co.kr/
Notes:
- Two boards are exposed by this module: the APT 분양/임대 board (which
  includes 신혼/생애최초/신생아 special supply) and the APT 무순위/잔여세대
  board (무순위/사후, 취소후재공급, 불법행위 재공급). Both share the same
  row structure ``<tr data-hmno=.. data-pbno=.. data-honm=..>`` so the
  parsing lives in :class:`Applyhome`; subclasses only override
  ``DETAIL_BASE`` because each board has a distinct detail endpoint.
- Title anchors use ``href="#"``; the actual detail page is opened by a
  JS-built form POST. The same endpoint responds to GET with
  ``houseManageNo=<X>&pblancNo=<X>`` and returns the full bulletin page,
  so Telegram links use that GET form.
- The 모집공고일 column sits at a different td index per board (APT=td[6],
  REMNDR=td[4]), so the date is located by scanning each row for the first
  ``YYYY-MM-DD`` cell text rather than a fixed index.
- 지역(공급지역) is td[0] on both boards (단축형: ``서울``/``경기``/``강원``...).
  Optional ``allowed_regions`` keyword filters rows by ``region_passes`` so
  yaml can scope the alerts to e.g. ``[서울, 경기]``.
"""
from __future__ import annotations

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from src.sites.base import Post, SiteAdapter, region_passes

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)
DEFAULT_TIMEOUT = 15


class Applyhome(SiteAdapter):
    """Shared base for applyhome.co.kr list boards.

    Concrete subclasses must set :attr:`DETAIL_BASE` to a GET-accessible
    detail endpoint that accepts ``houseManageNo`` and ``pblancNo``.
    """

    DETAIL_BASE: str = ""

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

    def fetch(self) -> list[Post]:
        html = self._load_html()
        soup = BeautifulSoup(html, "lxml")
        posts: list[Post] = []
        for tr in soup.select("tr[data-hmno][data-pbno]"):
            hmno = (tr.get("data-hmno") or "").strip()
            pbno = (tr.get("data-pbno") or hmno).strip()
            if not hmno:
                continue
            tds = tr.find_all("td")
            region = tds[0].get_text(strip=True) if tds else ""
            if not region_passes(region, self._allowed_regions):
                continue
            anchor = tr.select_one("td.txt_l a")
            if anchor is None:
                continue
            title = anchor.get_text(strip=True)
            if not title:
                continue
            date = ""
            for td in tds:
                text = td.get_text(strip=True)
                if DATE_PATTERN.match(text):
                    date = text
                    break
            posts.append(
                Post(
                    id=hmno,
                    title=title,
                    url=f"{self.DETAIL_BASE}?houseManageNo={hmno}&pblancNo={pbno}",
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


class ApplyhomeApt(Applyhome):
    """APT 분양/임대 board (민영/공공 분양 + 신혼/생애최초/신생아 특별공급)."""

    DETAIL_BASE = (
        "https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancDetail.do"
    )


class ApplyhomeRemndr(Applyhome):
    """APT 무순위/잔여세대 board (무순위 사후, 취소후재공급, 불법행위 재공급)."""

    DETAIL_BASE = (
        "https://www.applyhome.co.kr/ai/aia/selectAPTRemndrLttotPblancDetailView.do"
    )
