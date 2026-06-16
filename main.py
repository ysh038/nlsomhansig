from __future__ import annotations

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from instagram import fetch_today_post
from slack_client import upload_lunch_menu
from state import load_state, save_state

KST = ZoneInfo("Asia/Seoul")


def main() -> int:
    load_dotenv()

    target_profile = os.environ.get("TARGET_PROFILE", "nlsomhansig").strip()
    today_str = datetime.now(KST).date().isoformat()

    state = load_state()
    post = fetch_today_post(target_profile)

    if post is None:
        print(f"[{today_str}] 오늘 올라온 게시물이 없습니다.")
        return 0

    if state.already_posted(post.shortcode):
        print(f"[{today_str}] 이미 전송한 게시물입니다: {post.shortcode}")
        return 0

    upload_lunch_menu(post.image_path, post.caption, target_profile)
    save_state(post.shortcode, today_str)
    print(f"[{today_str}] Slack 전송 완료: {post.shortcode}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
