"""Entry point: load config -> crawl each site -> filter -> diff against
state -> send Telegram summary -> persist updated state.
"""
from __future__ import annotations

import logging
import sys

from src.config import load_config
from src.crawler import fetch_all
from src.filter import apply_filter
from src.messenger import send_summary
from src.state import load_state, save_state

logger = logging.getLogger("webcrawling")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def run() -> int:
    setup_logging()
    cfg = load_config()
    state = load_state(cfg.state_path)
    site_names = {s.key: s.name for s in cfg.sites}

    new_posts = []
    for result in fetch_all(cfg.sites):
        if result.error is not None:
            continue
        filtered = apply_filter(result.posts, cfg.filters.include, cfg.filters.exclude)
        logger.info("after filter: %d posts (%s)", len(filtered), result.site_key)
        unseen = [p for p in filtered if not state.is_seen(result.site_key, p.id)]
        logger.info("new posts: %d (%s)", len(unseen), result.site_key)
        new_posts.extend(unseen)
        state.mark_seen(result.site_key, [p.id for p in unseen])

    if new_posts:
        try:
            count = send_summary(
                new_posts,
                cfg.telegram_token,
                cfg.telegram_chat_id,
                site_names=site_names,
            )
            logger.info("sent %d Telegram message(s)", count)
        except Exception:
            logger.exception("Telegram send failed; state not saved to avoid losing notifications")
            return 1
    else:
        logger.info("no new posts; no notification sent")

    save_state(state, cfg.state_path)
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
