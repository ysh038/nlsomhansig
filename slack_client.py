from __future__ import annotations

import os
from pathlib import Path

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def _get_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} 환경변수가 설정되지 않았습니다.")
    return value


def upload_lunch_menu(image_path: Path, caption: str, target_profile: str) -> None:
    token = _get_env("SLACK_BOT_TOKEN")
    channel_id = _get_env("SLACK_CHANNEL_ID")

    client = WebClient(token=token)
    message = f"오늘 점심 메뉴입니다!\n\n{caption}\n\n출처: @{target_profile}"

    try:
        client.files_upload_v2(
            channel=channel_id,
            file=str(image_path),
            title="오늘의 점심 메뉴",
            initial_comment=message,
        )
    except SlackApiError as exc:
        error = exc.response.get("error", "unknown_error")
        raise RuntimeError(f"Slack 업로드 실패: {error}") from exc
