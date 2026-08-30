"""Build a local Ultralytics YOLO detection set from the zombie01 curation.

Frame-level curation (A 실용, see zombie01_gore_ledger.md) selected ~455 keep frames
out of 1733 GD candidates. This script materializes that decision into a portable
YOLO dataset — entirely local, nothing pushed:

    positive       keep frame      -> GD filtered boxes converted to YOLO label
    hard negative  candidate, not keep (GD fired but FP: red dress/food/face) -> empty .txt
    easy negative  non-candidate (GD found nothing), only with --include-easy-neg -> empty .txt

    python scripts/zombie_to_yolo.py \
        --keep data/processed/vision_review/zombie01_keep_frames.json \
        --filtered-dir data/processed/gd_zombie_filtered/zombie01 \
        --frames-dir data/processed/zombie01_frames \
        --out-dir data/processed/zombie01_yolo

Class ids (local, 0-indexed): 0 weapon_gun, 1 weapon_knife, 2 weapon_blunt, 3 blood.
Remap to the project CVAT schema (11/10/12/13) on merge — see manifest remap_to_cvat.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import cast

from PIL import Image

CLASS_ORDER = ["weapon_gun", "weapon_knife", "weapon_blunt", "blood"]
CLASS_ID = {name: i for i, name in enumerate(CLASS_ORDER)}


def frame_stem(n: int) -> str:
    return f"zombie01_frame_{n:05d}"


def to_yolo_line(label: str, box: list[float], w: int, h: int) -> str:
    x1, y1, x2, y2 = box
    cx = ((x1 + x2) / 2) / w
    cy = ((y1 + y2) / 2) / h
    bw = (x2 - x1) / w
    bh = (y2 - y1) / h
    cx, cy = min(max(cx, 0.0), 1.0), min(max(cy, 0.0), 1.0)
    bw, bh = min(max(bw, 0.0), 1.0), min(max(bh, 0.0), 1.0)
    return f"{CLASS_ID[label]} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}"


def main() -> None:
    ap = argparse.ArgumentParser(description="Curation -> local YOLO detection set.")
    ap.add_argument("--keep", type=Path, required=True)
    ap.add_argument("--filtered-dir", type=Path, required=True)
    ap.add_argument("--frames-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--include-easy-neg", action="store_true")
    args = ap.parse_args()
    keep_path = cast(Path, args.keep)
    filtered_dir = cast(Path, args.filtered_dir)
    frames_dir = cast(Path, args.frames_dir)
    out_dir = cast(Path, args.out_dir)
    include_easy = cast(bool, args.include_easy_neg)

    manifest = json.loads(keep_path.read_text(encoding="utf-8"))
    keep: set[int] = set(cast(list[int], manifest["keep_frames"]))
    candidate: set[int] = {
        int(p.stem.split("_")[-1]) for p in filtered_dir.glob("zombie01_frame_*.json")
    }
    missing_keep = sorted(keep - candidate)
    if missing_keep:
        raise SystemExit(f"keep frames absent from filtered candidates: {missing_keep}")

    img_dir = out_dir / "images" / "train"
    lbl_dir = out_dir / "labels" / "train"
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    if include_easy:
        selected = {int(p.stem.split("_")[-1]) for p in frames_dir.glob("zombie01_frame_*.jpg")}
    else:
        selected = candidate | keep

    label_ct: dict[str, int] = {name: 0 for name in CLASS_ORDER}
    n_pos = n_hardneg = n_easyneg = 0
    for n in sorted(selected):
        stem = frame_stem(n)
        src = frames_dir / f"{stem}.jpg"
        if not src.exists():
            continue
        with Image.open(src) as im:
            w, h = im.size
        lines: list[str] = []
        if n in keep:
            rec = json.loads((filtered_dir / f"{stem}.json").read_text(encoding="utf-8"))
            for b in cast(list[dict[str, object]], rec["boxes"]):
                label = cast(str, b["label"])
                lines.append(to_yolo_line(label, cast(list[float], b["box"]), w, h))
                label_ct[label] += 1
            n_pos += 1
        elif n in candidate:
            n_hardneg += 1
        else:
            n_easyneg += 1
        shutil.copy2(src, img_dir / f"{stem}.jpg")
        (lbl_dir / f"{stem}.txt").write_text(
            ("\n".join(lines) + "\n") if lines else "", encoding="utf-8"
        )

    yaml = (
        f"path: {out_dir.resolve().as_posix()}\n"
        "train: images/train\n"
        "val: images/train\n"
        f"nc: {len(CLASS_ORDER)}\n"
        f"names: {CLASS_ORDER}\n"
    )
    (out_dir / "data.yaml").write_text(yaml, encoding="utf-8")

    print(f"positives={n_pos} hard_neg={n_hardneg} easy_neg={n_easyneg} total={n_pos + n_hardneg + n_easyneg}")
    print(f"box label dist: {label_ct}")
    print(f"out: {out_dir}")


if __name__ == "__main__":
    main()
