"""야간 배치 — 유튜브 영화 요약·컴파일 영상 10편 다운로드 + ffmpeg fps=1 프레임 추출.

회의 전 false positive 완화 트랙용 raw frame pool 수집.
2026-05-30 사장 결정: Katna 다양성 추출 → ffmpeg 시간 균등(1초당 1f)으로 교체.
음주·흡연 cut을 시간 비례로 더 잘 잡기 위함.

실행:
    .venv\\Scripts\\python.exe scripts\\crawl_yt_drama.py

특징:
- idempotent: 이미 다운로드된 영상·이미 추출된 frame은 skip
- 영상 1개 실패해도 try/except로 격리, 다음 영상 진행
- 로그: stdout + data/logs/crawl_yt_drama_{TIMESTAMP}.log

출력:
    data/raw/yt_drama/{video_id}.mp4
    data/processed/yt_drama_frames/{video_id}_frame_{NNNNN}.jpg
"""

from __future__ import annotations

import logging
import subprocess
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import imageio_ffmpeg
import yt_dlp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import DATA_DIR, PROCESSED_DIR, RAW_DIR

FPS_PER_SECOND: int = 1


@dataclass(frozen=True)
class VideoTarget:
    video_id: str
    label: str


VIDEOS: tuple[VideoTarget, ...] = (
    VideoTarget("vyXEi00PVrw", "신세계"),
    VideoTarget("69RJZ7TwDrQ", "범죄와의 전쟁"),
    VideoTarget("3auH8hGUezI", "내부자들"),
    VideoTarget("Rqlf3zNPqgQ", "달콤한 인생"),
    VideoTarget("LkSY-EuTb1E", "마약왕"),
    VideoTarget("Tj7Doyo8XdQ", "친구"),
    VideoTarget("wBr3f72w-fg", "비열한 거리"),
    VideoTarget("sMpzdgHrINs", "베테랑"),
    VideoTarget("x2PjLCMrfTk", "황해"),
    VideoTarget("jGP1Z18maME", "흡연 장면 모음"),
)

VIDEO_DIR: Path = RAW_DIR / "yt_drama"
FRAMES_DIR: Path = PROCESSED_DIR / "yt_drama_frames"
LOG_DIR: Path = DATA_DIR / "logs"

FFMPEG_BIN: str = imageio_ffmpeg.get_ffmpeg_exe()


def setup_logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"crawl_yt_drama_{timestamp}.log"

    logger = logging.getLogger("crawl_yt_drama")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    logger.info(f"log file: {log_path}")
    return logger


def _existing_video_path(video_id: str) -> Path | None:
    candidates = sorted(VIDEO_DIR.glob(f"{video_id}.*"))
    for path in candidates:
        if path.suffix.lower() in {".mp4", ".mkv", ".webm"} and path.stat().st_size > 0:
            return path
    return None


def download_video(target: VideoTarget, logger: logging.Logger) -> Path | None:
    existing = _existing_video_path(target.video_id)
    if existing is not None:
        size_mb = existing.stat().st_size / 1_000_000
        logger.info(
            f"[{target.video_id}] already downloaded "
            f"({existing.name}, {size_mb:.1f} MB) — skip"
        )
        return existing

    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    outtmpl = str(VIDEO_DIR / f"{target.video_id}.%(ext)s")

    opts: dict[str, object] = {
        "format": (
            "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]"
            "/best[ext=mp4][height<=720]"
            "/best[height<=720]"
        ),
        "merge_output_format": "mp4",
        "outtmpl": outtmpl,
        "ffmpeg_location": FFMPEG_BIN,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "retries": 3,
        "fragment_retries": 3,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={target.video_id}"])
    except Exception as e:
        logger.error(f"[{target.video_id}] download failed: {type(e).__name__}: {e}")
        return None

    result = _existing_video_path(target.video_id)
    if result is None:
        logger.error(f"[{target.video_id}] download finished but no output file found")
        return None

    size_mb = result.stat().st_size / 1_000_000
    logger.info(f"[{target.video_id}] downloaded ({size_mb:.1f} MB) → {result.name}")
    return result


def extract_frames_for(
    target: VideoTarget, video_path: Path, logger: logging.Logger
) -> int:
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(FRAMES_DIR.glob(f"{target.video_id}_frame_*.jpg"))
    if existing:
        logger.info(
            f"[{target.video_id}] frames already extracted "
            f"({len(existing)} files) — skip"
        )
        return len(existing)

    out_pattern = FRAMES_DIR / f"{target.video_id}_frame_%05d.jpg"
    cmd = [
        FFMPEG_BIN,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video_path),
        "-vf",
        f"fps={FPS_PER_SECOND}",
        "-qscale:v",
        "2",
        "-y",
        str(out_pattern),
    ]
    logger.info(f"[{target.video_id}] ffmpeg fps={FPS_PER_SECOND} extracting...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(
            f"[{target.video_id}] ffmpeg failed (code={result.returncode}): "
            f"{result.stderr[-500:]}"
        )
        return 0

    saved = list(FRAMES_DIR.glob(f"{target.video_id}_frame_*.jpg"))
    logger.info(f"[{target.video_id}] saved {len(saved)} frames")
    return len(saved)


def main() -> None:
    logger = setup_logger()
    logger.info(f"targets: {len(VIDEOS)} videos")
    logger.info(f"video dir: {VIDEO_DIR}")
    logger.info(f"frames dir: {FRAMES_DIR}")
    logger.info(f"FPS_PER_SECOND: {FPS_PER_SECOND}")
    logger.info(f"ffmpeg: {FFMPEG_BIN}")
    logger.info("=" * 60)

    summary: list[tuple[str, str, int]] = []
    for i, target in enumerate(VIDEOS, 1):
        logger.info(f"--- [{i}/{len(VIDEOS)}] {target.video_id} | {target.label} ---")
        try:
            video_path = download_video(target, logger)
            if video_path is None:
                summary.append((target.video_id, target.label, 0))
                continue
            n = extract_frames_for(target, video_path, logger)
            summary.append((target.video_id, target.label, n))
        except Exception:
            logger.error(
                f"[{target.video_id}] uncaught error:\n{traceback.format_exc()}"
            )
            summary.append((target.video_id, target.label, 0))

    logger.info("=" * 60)
    logger.info("SUMMARY")
    total = 0
    for vid, label, n in summary:
        logger.info(f"  {vid} [{label}]: {n} keyframes")
        total += n
    logger.info(f"TOTAL: {total} keyframes across {len(VIDEOS)} videos")


if __name__ == "__main__":
    main()
