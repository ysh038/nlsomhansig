from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

STATE_FILE = Path("state.json")


@dataclass
class State:
    last_posted_date: str | None = None
    posted_shortcodes: list[str] = field(default_factory=list)

    def reset_if_new_day(self, today: str) -> None:
        if self.last_posted_date != today:
            self.last_posted_date = today
            self.posted_shortcodes = []

    def filter_unposted(self, shortcodes: list[str]) -> list[str]:
        posted = set(self.posted_shortcodes)
        return [code for code in shortcodes if code not in posted]

    def mark_posted(self, shortcodes: list[str], posted_date: str) -> None:
        self.reset_if_new_day(posted_date)
        for code in shortcodes:
            if code not in self.posted_shortcodes:
                self.posted_shortcodes.append(code)
        self.last_posted_date = posted_date


def load_state() -> State:
    if not STATE_FILE.exists():
        return State()

    data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    posted = data.get("posted_shortcodes")
    if posted is None and data.get("last_posted_shortcode"):
        posted = [data["last_posted_shortcode"]]

    return State(
        last_posted_date=data.get("last_posted_date"),
        posted_shortcodes=posted or [],
    )


def save_state(state: State) -> None:
    payload = {
        "last_posted_date": state.last_posted_date,
        "posted_shortcodes": state.posted_shortcodes,
    }
    STATE_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
