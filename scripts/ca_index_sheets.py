from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(r"C:/Users/windg/Desktop/SCHOOL/3-1/데이터엔지니어링/project2/data/processed/violence/Car Accident")
REV = Path(r"C:/Users/windg/Desktop/SCHOOL/3-1/데이터엔지니어링/project2/data/processed/vision_review")
SHEETDIR = REV / "ca_sheets"

TILE = 200
COLS = 6
ROWS = 5
PER = COLS * ROWS
CAP = 22

try:
    FONT = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
except Exception:  # noqa: BLE001
    FONT = ImageFont.load_default()


def main() -> None:
    files = sorted(ROOT.glob("*.jpg"))
    SHEETDIR.mkdir(parents=True, exist_ok=True)
    (REV / "ca_index_map.json").write_text(
        json.dumps([f.name for f in files], ensure_ascii=False), encoding="utf-8"
    )
    n_sheets = (len(files) + PER - 1) // PER
    for s in range(n_sheets):
        chunk = files[s * PER : (s + 1) * PER]
        canvas = Image.new("RGB", (COLS * TILE, ROWS * (TILE + CAP)), (15, 15, 15))
        draw = ImageDraw.Draw(canvas)
        for j, f in enumerate(chunk):
            gi = s * PER + j
            r, c = divmod(j, COLS)
            try:
                im = Image.open(f).convert("RGB")
                im = ImageOps.autocontrast(im, cutoff=1)  # lift dark night frames
                im.thumbnail((TILE, TILE))
            except Exception:  # noqa: BLE001
                im = Image.new("RGB", (TILE, TILE), (80, 0, 0))
            x, y = c * TILE, r * (TILE + CAP)
            canvas.paste(im, (x, y))
            draw.rectangle([x, y + TILE, x + TILE, y + TILE + CAP], fill=(0, 0, 0))
            draw.text((x + 4, y + TILE + 2), f"#{gi}", fill=(0, 255, 120), font=FONT)
        out = SHEETDIR / f"ca_{s:02d}_{s*PER}-{s*PER+len(chunk)-1}.png"
        canvas.save(out)
    print(f"total {len(files)} imgs, {n_sheets} sheets")


if __name__ == "__main__":
    main()
