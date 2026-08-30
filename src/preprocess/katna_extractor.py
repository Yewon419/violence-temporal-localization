from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

import cv2
import numpy as np
from Katna.video import Video
from numpy.typing import NDArray

# BGR uint8 image, OpenCV convention
Frame = NDArray[np.uint8]


class CaptureWriter:
    """Katna-compatible writer that captures frames in memory.

    Katna's ``extract_video_keyframes`` calls ``writer.write(file_path, top_frames)``
    where ``top_frames`` is a list of BGR numpy arrays. This writer stores them
    rather than persisting to disk, so the caller can name and place files
    according to its own scheme.
    """

    def __init__(self) -> None:
        self.frames: list[Frame] = []
        self.file_path: str = ""

    def write(self, file_path: str, top_frames: list[Frame]) -> None:
        self.file_path = file_path
        self.frames = list(top_frames)


def _cv2_uniform_sample(video_path: Path, no_of_frames: int) -> list[Frame]:
    """Pick N evenly-spaced frames via cv2 — fallback when Katna returns 0.

    Useful for very short segments where Katna's LUV cluster cannot resolve
    the requested ``no_of_frames`` and silently returns an empty list.
    Frames are picked at the midpoint of each evenly divided sub-interval
    to avoid leading/trailing edge frames.
    """
    cap = cv2.VideoCapture(str(video_path))
    try:
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total <= 0:
            return []
        n = min(no_of_frames, total)
        if n < 1:
            return []
        indices = [int((i + 0.5) * total / n) for i in range(n)]
        frames: list[Frame] = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if ok and frame is not None:
                frames.append(cast(Frame, frame))
        return frames
    finally:
        cap.release()


def extract_keyframes(video_path: Path, no_of_frames: int) -> list[Frame]:
    """Extract up to ``no_of_frames`` keyframes via Katna, with cv2 fallback.

    Katna's LUV cluster occasionally returns 0 frames on very short clips
    (observed on Abuse / short Fighting segments). When that happens we
    fall back to cv2 uniform sampling so short segments still contribute
    to the dataset.
    """
    if no_of_frames < 1:
        raise ValueError(f"no_of_frames must be >= 1, got {no_of_frames}")
    vd = Video()
    writer = CaptureWriter()
    try:
        vd.extract_video_keyframes(
            no_of_frames=no_of_frames,
            file_path=str(video_path),
            writer=writer,
        )
    except Exception as e:
        # Katna can raise a variety of internal errors on tiny clips;
        # we don't propagate — fall back to cv2 uniform sampling below.
        print(
            f"[katna] {video_path.name}: {type(e).__name__}: {e} — falling back to cv2",
            file=sys.stderr,
        )
        writer.frames = []
    if writer.frames:
        return writer.frames
    return _cv2_uniform_sample(video_path, no_of_frames)


def save_keyframes(
    frames: list[Frame],
    out_dir: Path,
    filename_prefix: str,
) -> list[Path]:
    """Save frames as JPG into ``out_dir`` with filename ``{prefix}_kf{idx:04d}.jpg``.

    Uses ``cv2.imencode`` + ``Path.write_bytes`` instead of ``cv2.imwrite``
    because OpenCV's writer mangles unicode paths on Windows (a long-standing
    issue with non-ASCII chars in the path).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for idx, frame in enumerate(frames):
        path = out_dir / f"{filename_prefix}_kf{idx:04d}.jpg"
        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            raise RuntimeError(f"cv2.imencode failed for {path}")
        path.write_bytes(encoded.tobytes())
        saved.append(path)
    return saved
