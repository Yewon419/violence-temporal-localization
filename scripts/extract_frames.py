"""Extract frames from one video (YouTube id/URL or local file) at a fixed fps.

Generalizes crawl_yt_drama.py to a single arbitrary source so new dataset videos
(e.g. a zombie movie for the violence track) can be pulled on demand. Idempotent:
re-running with an already-downloaded video / already-extracted frames skips.

    python scripts/extract_frames.py --source <youtube_id|url|local.mp4> --name zombie01 [--fps 1]

Output:
    data/raw/extra/<name>.mp4                         (only when source is YouTube)
    data/processed/<name>_frames/<name>_frame_<NNNNN>.jpg
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import yt_dlp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR, RAW_DIR

RAW_EXTRA_DIR: Path = RAW_DIR / "extra"
FFMPEG_BIN: str = imageio_ffmpeg.get_ffmpeg_exe()
VIDEO_SUFFIXES = {".mp4", ".mkv", ".webm", ".avi", ".mov"}


def _existing_video(name: str) -> Path | None:
    for path in sorted(RAW_EXTRA_DIR.glob(f"{name}.*")):
        if path.suffix.lower() in VIDEO_SUFFIXES and path.stat().st_size > 0:
            return path
    return None


def resolve_source(source: str, name: str) -> Path | None:
    """Return a local video path: pass-through for a file, else yt-dlp download."""
    local = Path(source)
    if local.exists() and local.suffix.lower() in VIDEO_SUFFIXES:
        print(f"[{name}] local source: {local}")
        return local

    existing = _existing_video(name)
    if existing is not None:
        print(f"[{name}] already downloaded: {existing.name} — skip download")
        return existing

    url = source if source.startswith("http") else f"https://www.youtube.com/watch?v={source}"
    RAW_EXTRA_DIR.mkdir(parents=True, exist_ok=True)
    opts: dict[str, object] = {
        "format": (
            "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]"
            "/best[ext=mp4][height<=720]/best[height<=720]"
        ),
        "merge_output_format": "mp4",
        "outtmpl": str(RAW_EXTRA_DIR / f"{name}.%(ext)s"),
        "ffmpeg_location": FFMPEG_BIN,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "retries": 3,
        "fragment_retries": 3,
    }
    print(f"[{name}] downloading {url} ...")
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception as e:  # report and bail, never crash the batch
        print(f"[{name}] download failed: {type(e).__name__}: {e}")
        return None
    result = _existing_video(name)
    if result is None:
        print(f"[{name}] download finished but no output file found")
        return None
    print(f"[{name}] downloaded ({result.stat().st_size / 1_000_000:.1f} MB) -> {result.name}")
    return result


def extract_frames(name: str, video: Path, fps: int) -> int:
    out_dir = PROCESSED_DIR / f"{name}_frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = list(out_dir.glob(f"{name}_frame_*.jpg"))
    if existing:
        print(f"[{name}] frames already extracted ({len(existing)}) — skip")
        return len(existing)

    out_pattern = out_dir / f"{name}_frame_%05d.jpg"
    cmd = [
        FFMPEG_BIN, "-hide_banner", "-loglevel", "error",
        "-i", str(video), "-vf", f"fps={fps}", "-qscale:v", "2",
        "-y", str(out_pattern),
    ]
    print(f"[{name}] ffmpeg fps={fps} extracting -> {out_dir}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[{name}] ffmpeg failed (code={result.returncode}): {result.stderr[-500:]}")
        return 0
    saved = list(out_dir.glob(f"{name}_frame_*.jpg"))
    print(f"[{name}] saved {len(saved)} frames")
    return len(saved)


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract frames from one video at fixed fps.")
    ap.add_argument("--source", required=True, help="YouTube id/URL or local video path")
    ap.add_argument("--name", required=True, help="short id used in output filenames")
    ap.add_argument("--fps", type=int, default=1, help="frames per second (default 1)")
    args = ap.parse_args()

    video = resolve_source(args.source, args.name)
    if video is None:
        raise SystemExit(1)
    n = extract_frames(args.name, video, args.fps)
    print(f"DONE [{args.name}]: {n} frames at fps={args.fps}")


if __name__ == "__main__":
    main()
