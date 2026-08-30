from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import KEYFRAMES_PER_MINUTE, PROCESSED_DIR, XDV_TEST_VIDEOS_DIR
from src.ingest.xdv_annotations import XdvAnnotation, load_annotations
from src.preprocess.katna_extractor import extract_keyframes, save_keyframes
from src.preprocess.segment_cutter import cut_segment

# XD-V class code → output folder name
CLASS_CODE_TO_FOLDER: dict[str, str] = {
    "B1": "Fighting",
    "B2": "Shooting",
    "B4": "Riot",
    "B5": "Abuse",
    "B6": "Car Accident",
    "G":  "Explosion",
}

VIOLENCE_ROOT: Path = PROCESSED_DIR / "violence"
VIDEO_EXTENSIONS: tuple[str, ...] = (".mp4", ".MP4", ".mkv", ".avi", ".webm")
# Real XD-V filenames embed the label: ``{clip_id}_label_{codes}.mp4``.
# We locate a clip by glob since the label suffix is not known up front.
VIDEO_FILENAME_GLOB: str = "{clip_id}_label_*.mp4"


def calc_no_of_frames(seg_length_sec: float, per_minute: int = KEYFRAMES_PER_MINUTE) -> int:
    """Convert segment length in seconds to a Katna ``no_of_frames`` count."""
    return max(1, int(seg_length_sec * per_minute / 60))


def get_video_fps(video_path: Path) -> float:
    cap = cv2.VideoCapture(str(video_path))
    try:
        fps: float = float(cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0:
            raise RuntimeError(f"Could not read FPS from {video_path}")
        return fps
    finally:
        cap.release()


def find_video_file(clip_id: str, video_dir: Path) -> Path | None:
    """Locate the mp4 matching ``clip_id`` under the XD-V naming scheme.

    XD-V test files are named ``{clip_id}_label_{codes}.mp4`` — the label
    suffix is unknown until the file lands. We glob and take the first match
    (one-to-one in the published dataset).
    """
    matches = sorted(video_dir.glob(VIDEO_FILENAME_GLOB.format(clip_id=clip_id)))
    return matches[0] if matches else None


def process_annotation(
    ann: XdvAnnotation,
    video_dir: Path,
    out_root: Path,
) -> int:
    """Cut, extract, save for one annotation line. Returns saved keyframe count."""
    folder_name = CLASS_CODE_TO_FOLDER.get(ann.primary_class)
    if folder_name is None:
        print(f"[skip] unknown class {ann.primary_class} for {ann.clip_id}", file=sys.stderr)
        return 0

    video_path = find_video_file(ann.clip_id, video_dir)
    if video_path is None:
        print(f"[skip] no video file: {ann.clip_id}", file=sys.stderr)
        return 0

    fps = get_video_fps(video_path)
    out_dir = out_root / folder_name
    total_saved = 0

    with tempfile.TemporaryDirectory(prefix="violence_cut_") as tmp:
        tmp_path = Path(tmp)
        for seg_idx, seg in enumerate(ann.segments):
            start_sec: float = seg.start_frame / fps
            end_sec: float = seg.end_frame / fps
            length_sec: float = end_sec - start_sec
            if length_sec <= 0:
                continue

            seg_video = tmp_path / f"seg_{seg_idx:03d}.mp4"
            try:
                cut_segment(video_path, start_sec, end_sec, seg_video)
            except RuntimeError as e:
                print(f"[warn] cut failed: {ann.clip_id} seg{seg_idx}: {e}", file=sys.stderr)
                continue

            n_frames = calc_no_of_frames(length_sec)
            try:
                frames = extract_keyframes(seg_video, n_frames)
            except (RuntimeError, ValueError) as e:
                print(f"[warn] katna failed: {ann.clip_id} seg{seg_idx}: {e}", file=sys.stderr)
                continue

            prefix = f"{ann.clip_id}_seg{seg_idx:03d}"
            saved = save_keyframes(frames, out_dir, prefix)
            total_saved += len(saved)

    return total_saved


def main() -> None:
    annotations = load_annotations()
    print(f"Loaded {len(annotations)} annotation lines")

    for folder in CLASS_CODE_TO_FOLDER.values():
        (VIOLENCE_ROOT / folder).mkdir(parents=True, exist_ok=True)

    total = 0
    processed = 0
    for i, ann in enumerate(annotations, start=1):
        n_saved = process_annotation(ann, XDV_TEST_VIDEOS_DIR, VIOLENCE_ROOT)
        total += n_saved
        if n_saved > 0:
            processed += 1
        if i % 10 == 0:
            print(f"  [{i}/{len(annotations)}] saved={total}, processed_clips={processed}")

    print(f"\n=== Done: {total} keyframes from {processed} clips ===")
    print(f"Output root: {VIOLENCE_ROOT}")


if __name__ == "__main__":
    main()
