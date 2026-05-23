"""Configuration loader.

Loads:
- ``config/sites.yml``   -> list[SiteConfig]
- ``config/filters.yml`` -> FilterConfig
- ``.env`` (optional)    -> merged with os.environ for TELEGRAM_*

Secrets resolution order: os.environ first, .env file as fallback.
This means GitHub Actions (Secrets injected into env) overrides any
checked-in .env values, which matters if a stale .env ever ships.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_CONFIG_DIR = Path("config")
DEFAULT_STATE_PATH = Path("data/seen_ids.json")
DEFAULT_ENV_PATH = Path(".env")


@dataclass
class SiteConfig:
    key: str
    name: str
    adapter: str
    url: str
    selectors: dict[str, str]
    enabled: bool = True


@dataclass
class FilterConfig:
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)


@dataclass
class Config:
    sites: list[SiteConfig]
    filters: FilterConfig
    telegram_token: str
    telegram_chat_id: str
    state_path: Path


def parse_dotenv(path: Path) -> dict[str, str]:
    """Tiny .env reader. Ignores comments/blank lines, strips quotes."""
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip().strip('"').strip("'")
        out[key] = value
    return out


def parse_sites(path: Path) -> list[SiteConfig]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sites: list[SiteConfig] = []
    for raw in data.get("sites", []) or []:
        sites.append(
            SiteConfig(
                key=raw["key"],
                name=raw.get("name", raw["key"]),
                adapter=raw["adapter"],
                url=raw["url"],
                selectors=dict(raw.get("selectors", {}) or {}),
                enabled=bool(raw.get("enabled", True)),
            )
        )
    return sites


def parse_filters(path: Path) -> FilterConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return FilterConfig(
        include=list(data.get("include") or []),
        exclude=list(data.get("exclude") or []),
    )


def load_config(
    config_dir: Path = DEFAULT_CONFIG_DIR,
    state_path: Path = DEFAULT_STATE_PATH,
    env_path: Path | None = DEFAULT_ENV_PATH,
) -> Config:
    sites = parse_sites(Path(config_dir) / "sites.yml")
    filters = parse_filters(Path(config_dir) / "filters.yml")

    env_file = parse_dotenv(Path(env_path)) if env_path else {}
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or env_file.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or env_file.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set "
            "(via environment or .env file)"
        )

    return Config(
        sites=sites,
        filters=filters,
        telegram_token=token,
        telegram_chat_id=chat_id,
        state_path=Path(state_path),
    )
