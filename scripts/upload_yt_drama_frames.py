"""yt_drama 키프레임을 smoking + drinking 양쪽 sub-path에 동시 push.

사장 결정: decisions.md §4 multi-class 정책 정합 — 한 영상의 raw frame이
음주·흡연 둘 다 등장 가능하므로 두 카테고리 폴더에 같은 파일 복사.

실행:
    .venv\\Scripts\\python.exe scripts\\upload_yt_drama_frames.py <video_id> [video_id ...]
    .venv\\Scripts\\python.exe scripts\\upload_yt_drama_frames.py --all  # 폴더 전체

각 영상당 1 commit (smoking + drinking add 묶음).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huggingface_hub import CommitOperationAdd, HfApi

from src.config import PROCESSED_DIR

FRAMES_DIR: Path = PROCESSED_DIR / "yt_drama_frames"
REPO_ID: str = "DEteam4/movie-rating-violence"
TOKEN_PATH: Path = Path(r"C:\Users\windg\Desktop\PROJECT\_keys\DEproject2\HF_TOKEN.txt")
TARGET_PATHS: tuple[str, ...] = ("smoking/drama_frames", "drinking/drama_frames")


def get_token() -> str:
    env = os.environ.get("HF_TOKEN")
    if env:
        return env
    return TOKEN_PATH.read_text(encoding="utf-8").strip()


def push_video(api: HfApi, video_id: str) -> int:
    files = sorted(FRAMES_DIR.glob(f"{video_id}_frame_*.jpg"))
    if not files:
        print(f"  [{video_id}] no frames found", file=sys.stderr)
        return 0
    ops: list[CommitOperationAdd] = []
    for fp in files:
        for target in TARGET_PATHS:
            ops.append(
                CommitOperationAdd(
                    path_in_repo=f"{target}/{video_id}/{fp.name}",
                    path_or_fileobj=str(fp),
                )
            )
    api.create_commit(
        repo_id=REPO_ID,
        repo_type="dataset",
        operations=ops,
        commit_message=(
            f"Add yt_drama keyframes: {video_id} "
            f"({len(files)} frames x smoking+drinking)"
        ),
    )
    print(f"  [{video_id}] pushed {len(files)} frames x 2 paths")
    return len(files)


def discover_all() -> list[str]:
    ids: set[str] = set()
    for fp in FRAMES_DIR.glob("*_frame_*.jpg"):
        stem = fp.stem
        idx = stem.rfind("_frame_")
        if idx > 0:
            ids.add(stem[:idx])
    return sorted(ids)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("video_ids", nargs="*", help="video IDs to push")
    p.add_argument(
        "--all", action="store_true", help="push every video_id present in frame dir"
    )
    args = p.parse_args()

    video_ids = discover_all() if args.all else list(args.video_ids)
    if not video_ids:
        print("no video_ids given (use --all or list IDs)", file=sys.stderr)
        sys.exit(1)

    api = HfApi(token=get_token())
    total = 0
    for vid in video_ids:
        total += push_video(api, vid)
    print(f"TOTAL pushed: {total} frames across {len(video_ids)} videos")


if __name__ == "__main__":
    main()
