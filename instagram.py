from __future__ import annotations

import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import instaloader
from instaloader.exceptions import InstaloaderException

import instaloader_patch

instaloader_patch.apply()

KST = ZoneInfo("Asia/Seoul")
DOWNLOAD_DIR = Path("downloads")
MAX_POSTS_TO_CHECK = 20
MAX_POSTS_PER_DAY = 10
FETCH_TIMEOUT_SEC = 60


@dataclass
class TodayPost:
    image_paths: list[Path]
    shortcode: str
    caption: str


def _create_loader() -> instaloader.Instaloader:
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    return instaloader.Instaloader(
        download_pictures=False,
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


def _download_post_images(post: instaloader.Post, target_profile: str) -> list[Path]:
    profile_dir = DOWNLOAD_DIR / target_profile
    profile_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    if post.typename == "GraphSidecar":
        image_index = 0
        for node in post.get_sidecar_nodes():
            if node.is_video:
                continue
            dest = profile_dir / f"{post.shortcode}_{image_index}.jpg"
            urllib.request.urlretrieve(node.display_url, dest)
            paths.append(dest)
            image_index += 1
        return paths

    dest = profile_dir / f"{post.shortcode}.jpg"
    urllib.request.urlretrieve(post.url, dest)
    return [dest]


def _fetch_today_posts_inner(target_profile: str) -> list[TodayPost]:
    today = datetime.now(KST).date()
    today_posts: list[TodayPost] = []

    loader = _create_loader()
    _load_session(loader)

    print(f"@{target_profile} 오늘({today}) 게시물 확인 중...")
    profile = instaloader.Profile.from_username(loader.context, target_profile)

    for index, post in enumerate(profile.get_posts()):
        if index >= MAX_POSTS_TO_CHECK:
            break

        post_date = _post_date_kst(post)
        print(f"  - {post.shortcode} ({post_date})")

        if post_date < today:
            break

        if post_date == today:
            image_paths = _download_post_images(post, target_profile)
            if not image_paths:
                print(f"  ! {post.shortcode}: 이미지 없음 (동영상 전용 게시물일 수 있음), 건너뜀")
                continue
            caption = post.caption or "오늘의 점심 메뉴"
            today_posts.append(
                TodayPost(
                    image_paths=image_paths,
                    shortcode=post.shortcode,
                    caption=caption,
                )
            )

            if len(today_posts) >= MAX_POSTS_PER_DAY:
                print(f"오늘 게시물 {MAX_POSTS_PER_DAY}개 도달, 조회 중단.")
                break

    today_posts.reverse()
    if today_posts:
        total_images = sum(len(post.image_paths) for post in today_posts)
        print(
            f"오늘 게시물 {len(today_posts)}건, 이미지 {total_images}장 발견 "
            f"({', '.join(post.shortcode for post in today_posts)})"
        )

    return today_posts


def fetch_today_posts(target_profile: str | None = None) -> list[TodayPost]:
    profile_name = (target_profile or os.environ.get("TARGET_PROFILE", "nlsomhansig")).strip()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_fetch_today_posts_inner, profile_name)
        try:
            return future.result(timeout=FETCH_TIMEOUT_SEC)
        except FuturesTimeout as exc:
            raise RuntimeError(
                f"Instagram 조회 시간 초과 ({FETCH_TIMEOUT_SEC}초). "
                "잠시 후 다시 시도하세요."
            ) from exc
        except InstaloaderException as exc:
            raise RuntimeError(f"Instagram 조회 실패: {exc}") from exc
