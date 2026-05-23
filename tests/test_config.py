from __future__ import annotations

from pathlib import Path

import pytest

from src.config import (
    load_config,
    parse_dotenv,
    parse_filters,
    parse_sites,
)


# ---------------- parse_dotenv ----------------

def test_parse_dotenv_missing_file_returns_empty(tmp_path: Path):
    assert parse_dotenv(tmp_path / "no.env") == {}


def test_parse_dotenv_skips_comments_and_blanks(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("# a comment\n\nA=1\n B = 2 \n", encoding="utf-8")
    assert parse_dotenv(p) == {"A": "1", "B": "2"}


def test_parse_dotenv_strips_quotes(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("A=\"hello\"\nB='world'\n", encoding="utf-8")
    assert parse_dotenv(p) == {"A": "hello", "B": "world"}


def test_parse_dotenv_handles_value_containing_equals(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("URL=a=b=c\n", encoding="utf-8")
    assert parse_dotenv(p) == {"URL": "a=b=c"}


# ---------------- parse_sites ----------------

def test_parse_sites_minimal(tmp_path: Path):
    p = tmp_path / "sites.yml"
    p.write_text(
        """
sites:
  - key: s1
    adapter: example_site.ExampleSite
    url: http://x
""",
        encoding="utf-8",
    )
    sites = parse_sites(p)
    assert len(sites) == 1
    s = sites[0]
    assert s.key == "s1"
    assert s.name == "s1"               # name defaults to key
    assert s.enabled is True             # enabled defaults to true
    assert s.selectors == {}


def test_parse_sites_empty_file(tmp_path: Path):
    p = tmp_path / "sites.yml"
    p.write_text("", encoding="utf-8")
    assert parse_sites(p) == []


# ---------------- parse_filters ----------------

def test_parse_filters_defaults_empty(tmp_path: Path):
    p = tmp_path / "filters.yml"
    p.write_text("", encoding="utf-8")
    f = parse_filters(p)
    assert f.include == []
    assert f.exclude == []


def test_parse_filters_populated(tmp_path: Path):
    p = tmp_path / "filters.yml"
    p.write_text(
        "include:\n  - 청약\nexclude:\n  - 발표\n  - 결과\n", encoding="utf-8"
    )
    f = parse_filters(p)
    assert f.include == ["청약"]
    assert f.exclude == ["발표", "결과"]


# ---------------- load_config ----------------

def _write_config_dir(root: Path) -> Path:
    cdir = root / "config"
    cdir.mkdir()
    (cdir / "sites.yml").write_text(
        "sites:\n  - key: k\n    adapter: example_site.ExampleSite\n    url: http://x\n",
        encoding="utf-8",
    )
    (cdir / "filters.yml").write_text("include: []\nexclude: []\n", encoding="utf-8")
    return cdir


def test_load_config_uses_env_vars(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cdir = _write_config_dir(tmp_path)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "cid")
    cfg = load_config(cdir, state_path=tmp_path / "state.json", env_path=None)
    assert cfg.telegram_token == "tok"
    assert cfg.telegram_chat_id == "cid"


def test_load_config_falls_back_to_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cdir = _write_config_dir(tmp_path)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    env = tmp_path / ".env"
    env.write_text("TELEGRAM_BOT_TOKEN=etok\nTELEGRAM_CHAT_ID=ecid\n", encoding="utf-8")
    cfg = load_config(cdir, state_path=tmp_path / "state.json", env_path=env)
    assert cfg.telegram_token == "etok"
    assert cfg.telegram_chat_id == "ecid"


def test_load_config_env_overrides_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cdir = _write_config_dir(tmp_path)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "from_env")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "from_env")
    env = tmp_path / ".env"
    env.write_text("TELEGRAM_BOT_TOKEN=from_dotenv\nTELEGRAM_CHAT_ID=from_dotenv\n", encoding="utf-8")
    cfg = load_config(cdir, state_path=tmp_path / "state.json", env_path=env)
    assert cfg.telegram_token == "from_env"
    assert cfg.telegram_chat_id == "from_env"


def test_load_config_missing_secrets_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cdir = _write_config_dir(tmp_path)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with pytest.raises(RuntimeError, match="TELEGRAM"):
        load_config(cdir, state_path=tmp_path / "state.json", env_path=None)
