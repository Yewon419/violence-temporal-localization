from __future__ import annotations

import subprocess
from pathlib import Path

import imageio_ffmpeg

FFMPEG_BIN: str = imageio_ffmpeg.get_ffmpeg_exe()


def cut_segment(
    src_video: Path,
    start_sec: float,
    end_sec: float,
    dst_video: Path,
) -> None:
    """Cut ``[start_sec, end_sec]`` out of ``src_video`` and write to ``dst_video``.

    Re-encoded (libx264) for frame-accurate boundaries. Audio is dropped —
    Katna only needs the video stream.
    """
    if start_sec < 0 or end_sec <= start_sec:
        raise ValueError(f"Invalid segment range: start={start_sec}, end={end_sec}")
    dst_video.parent.mkdir(parents=True, exist_ok=True)
    cmd: list[str] = [
        FFMPEG_BIN,
        "-y",
        "-i", str(src_video),
        "-ss", f"{start_sec:.3f}",
        "-to", f"{end_sec:.3f}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-an",
        "-loglevel", "error",
        str(dst_video),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (code={result.returncode}) for {src_video.name} "
            f"[{start_sec:.3f}-{end_sec:.3f}]: {result.stderr.strip()}"
        )
