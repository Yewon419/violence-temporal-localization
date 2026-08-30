"""Build the *drinking* category dataset end-to-end.

Run:
    python scripts/build_drinking.py

Performs in order:

1. **HOD (Harmful Object Detection)**: copies alcohol images from the
   YOLOv5 zip into ``drinking/alcohol/``.
   Requires: ``~/Downloads/yolo_v5_dataset.zip``.
   Output prefix: ``hod_``.

2. **Roboflow Smoking and Drinking Detection**: copies drinking-class
   images from the YOLOv8-OBB zip into ``drinking/alcohol/``.
   Requires: ``~/Downloads/Smoking and Drinking Detection.v2-test-yolov5m.yolov8-obb.zip``.
   Output prefix: ``rfsd_``.

See ``docs/datasets.md`` for download instructions, ``docs/decisions.md``
for class-mapping rationale.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import PROCESSED_DIR
from src.ingest.hod_extractor import extract_hod_drinking
from src.ingest.roboflow_smoking_drinking_extractor import extract_roboflow_drinking

DRINKING_ROOT: Path = PROCESSED_DIR / "drinking"
IMAGE_EXTS: tuple[str, ...] = (".jpg", ".jpeg", ".png")


def print_folder_counts() -> None:
    print("\n=== final drinking/ folder counts ===")
    total = 0
    if not DRINKING_ROOT.exists():
        print(f"  <{DRINKING_ROOT} does not exist>")
        return
    for folder in sorted(p for p in DRINKING_ROOT.iterdir() if p.is_dir()):
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
    banner("Step 1/2: HOD — alcohol images")
    hod_stats = extract_hod_drinking()
    for key, value in hod_stats.items():
        print(f"  {key:22s}: {value}")

    banner("Step 2/2: Roboflow S&D — drinking-class images")
    rfsd_stats = extract_roboflow_drinking()
    for key, value in rfsd_stats.items():
        print(f"  {key:22s}: {value}")

    print_folder_counts()


if __name__ == "__main__":
    main()
