from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

STATE_FILE = Path("state.json")


@dataclass
class State:
    last_posted_shortcode: str | None = None
    last_posted_date: str | None = None

    def already_posted(self, shortcode: str) -> bool:
        return self.last_posted_shortcode == shortcode


def load_state() -> State:
    if not STATE_FILE.exists():
        return State()

    data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return State(
        last_posted_shortcode=data.get("last_posted_shortcode"),
        last_posted_date=data.get("last_posted_date"),
    )


def save_state(shortcode: str, posted_date: str) -> None:
    payload = {
        "last_posted_shortcode": shortcode,
        "last_posted_date": posted_date,
    }
    STATE_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
