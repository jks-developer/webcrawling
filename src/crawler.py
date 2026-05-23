"""Site adapter dispatcher.

Given a ``SiteConfig`` whose ``adapter`` field looks like
``module.ClassName`` (relative to ``src.sites``), builds the adapter
instance and runs its ``fetch()``.  Errors are captured per-site so a
single broken site does not abort the whole run.
"""
from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field

from src.config import SiteConfig
from src.sites.base import Post, SiteAdapter

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    site_key: str
    posts: list[Post] = field(default_factory=list)
    error: Exception | None = None


def build_adapter(site_cfg: SiteConfig) -> SiteAdapter:
    if "." not in site_cfg.adapter:
        raise ValueError(
            f"adapter must be 'module.ClassName', got {site_cfg.adapter!r}"
        )
    module_name, class_name = site_cfg.adapter.rsplit(".", 1)
    module = importlib.import_module(f"src.sites.{module_name}")
    cls = getattr(module, class_name)
    return cls(
        key=site_cfg.key,
        url=site_cfg.url,
        selectors=site_cfg.selectors,
        **site_cfg.options,
    )


def fetch_all(sites: list[SiteConfig]) -> list[FetchResult]:
    results: list[FetchResult] = []
    for site_cfg in sites:
        if not site_cfg.enabled:
            logger.info("skip disabled site: %s", site_cfg.key)
            continue
        try:
            adapter = build_adapter(site_cfg)
            posts = adapter.fetch()
            logger.info("fetched %d posts from %s", len(posts), site_cfg.key)
            results.append(FetchResult(site_cfg.key, posts))
        except Exception as e:  # noqa: BLE001 -- per-site isolation
            logger.exception("fetch failed for %s", site_cfg.key)
            results.append(FetchResult(site_cfg.key, error=e))
    return results
