from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data/processed/violence"
DEST = ROOT.parent / "violence_curated_500"
REV = ROOT.parent / "vision_review"
MAN = json.loads((REV / "xdv_curated_500_manifest.json").read_text(encoding="utf-8"))["picks"]

TILE = 150
COLS = 6
ROWS = 5  # 30 thumbs per sheet, spread across the picks


def make_sheet(cat: str) -> None:
    picks = MAN[cat]
    n = COLS * ROWS
    step = max(1, len(picks) // n)
    sample = picks[::step][:n]
    canvas = Image.new("RGB", (COLS * TILE, ROWS * (TILE + 14)), (18, 18, 18))
    draw = ImageDraw.Draw(canvas)
    for i, name in enumerate(sample):
        r, c = divmod(i, COLS)
        try:
            im = Image.open(DEST / cat / name).convert("RGB")
            im.thumbnail((TILE, TILE))
        except Exception:
            im = Image.new("RGB", (TILE, TILE), (80, 0, 0))
        x, y = c * TILE, r * (TILE + 14)
        canvas.paste(im, (x, y))
        draw.text((x + 2, y + TILE + 1), name.split("__#")[0][:22], fill=(230, 230, 0))
    out = REV / f"verify_{cat.replace(' ', '_')}.png"
    canvas.save(out)
    print(f"{cat}: {len(sample)} thumbs -> {out.name}")


def main() -> None:
    for cat in MAN:
        make_sheet(cat)


if __name__ == "__main__":
    main()
