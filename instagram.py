from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import instaloader

KST = ZoneInfo("Asia/Seoul")
DOWNLOAD_DIR = Path("downloads")


@dataclass
class TodayPost:
    image_path: Path
    shortcode: str
    caption: str


def _create_loader() -> instaloader.Instaloader:
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    return instaloader.Instaloader(
        download_pictures=True,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        dirname_pattern=str(DOWNLOAD_DIR / "{target}"),
    )


def _load_session(loader: instaloader.Instaloader) -> None:
    username = os.environ.get("INSTAGRAM_USERNAME", "").strip()
    if not username:
        raise ValueError("INSTAGRAM_USERNAME 환경변수가 설정되지 않았습니다.")

    session_path = Path("session")
    if not session_path.exists():
        raise FileNotFoundError(
            "session 파일이 없습니다. README의 안내에 따라 instaloader --login으로 생성하세요."
        )

    loader.load_session_from_file(username, filename=str(session_path))


def _post_date_kst(post: instaloader.Post) -> datetime.date:
    return post.date_local.date()


def _find_downloaded_image(target_profile: str, post: instaloader.Post) -> Path:
    profile_dir = DOWNLOAD_DIR / target_profile
    if not profile_dir.exists():
        raise FileNotFoundError(f"다운로드 디렉터리를 찾을 수 없습니다: {profile_dir}")

    matches = sorted(profile_dir.glob(f"*_{post.shortcode}*.jpg"))
    if not matches:
        matches = sorted(profile_dir.glob(f"*_{post.shortcode}*"))
    if not matches:
        raise FileNotFoundError(f"게시물 이미지를 찾을 수 없습니다: {post.shortcode}")

    return matches[0]


def fetch_today_post(target_profile: str | None = None) -> TodayPost | None:
    profile_name = (target_profile or os.environ.get("TARGET_PROFILE", "nlsomhansig")).strip()
    today = datetime.now(KST).date()

    loader = _create_loader()
    _load_session(loader)

    profile = instaloader.Profile.from_username(loader.context, profile_name)

    for post in profile.get_posts():
        post_date = _post_date_kst(post)

        if post_date < today:
            return None

        if post_date == today:
            loader.download_post(post, target=profile_name)
            image_path = _find_downloaded_image(profile_name, post)
            caption = post.caption or "오늘의 점심 메뉴"
            return TodayPost(
                image_path=image_path,
                shortcode=post.shortcode,
                caption=caption,
            )

    return None
