"""Extract frames at a fixed fps from XD-Violence test clips matching given labels.

Selection is *contains-any*: a clip is taken if its label set (filename
``label_X-X-X``, ``0`` = empty slot) intersects ``--labels``. Default B1,B5
(fighting / abuse) for the people-vs-people physical-violence track.

    python scripts/extract_xdv_frames.py --fps 2 --labels B1 B5

Output (one folder per clip, ordered frames -> good for temporal localization):
    data/processed/xdviolence_test/<clip_stem>/<clip_stem>_<NNNNN>.jpg

Idempotent: a clip whose output folder already holds frames is skipped.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import XDV_TEST_KEYFRAMES_DIR, XDV_TEST_VIDEOS_DIR

FFMPEG_BIN: str = imageio_ffmpeg.get_ffmpeg_exe()
_LABEL_RE = re.compile(r"label_([^.]+)")


def clip_labels(filename: str) -> frozenset[str]:
    match = _LABEL_RE.search(filename)
    if match is None:
        return frozenset()
    return frozenset(tok for tok in match.group(1).split("-") if tok != "0")


def select_clips(videos_dir: Path, targets: frozenset[str]) -> list[Path]:
    return sorted(
        path
        for path in videos_dir.glob("*.mp4")
        if clip_labels(path.name) & targets
    )


def extract_clip(video: Path, out_root: Path, fps: int) -> int:
    out_dir = out_root / video.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = list(out_dir.glob(f"{video.stem}_*.jpg"))
    if existing:
        print(f"[skip] {video.stem} — already has {len(existing)} frames")
        return len(existing)

    out_pattern = out_dir / f"{video.stem}_%05d.jpg"
    cmd = [
        FFMPEG_BIN, "-hide_banner", "-loglevel", "error",
        "-i", str(video), "-vf", f"fps={fps}", "-qscale:v", "2",
        "-y", str(out_pattern),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[FAIL] {video.stem} (code={result.returncode}): {result.stderr[-300:]}")
        return 0
    saved = list(out_dir.glob(f"{video.stem}_*.jpg"))
    print(f"[ok]   {video.stem} -> {len(saved)} frames")
    return len(saved)


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract fps frames from labelled XD-Violence test clips.")
    ap.add_argument("--fps", type=int, default=2, help="frames per second (default 2)")
    ap.add_argument("--labels", nargs="+", default=["B1", "B5"], help="target labels (contains-any)")
    args = ap.parse_args()

    targets = frozenset(args.labels)
    clips = select_clips(XDV_TEST_VIDEOS_DIR, targets)
    print(f"labels={sorted(targets)} -> {len(clips)} clips, fps={args.fps}\n")

    total_frames = 0
    failed: list[str] = []
    for i, video in enumerate(clips, 1):
        print(f"({i}/{len(clips)}) ", end="")
        n = extract_clip(video, XDV_TEST_KEYFRAMES_DIR, args.fps)
        total_frames += n
        if n == 0:
            failed.append(video.stem)

    print(f"\nDONE: {len(clips)} clips, {total_frames} frames at fps={args.fps}")
    if failed:
        print(f"FAILED ({len(failed)}): " + ", ".join(failed))


if __name__ == "__main__":
    main()
