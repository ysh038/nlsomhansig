from __future__ import annotations

import os
from pathlib import Path

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from instagram import TodayPost


def _get_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} 환경변수가 설정되지 않았습니다.")
    return value


def upload_lunch_menu(posts: list[TodayPost], target_profile: str) -> None:
    if not posts:
        return

    token = _get_env("SLACK_BOT_TOKEN")
    channel_id = _get_env("SLACK_CHANNEL_ID")
    client = WebClient(token=token)

    image_paths: list[Path] = []
    for post in posts:
        image_paths.extend(post.image_paths)

    captions = [post.caption for post in posts if post.caption]
    caption_text = captions[0] if captions else "오늘의 점심 메뉴"
    image_count = len(image_paths)
    message = (
        f"오늘 점심 메뉴입니다! ({image_count}장)\n\n"
        f"{caption_text}\n\n"
        f"출처: @{target_profile}"
    )

    file_uploads = [
        {
            "file": str(path),
            "title": f"점심메뉴 {index + 1}",
        }
        for index, path in enumerate(image_paths)
    ]

    try:
        client.files_upload_v2(
            channel=channel_id,
            file_uploads=file_uploads,
            initial_comment=message,
        )
    except SlackApiError as exc:
        error = exc.response.get("error", "unknown_error")
        raise RuntimeError(f"Slack 업로드 실패: {error}") from exc
