"""Build the *violence* category dataset end-to-end.

Run:
    python scripts/build_violence.py

Performs in order:

1. **XD-V zip extraction** (idempotent): unpacks ``videos.zip`` into
   ``data/raw/xdviolence_test/``, flattening the inner ``videos/`` prefix.
   Files already on disk with matching size are skipped.
   Requires: ``~/Downloads/videos.zip`` (10GB, downloaded from the
   official Test Videos SharePoint link).

2. **XD-Violence keyframe extraction**: ffmpeg-cuts each annotated
   violence segment then runs Katna on the cut. Requires:
     - ``data/raw/xdviolence_test/*.mp4`` (auto-populated by Step 1)
     - ``data/annotated/xdv_test_annotations.txt``
   Output: ``data/processed/violence/{Fighting|Shooting|Riot|Abuse|
   Car Accident|Explosion}/{clip_id}_seg{si:03d}_kf{ki:04d}.jpg``.

3. **HOD (Harmful Object Detection)**: copies gun / knife / blood
   images directly from the YOLOv5 zip into the violence folders.
   Requires: ``~/Downloads/yolo_v5_dataset.zip``.
   Output prefix: ``hod_`` under ``총기 / 흉기 / 상해(피)``.

4. **Roboflow Harmful Objects**: copies weapon images (axe, hammer,
   dumbbell → 둔기; knife, scissors, fork, chisel, screwdriver,
   chainsaw → 흉기) from the YOLOv8 zip.
   Requires: ``~/Downloads/harmful objects.v1i.yolov8.zip``.
   Output prefix: ``rfh_`` under ``둔기 / 흉기``.

See ``docs/datasets.md`` for download instructions, ``docs/decisions.md``
for class-mapping rationale.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR
from src.ingest.hod_extractor import extract_hod_violence
from src.ingest.roboflow_harmful_extractor import extract_roboflow_harmful
from src.ingest.xdv_extract_videos import extract_xdv_test_videos
from src.preprocess.build_violence_dataset import main as build_xdv_keyframes

VIOLENCE_ROOT: Path = PROCESSED_DIR / "violence"
IMAGE_EXTS: tuple[str, ...] = (".jpg", ".jpeg", ".png")


def print_folder_counts() -> None:
    print("\n=== final violence/ folder counts ===")
    total = 0
    if not VIOLENCE_ROOT.exists():
        print(f"  <{VIOLENCE_ROOT} does not exist>")
        return
    for folder in sorted(p for p in VIOLENCE_ROOT.iterdir() if p.is_dir()):
        n = sum(1 for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTS)
        print(f"  {folder.name:20s}: {n}")
        total += n
    print(f"  {'TOTAL':20s}: {total}")


def banner(text: str) -> None:
    print()
    print("=" * 60)
    print(text)
    print("=" * 60)


def main() -> None:
    banner("Step 1/4: XD-Violence — unpack videos.zip into data/raw/ (idempotent)")
    xdv_zip_stats = extract_xdv_test_videos()
    for key, value in xdv_zip_stats.items():
        print(f"  {key:20s}: {value}")

    banner("Step 2/4: XD-Violence — Katna keyframes from violence segments")
    build_xdv_keyframes()

    banner("Step 3/4: HOD — gun / knife / blood images")
    hod_stats = extract_hod_violence()
    for key, value in hod_stats.items():
        print(f"  {key:20s}: {value}")

    banner("Step 4/4: Roboflow Harmful Objects — weapon images")
    rfh_stats = extract_roboflow_harmful()
    for key, value in rfh_stats.items():
        print(f"  {key:20s}: {value}")

    print_folder_counts()


if __name__ == "__main__":
    main()
