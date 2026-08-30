"""Per-frame composite images for the P4 object re-review.

Draws every bottle/cup/cigarette box of a frame on one image, each tagged with
its manifest idx + label + score, so a whole scene (drinking context?) is judged
at once instead of 373 single-box crops. Output -> vision_review/p4_frames/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"C:\Users\windg\Desktop\SCHOOL\3-1\데이터엔지니어링\project2")
REVIEW = ROOT / "data" / "processed" / "vision_review"
FRAMES = ROOT / "data" / "processed" / "yt_drama_frames"
OUT = REVIEW / "p4_frames"

COLORS = [
    (255, 40, 40), (40, 200, 255), (80, 255, 80), (255, 220, 0),
    (255, 120, 255), (255, 150, 30), (180, 180, 255),
]


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for n in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    entries = json.loads((REVIEW / "p4_objects_manifest.json").read_text(encoding="utf-8"))
    by_frame: dict[tuple[str, str], list[dict[str, object]]] = {}
    for e in entries:
        by_frame.setdefault((e["vid"], e["frame"]), []).append(e)

    f = font(22)
    n = 0
    for (vid, frame), boxes in sorted(by_frame.items()):
        src = FRAMES / frame
        if not src.exists():
            print(f"MISSING {src}")
            continue
        img = Image.open(src).convert("RGB")
        draw = ImageDraw.Draw(img)
        boxes_sorted = sorted(boxes, key=lambda b: cast(int, b["idx"]))
        for i, b in enumerate(boxes_sorted):
            color = COLORS[i % len(COLORS)]
            x, y, w, h = cast("list[float]", b["bbox_xywh"])
            draw.rectangle([x, y, x + w, y + h], outline=color, width=4)
            score = b["score"]
            sc = f"{score:.2f}" if isinstance(score, (int, float)) else "?"
            cap = f"#{b['idx']} {b['cvat_label']} {sc}"
            ty = max(0.0, y - 26)
            tw = draw.textlength(cap, font=f)
            draw.rectangle([x, ty, x + tw + 6, ty + 26], fill=color)
            draw.text((x + 3, ty + 2), cap, fill=(0, 0, 0), font=f)
        stem = Path(frame).stem.split("_")[-1]
        out = OUT / f"{vid}_{stem}.jpg"
        img.save(out, quality=85)
        n += 1
    print(f"composites: {n} frames -> {OUT}")


if __name__ == "__main__":
    main()
