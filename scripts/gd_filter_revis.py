"""Filter GD raw detections to weapon/blood candidates and re-visualize for review.

The full GD run labels ~62% of boxes 'bloody face' (clean faces = FP) plus empty
labels. Those are auto-dropped here. Remaining boxes are mapped (best-effort) to the
project violence schema and redrawn so the review substrate is only plausible
weapon/blood candidates — the annotator then keeps/relabels/drops per box.

Drop: any label containing 'face', or empty.
Map:  gun/rifle -> weapon_gun ; sword/axe/knife -> weapon_knife ;
      hammer/baseball/bat -> weapon_blunt ; blood/bloody/wound/injury -> blood ; else drop.

    python scripts/gd_filter_revis.py --gd-dir data/processed/gd_zombie_full/zombie01 \
        --frames-dir data/processed/zombie01_frames \
        --out-dir data/processed/gd_zombie_filtered/zombie01

Output: per kept-frame {stem}.json (filtered boxes + mapped label) + {stem}_vis.jpg.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import cast

from PIL import Image, ImageDraw

WEAPON_GUN = {"gun", "rifle"}
WEAPON_KNIFE = {"sword", "axe", "knife"}
WEAPON_BLUNT = {"hammer", "baseball", "bat"}
BLOOD = {"blood", "bloody", "wound", "injury"}


def map_label(raw: str) -> str | None:
    tokens = set(raw.split())
    if not tokens or "face" in tokens:
        return None
    if tokens & WEAPON_GUN:
        return "weapon_gun"
    if tokens & WEAPON_KNIFE:
        return "weapon_knife"
    if tokens & WEAPON_BLUNT:
        return "weapon_blunt"
    if tokens & BLOOD:
        return "blood"
    return None


COLORS = {
    "weapon_gun": (255, 60, 60),
    "weapon_knife": (255, 160, 0),
    "weapon_blunt": (255, 0, 255),
    "blood": (40, 120, 255),
}


def main() -> None:
    ap = argparse.ArgumentParser(description="Filter GD detections + re-visualize.")
    ap.add_argument("--gd-dir", type=Path, required=True)
    ap.add_argument("--frames-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    gd_dir: Path = args.gd_dir
    frames_dir: Path = args.frames_dir
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    jsons = sorted(p for p in gd_dir.glob("*.json"))
    label_ct: Counter[str] = Counter()
    kept_frames = 0
    kept_boxes = 0
    for jp in jsons:
        rec = json.loads(jp.read_text(encoding="utf-8"))
        boxes = cast(list[list[float]], rec["boxes"])
        scores = cast(list[float], rec["scores"])
        labels = cast(list[str], rec["labels"])
        keep: list[dict[str, object]] = []
        for box, score, raw in zip(boxes, scores, labels, strict=False):
            mapped = map_label(str(raw))
            if mapped is None:
                continue
            keep.append({"box": box, "score": score, "raw": raw, "label": mapped})
            label_ct[mapped] += 1
        if not keep:
            continue
        kept_frames += 1
        kept_boxes += len(keep)
        frame_name = cast(str, rec["frame"])
        stem = Path(frame_name).stem
        (out_dir / f"{stem}.json").write_text(
            json.dumps({"frame": frame_name, "boxes": keep}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        src = frames_dir / frame_name
        if not src.exists():
            continue
        img = Image.open(src).convert("RGB")
        draw = ImageDraw.Draw(img)
        for k in keep:
            x1, y1, x2, y2 = cast(list[float], k["box"])
            color = COLORS[cast(str, k["label"])]
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            draw.text((x1, max(0, y1 - 12)), f"{k['label']} {k['score']:.2f}", fill=color)
        img.save(out_dir / f"{stem}_vis.jpg", quality=85)

    print(f"kept_frames={kept_frames} kept_boxes={kept_boxes}")
    print(f"mapped label dist: {dict(label_ct)}")


if __name__ == "__main__":
    main()
