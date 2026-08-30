"""Contact sheets (3x3) of the to-review negative frames for false-negative scan.

The 638 now-empty frames that were NOT human-reviewed in the strict P4 pass
(p4_negative_frames.json, reviewed=false) are tiled 9-per-sheet so a whole batch is
scanned at once for a missed target (a clear 술자리 bottle table / someone smoking)
that GD failed to box. Any suspicious cell is then re-read full-res from
yt_drama_frames/. Output -> vision_review/p4_neg_sheets/{vid}_{n}.jpg.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"C:\Users\windg\Desktop\SCHOOL\3-1\데이터엔지니어링\project2")
REVIEW = ROOT / "data" / "processed" / "vision_review"
FRAMES = ROOT / "data" / "processed" / "yt_drama_frames"
NEG = REVIEW / "p4_negative_frames.json"
OUT = REVIEW / "p4_neg_sheets"

COLS = 3
ROWS = 3
CELL_W = 480
CELL_H = 270
PER = COLS * ROWS


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for n in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default()


def stem_of(frame: str) -> str:
    return Path(frame).stem.split("_")[-1]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    entries = json.loads(NEG.read_text(encoding="utf-8"))
    todo = [e for e in entries if not e["reviewed"]]
    by_vid: dict[str, list[str]] = {}
    for e in todo:
        by_vid.setdefault(cast(str, e["vid"]), []).append(cast(str, e["frame"]))

    f = font(26)
    n_sheets = 0
    for vid, frames in sorted(by_vid.items()):
        frames.sort(key=stem_of)
        for start in range(0, len(frames), PER):
            chunk = frames[start : start + PER]
            sheet = Image.new("RGB", (COLS * CELL_W, ROWS * CELL_H), (0, 0, 0))
            draw = ImageDraw.Draw(sheet)
            for i, frame in enumerate(chunk):
                src = FRAMES / frame
                if not src.exists():
                    continue
                cell = Image.open(src).convert("RGB").resize((CELL_W, CELL_H))
                cx = (i % COLS) * CELL_W
                cy = (i // COLS) * CELL_H
                sheet.paste(cell, (cx, cy))
                tag = stem_of(frame)
                draw.rectangle([cx, cy, cx + 70, cy + 24], fill=(0, 0, 0))
                draw.text((cx + 3, cy + 1), tag, fill=(255, 235, 0), font=f)
            sheet_no = start // PER
            out = OUT / f"{vid}_{sheet_no:02d}.jpg"
            sheet.save(out, quality=88)
            n_sheets += 1
    print(f"sheets: {n_sheets} -> {OUT}")


if __name__ == "__main__":
    main()
