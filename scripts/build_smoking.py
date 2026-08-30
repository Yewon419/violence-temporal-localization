"""Build the *smoking* category dataset end-to-end.

Run:
    python scripts/build_smoking.py

Performs in order:

1. **HOD (Harmful Object Detection)**: copies cigarette images from the
   YOLOv5 zip into ``smoking/cigarette/``.
   Requires: ``~/Downloads/yolo_v5_dataset.zip``.
   Output prefix: ``hod_``.

2. **Roboflow Smoking and Drinking Detection**: copies smoking-class
   images from the YOLOv8-OBB zip into ``smoking/cigarette/``.
   Requires: ``~/Downloads/Smoking and Drinking Detection.v2-test-yolov5m.yolov8-obb.zip``.
   Output prefix: ``rfsd_``.

3. **Mendeley Smoker Detection**: copies the Smoking class (560 images)
   from the rar archive into ``smoking/cigarette/``. NotSmoking class is
   intentionally skipped.
   Requires: ``~/Downloads/Smoker Detection.rar`` AND an unrar/bsdtar/7z
   backend on PATH (rarfile package handles the rest).
   Output prefix: ``mds_``.

See ``docs/datasets.md`` for download instructions, ``docs/decisions.md``
for class-mapping rationale.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR
from src.ingest.hod_extractor import extract_hod_smoking
from src.ingest.mendeley_smoker_extractor import extract_mendeley_smoker
from src.ingest.roboflow_smoking_drinking_extractor import extract_roboflow_smoking

SMOKING_ROOT: Path = PROCESSED_DIR / "smoking"
IMAGE_EXTS: tuple[str, ...] = (".jpg", ".jpeg", ".png")


def print_folder_counts() -> None:
    print("\n=== final smoking/ folder counts ===")
    total = 0
    if not SMOKING_ROOT.exists():
        print(f"  <{SMOKING_ROOT} does not exist>")
        return
    for folder in sorted(p for p in SMOKING_ROOT.iterdir() if p.is_dir()):
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
    banner("Step 1/3: HOD — cigarette images")
    hod_stats = extract_hod_smoking()
    for key, value in hod_stats.items():
        print(f"  {key:22s}: {value}")

    banner("Step 2/3: Roboflow S&D — smoking-class images")
    rfsd_stats = extract_roboflow_smoking()
    for key, value in rfsd_stats.items():
        print(f"  {key:22s}: {value}")

    banner("Step 3/3: Mendeley Smoker — Smoking class")
    mds_stats = extract_mendeley_smoker()
    for key, value in mds_stats.items():
        print(f"  {key:22s}: {value}")

    print_folder_counts()


if __name__ == "__main__":
    main()
